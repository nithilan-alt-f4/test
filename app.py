import re
import subprocess
import urllib.parse
from flask import Flask, request, Response, stream_with_context, jsonify

app = Flask(__name__)

YTDLP = "yt-dlp"


def clean_url(url):
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.hostname == "music.youtube.com":
            return url
        if parsed.hostname == "youtu.be":
            vid = parsed.path.lstrip("/").split("?")[0]
            return f"https://www.youtube.com/watch?v={vid}"
        qs = urllib.parse.parse_qs(parsed.query)
        if "list" in qs and "v" not in qs:
            return url
        cq = {k: v for k, v in qs.items() if k == "v"}
        c = parsed._replace(query=urllib.parse.urlencode(cq, doseq=True))
        return urllib.parse.urlunparse(c)
    except Exception:
        return url


def is_playlist(url):
    try:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        return "list" in qs and "v" not in qs
    except Exception:
        return False


@app.route("/api/info")
def info():
    url = clean_url(request.args.get("url", "").strip())
    if not url:
        return jsonify(error="no url"), 400

    cmd = [YTDLP, "--no-warnings", "--print",
           "%(title)s\n%(channel)s\n%(duration_string)s",
           "--playlist-items", "1", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    lines = r.stdout.strip().splitlines()
    if not lines or not lines[0]:
        return jsonify(error=(r.stderr[:300] or "lookup failed")), 400

    q_cmd = [YTDLP, "--list-formats", "--no-warnings", "--playlist-items", "1", url]
    qr = subprocess.run(q_cmd, capture_output=True, text=True, timeout=30)
    heights = sorted({int(m.group(1)) for m in re.finditer(r"\b(\d{3,4})p\b", qr.stdout)}, reverse=True)

    return jsonify(
        title=lines[0],
        channel=lines[1] if len(lines) > 1 else "",
        duration=lines[2] if len(lines) > 2 else "",
        playlist=is_playlist(url),
        qualities=heights,
    )


@app.route("/api/download")
def download():
    url = clean_url(request.args.get("url", "").strip())
    fmt = request.args.get("fmt", "mp4")
    quality = request.args.get("quality", "1080")
    if not url:
        return jsonify(error="no url"), 400

    cmd = [YTDLP, "--no-warnings", "--restrict-filenames", "-o", "-"]

    if fmt == "mp3":
        bitrate = quality.replace("kbps", "") if "kbps" in quality else "320"
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", bitrate]
        ext = "mp3"
    else:
        h = quality if quality.isdigit() else "1080"
        fs = f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}][ext=mp4]/best"
        cmd += ["-f", fs, "--merge-output-format", "mp4"]
        ext = "mp4"

    cmd.append(url)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def generate():
        try:
            while True:
                chunk = proc.stdout.read(65536)
                if not chunk:
                    break
                yield chunk
        finally:
            proc.stdout.close()
            proc.wait()

    headers = {
        "Content-Disposition": f'attachment; filename="download.{ext}"',
        "Content-Type": "application/octet-stream",
    }
    return Response(stream_with_context(generate()), headers=headers)


@app.route("/health")
def health():
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
