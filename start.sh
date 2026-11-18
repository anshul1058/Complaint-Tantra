#!/bin/sh
set -e

mkdir -p /tmp/nginx/client_temp /tmp/nginx/proxy_temp /tmp/nginx/fastcgi_temp /tmp/nginx/uwsgi_temp /tmp/nginx/scgi_temp

python3 -m uvicorn main:app --app-dir /app/api --host 127.0.0.1 --port 8000 &
PORT=3000 HOSTNAME=127.0.0.1 node /app/server.js &

exec nginx -g 'daemon off;'
