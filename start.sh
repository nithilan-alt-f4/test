#!/bin/bash
set -e

# Start the PO token provider HTTP server in the background (default port 4416)
bgutil-pot server --host 127.0.0.1 --port 4416 &
BGUTIL_PID=$!

# Give it a moment to come up
sleep 2

# Sanity check
curl -sf http://127.0.0.1:4416/ping > /dev/null || echo "WARNING: bgutil-pot did not respond to ping"

cleanup() {
  kill $BGUTIL_PID 2>/dev/null || true
}
trap cleanup EXIT

exec gunicorn -w 2 --threads 4 -b 0.0.0.0:${PORT:-5000} --timeout 300 app:app
