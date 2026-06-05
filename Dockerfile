# Multi-stage build: Node compiles the React/Vite SPA, then Python runs the
# Flask + Socket.IO backend that serves both the API and the built SPA.
# Entry module is ghana_cap_app:app (legacy app:app was deleted in the tree).

# ─── Stage 1: build the React SPA (Vite → frontend/dist) ───────────────────
FROM node:20-slim AS frontend
WORKDIR /frontend

# VITE_*-prefixed vars are baked into the client bundle at build time. The
# Mapbox token is a publishable (pk.*) token, safe to embed. Render exposes
# the service's env vars as Docker build args, so this picks up VITE_MAPBOX_TOKEN.
ARG VITE_MAPBOX_TOKEN=""
ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN

# Install deps against the lockfile first for layer caching.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ─── Stage 2: Python runtime (Flask + Socket.IO under gunicorn/eventlet) ───
FROM python:3.10-slim AS app
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code: ghana_cap_app.py, db.py, services/, templates/, static/, etc.
COPY . .

# The built SPA from stage 1 — Flask serves this at "/" (frontend/dist is
# gitignored, so it must come from the build, not the repo).
COPY --from=frontend /frontend/dist ./frontend/dist

# TTS / mock-audio write target. The __main__ block that normally creates this
# doesn't run under gunicorn, so ensure it exists.
RUN mkdir -p static/audio

# Render injects $PORT at runtime; bind it. `exec` form via sh -c expands the
# var AND makes gunicorn PID 1 so it receives SIGTERM directly (clean shutdown
# on redeploys). eventlet worker is required for Socket.IO WebSocket support.
CMD ["sh", "-c", "exec gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:${PORT:-5000} ghana_cap_app:app"]
