# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.12 (for backend dev)
- Node 24 (for frontend dev)

## Local Development

```bash
# Backend
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api` requests to `http://localhost:8000`.

## Docker Compose

```bash
docker compose up --build
```

Services:
- **backend**: `http://127.0.0.1:8000`
- **frontend**: `http://127.0.0.1:5173`
- **keycloak**: `http://127.0.0.1:8080` (planned auth)
- **ntfy**: `http://127.0.0.1:8043`

## TLS Reverse Proxy

In production, terminate TLS at the reverse proxy (nginx, Caddy, or cloud
load balancer). Forward `Host`, `X-Real-IP`, and `X-Forwarded-Proto` headers.
WebSocket is not required — all API communication is HTTP/JSON.

Example nginx reverse proxy:
```nginx
server {
    listen 443 ssl;
    server_name skills.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
    }
}
```

## Backup and Restore

### Database
```bash
# Backup
sqlite3 skills.db ".backup backup.db"

# Restore
cp backup.db skills.db
```

### Volume-based (Docker)
```bash
# Backup
docker run --rm -v cobalt-foundry_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/data-backup.tar.gz -C /data .

# Restore
docker run --rm -v cobalt-foundry_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/data-backup.tar.gz -C /data
```

## Keycloak Enrolment (Planned)

When auth is implemented, operators will:
1. Start Keycloak via `docker compose up -d keycloak`
2. Create a realm and configure SAML identity brokering for upstream IdPs
3. Create a client with PKCE-enabled authorization-code flow
4. Set environment variables: `KEYCLOAK_REALM`, `KEYCLOAK_URL`,
   `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`

## Demo Mode

A local-only demo mode will be added that:
- Binds exclusively to `127.0.0.1`
- Starts with a bundled sample repository
- Refuses to start when `DEBUG=false` or a public interface is detected

## Environment Variables

See `.env.example` for all available configuration options.