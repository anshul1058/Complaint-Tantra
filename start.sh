#!/bin/sh
set -e

python3 -m uvicorn main:app --app-dir /app/api --host 127.0.0.1 --port 8000 &
PORT=3000 HOSTNAME=127.0.0.1 node /app/server.js &

exec nginx -g 'daemon off;'
