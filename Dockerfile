FROM python:3.11-slim

# ffmpeg for muxing video+audio, curl/unzip to fetch the PO token provider
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- yt-dlp + Flask ---
RUN pip install --no-cache-dir yt-dlp flask gunicorn

# --- bgutil-pot (Rust PO token provider, single static binary) ---
RUN curl -L -o /usr/local/bin/bgutil-pot \
    https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/latest/download/bgutil-pot-linux-x86_64 \
    && chmod +x /usr/local/bin/bgutil-pot

# --- yt-dlp plugin that talks to the provider ---
RUN mkdir -p /root/yt-dlp-plugins \
    && curl -L -o /tmp/plugin.zip \
    https://github.com/jim60105/bgutil-ytdlp-pot-provider-rs/releases/latest/download/bgutil-ytdlp-pot-provider-rs.zip \
    && unzip /tmp/plugin.zip -d /root/yt-dlp-plugins \
    && rm /tmp/plugin.zip

COPY app.py start.sh ./
RUN chmod +x start.sh

EXPOSE 5000
CMD ["./start.sh"]
