#!/bin/bash
set -e

echo "Starting PO token provider..."
# Start the PO token provider HTTP server in the background
bgutil-pot server --host 127.0.0.1 --port 4416 &
BGUTIL_PID=$!

# Give it a moment to come up
sleep 3

# Sanity check
if curl -sf http://127.0.0.1:4416/ping > /dev/null; then
    echo "SUCCESS: bgutil-pot is responding."
else
    echo "CRITICAL WARNING: bgutil-pot did not respond to ping!"
fi

cleanup() {
  echo "Cleaning up background processes..."
  kill $BGUTIL_PID 2>/dev/null || true
}
trap cleanup EXIT

echo "Starting Gunicorn..."
# Removed 'exec' so the bash script stays alive to manage the trap and handle errors
gunicorn -w 2 --threads 4 -b 0.0.0.0:${PORT:-5000} --timeout 300 --preload app:app
