#!/bin/sh
set -e
cd /app

mkdir -p /tmp/nginx/client_temp /tmp/nginx/proxy_temp /tmp/nginx/fastcgi_temp /tmp/nginx/uwsgi_temp /tmp/nginx/scgi_temp

echo "Starting FastAPI on 127.0.0.1:8000"
python3 -m uvicorn main:app --app-dir /app/api --host 127.0.0.1 --port 8000 &
echo "Starting Next.js on 127.0.0.1:3000"
PORT=3000 HOSTNAME=127.0.0.1 node /app/server.js &
echo "Starting nginx on 0.0.0.0:10000"

exec nginx -g 'daemon off;'
