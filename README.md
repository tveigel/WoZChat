# WebWOz – one‑click Wizard‑of‑Oz chat

## Run locally (dev)

```bash
# back‑end
python backend/app.py          # http://localhost:5000

# participant UI
cd frontend-participant && npm start   # http://localhost:3000/chat/test

# wizard UI
cd ../frontend-wizard && npm start     # http://localhost:3001/wizard
