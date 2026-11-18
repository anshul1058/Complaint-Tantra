# Complaint-Tantra frontend + API in one Render web service.
# The proxy exposes both processes through the single Render port.

FROM node:22-alpine AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web/ ./
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip nginx build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system nodejs \
    && adduser --system --ingroup nodejs nextjs
COPY apps/api/requirements.txt /tmp/api-requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/api-requirements.txt
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY apps/api ./api
COPY nginx.conf /etc/nginx/nginx.conf
USER nextjs
EXPOSE 10000
CMD ["sh", "-c", "python3 -m uvicorn main:app --app-dir /app/api --host 127.0.0.1 --port 8000 & PORT=3000 HOSTNAME=127.0.0.1 node server.js & exec nginx -g 'daemon off;'"]
