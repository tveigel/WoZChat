# ── Stage 1: build React bundles ──────────────────────────────────────────────
FROM node:20 AS builder
WORKDIR /src

COPY frontend-participant ./frontend-participant
COPY frontend-wizard     ./frontend-wizard

# Build with proper PUBLIC_URL namespacing to avoid static file conflicts
RUN cd frontend-participant && PUBLIC_URL="/static/p" npm install && npm run build
RUN cd frontend-wizard     && PUBLIC_URL="/static/w" npm install && npm run build

# ── Stage 2: lightweight Python image with static files ──────────────────────
FROM python:3.11-slim
WORKDIR /app

# install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy back‑end
COPY backend /app/backend

# copy React HTML files
COPY --from=builder /src/frontend-participant/build /app/backend/static/participant
COPY --from=builder /src/frontend-wizard/build     /app/backend/static/wizard

# copy static assets into namespaced directories to prevent conflicts
COPY --from=builder /src/frontend-participant/build/static /app/backend/static/static/p
COPY --from=builder /src/frontend-wizard/build/static     /app/backend/static/static/w

EXPOSE 10000
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:10000", "backend.app:app"]
