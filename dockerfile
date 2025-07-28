# ── Stage 1: build React bundles ──────────────────────────────────────────────
FROM node:20 AS builder
WORKDIR /src

COPY frontend-participant ./frontend-participant
COPY frontend-wizard     ./frontend-wizard

RUN cd frontend-participant && npm ci && npm run build
RUN cd frontend-wizard     && npm ci && npm run build

# ── Stage 2: lightweight Python image with static files ──────────────────────
FROM python:3.11-slim
WORKDIR /app

# install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy back‑end
COPY backend /app/backend

# copy React builds
COPY --from=builder /src/frontend-participant/build /app/backend/static/participant
COPY --from=builder /src/frontend-wizard/build     /app/backend/static/wizard
# hashed JS/CSS assets merged here
COPY --from=builder /src/frontend-participant/build/static /app/backend/static/static
COPY --from=builder /src/frontend-wizard/build/static     /app/backend/static/static

EXPOSE 10000
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:10000", "backend.app:app"]
