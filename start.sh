#!/bin/sh
set -e
cd /app

mkdir -p /tmp/nginx/client_temp /tmp/nginx/proxy_temp /tmp/nginx/fastcgi_temp /tmp/nginx/uwsgi_temp /tmp/nginx/scgi_temp

python3 -m uvicorn main:app --app-dir /app/api --host 127.0.0.1 --port 8000 >/tmp/api.log 2>&1 &
api_pid=$!
PORT=3000 HOSTNAME=127.0.0.1 node /app/server.js >/tmp/next.log 2>&1 &
next_pid=$!

sleep 3
if ! kill -0 "$api_pid" 2>/dev/null; then cat /tmp/api.log; exit 1; fi
if ! kill -0 "$next_pid" 2>/dev/null; then cat /tmp/next.log; exit 1; fi

nginx -g 'daemon off;'
