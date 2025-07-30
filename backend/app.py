# backend/app.py
"""
Flask‑SocketIO back‑end that also serves the pre‑built React bundles.

• /api/new_room          → POST, returns {"room": "<8‑char id>"}
• /wizard[/<room>]       → wizard UI (HTML)
• /chat/<room>           → participant UI (HTML)
• /static/*              → hashed JS/CSS assets of *both* bundles
• /api/templates         → GET/POST – list or create template
• /api/templates/<key>   → PUT/DELETE – update or remove template
• Socket.IO WS namespace → same origin, so client just uses io()

Built for Docker: gunicorn ‑k eventlet ‑w 1 ‑b 0.0.0.0:10000 backend.app:app
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# ───────────────────────────────────────────────  Server & paths

BASE_DIR      = Path(__file__).resolve().parent
STATIC_DIR    = BASE_DIR / "static"
PARTICIPANT_DIR = STATIC_DIR / "participant"
WIZARD_DIR      = STATIC_DIR / "wizard"
ASSETS_DIR      = STATIC_DIR / "static"         # merged hashed JS / CSS

# Template persistence - use /data if available (Render persistent disk), fallback to local
TEMPLATE_DIR = Path(os.environ.get("TEMPLATE_DIR", str(BASE_DIR)))
TEMPLATE_FILE = TEMPLATE_DIR / "templates.json"

# Ensure template directory exists
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

app      = Flask(__name__, static_folder=None)  # we serve manually
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change‑me‑for‑prod")

# CORS configuration - open for development, locked down for production
if os.environ.get("NODE_ENV") == "production":
    # Production: lock down to specific origins
    allowed_origins = [
        os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com"),
        "https://your-app.onrender.com"  # fallback
    ]
    CORS(app, resources={r"/*": {"origins": allowed_origins}})
    socketio = SocketIO(app, cors_allowed_origins=allowed_origins)
else:
    # Development: allow localhost
    CORS(app, resources={r"/*": {"origins": "*"}})
    socketio = SocketIO(app, cors_allowed_origins="*")

# room id → list[ message dict ]
rooms: Dict[str, List[dict]] = {}

# ───────────────────────────────────────────────  Template helpers

_template_lock = Lock()                         # file‑level synchronisation


def _save_templates(data: dict) -> None:
    """Write templates atomically (tmp → rename)."""
    tmp = TEMPLATE_FILE.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    tmp.replace(TEMPLATE_FILE)


def _normalise(data: dict) -> dict:
    """
    Accept either:
      • {"General": {"key": "value", …}}   ← preferred, category aware
      • {"key": "value", …}               ← old style, becomes "General"
    """
    if not data:
        return {"General": {}}
    # old flat style → wrap
    if all(isinstance(v, str) for v in data.values()):
        return {"General": data}
    return data

def _load_templates() -> dict:
    if TEMPLATE_FILE.exists():
        with TEMPLATE_FILE.open(encoding="utf-8") as fh:
            data = json.load(fh)
            return _normalise(data)

    default = {
        "General": {
            "greeting":      "Hello! How can I help you today?",
            "understanding": "I understand. Let me look into that for you.",
            "no_info":       "I'm sorry, I don't have information about that.",
            "goodbye":       "Thank you for chatting with me. Goodbye!",
        }
    }
    _save_templates(default)
    return default

TEMPLATES: Dict[str, dict] = _load_templates()

# ───────────────────────────────────────────────  Misc helpers


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _persist_and_broadcast() -> None:
    """Save TEMPLATES and push the fresh set to all connected wizards."""
    _save_templates(TEMPLATES)
    # Broadcast to every connected client (wizard UI filters internally)
    socketio.emit("templates", TEMPLATES, broadcast=True)


def save(room: str, sender: str, text: str) -> dict:
    msg = {"sender": sender, "text": text, "timestamp": utc_now()}
    rooms.setdefault(room, []).append(msg)
    return msg


def _stream_wizard_message(room: str, text: str) -> None:
    words = text.split()
    for i, w in enumerate(words):
        socketio.sleep(0.08)  # tweak typing speed
        emit(
            "stream_chunk",
            {"word": w, "is_last": i == len(words) - 1},
            to=room,
            include_self=False,
        )

# ───────────────────────────────────────────────  HTTP routes


@app.post("/api/new_room")
def new_room():
    room_id = uuid.uuid4().hex[:8]
    rooms[room_id] = []
    return jsonify({"room": room_id})


@app.route("/wizard")
@app.route("/wizard/<room_id>")
def wizard_app(room_id: str | None = None):
    return send_from_directory(WIZARD_DIR, "index.html")


@app.route("/chat/<room_id>")
def participant_app(room_id: str):
    return send_from_directory(PARTICIPANT_DIR, "index.html")


@app.route("/static/<path:filename>")
def static_assets(filename):
    # Handle both separated bundles and any fallback to merged assets
    if filename.startswith("p/"):
        # Participant bundle assets
        return send_from_directory(ASSETS_DIR / "p", filename[2:])
    elif filename.startswith("w/"):
        # Wizard bundle assets  
        return send_from_directory(ASSETS_DIR / "w", filename[2:])
    else:
        # Fallback to original location for any other assets
        return send_from_directory(ASSETS_DIR, filename)


# ─────────────────────  ↑ existing routes unchanged – NEW below  ↑


@app.get("/api/templates")
def list_templates():
    """Return the currently active template dictionary."""
    return jsonify(TEMPLATES)


@app.post("/api/templates")
def create_template():
    """Add a new template:  {key, value}  in JSON body."""
    payload = request.get_json(silent=True) or {}
    key, value = payload.get("key"), payload.get("value")
    if not key or not value:
        return jsonify({"error": "Both 'key' and 'value' are required."}), 400

    with _template_lock:
        if key in TEMPLATES:
            return jsonify({"error": "Template already exists."}), 409
        TEMPLATES[key] = value
        _persist_and_broadcast()
    return jsonify({"status": "created"}), 201


@app.put("/api/templates/<string:key>")
def update_template(key: str):
    """Replace an existing template’s text."""
    payload = request.get_json(silent=True) or {}
    value = payload.get("value")
    if value is None:
        return jsonify({"error": "'value' is required."}), 400

    with _template_lock:
        TEMPLATES[key] = value
        _persist_and_broadcast()
    return jsonify({"status": "updated"})


@app.delete("/api/templates/<string:key>")
def delete_template(key: str):
    """Remove a template entirely."""
    with _template_lock:
        if key not in TEMPLATES:
            return jsonify({"error": "Template not found."}), 404
        TEMPLATES.pop(key)
        _persist_and_broadcast()
    return jsonify({"status": "deleted"})




@app.post("/api/templates/item")
def create_template_item():
    """
    Add a template specifying *category* explicitly.
    Body → {"category": "Sales", "key": "upsell", "value": "Have you seen …?"}
    """
    payload = request.get_json(silent=True) or {}
    cat  = payload.get("category") or "General"
    key  = payload.get("key")
    val  = payload.get("value")
    if not key or not val:
        return jsonify({"error": "'key' and 'value' required"}), 400

    with _template_lock:
        cat_dict = TEMPLATES.setdefault(cat, {})
        if key in cat_dict:
            return jsonify({"error": "Template already exists"}), 409
        cat_dict[key] = val
        _persist_and_broadcast()
    return jsonify({"status": "created"}), 201


@app.put("/api/templates/<string:category>/<string:key>")
def update_template_item(category: str, key: str):
    payload = request.get_json(silent=True) or {}
    val = payload.get("value")
    if val is None:
        return jsonify({"error": "'value' required"}), 400

    with _template_lock:
        TEMPLATES.setdefault(category, {})[key] = val
        _persist_and_broadcast()
    return jsonify({"status": "updated"})


@app.delete("/api/templates/<string:category>/<string:key>")
def delete_template_item(category: str, key: str):
    with _template_lock:
        if key not in TEMPLATES.get(category, {}):
            return jsonify({"error": "Not found"}), 404
        TEMPLATES[category].pop(key)
        if not TEMPLATES[category]:          # remove empty category
            TEMPLATES.pop(category)
        _persist_and_broadcast()
    return jsonify({"status": "deleted"})



# ───────────────────────────────────────────────  Socket.IO


@socketio.on("connect")
def _connect():
    print("Client connected")


@socketio.on("disconnect")
def _disconnect():
    print("Client disconnected")


@socketio.on("join")
def on_join(data):
    room = data.get("room", "default_room")
    kind = data.get("type", "unknown")
    join_room(room)
    print(f"{kind} joined {room}")
    
    # Send existing message history to the joining user
    if room in rooms and rooms[room]:
        emit("message_history", {"messages": rooms[room]})
    
    if kind == "wizard":
        emit("templates", TEMPLATES)   # unchanged


@socketio.on("leave")
def on_leave(data):
    room = data.get("room", "default_room")
    leave_room(room)
    print(f"User left {room}")


@socketio.on("participant_typing")
def on_participant_typing(data):
    emit(
        "participant_is_typing",
        {"text": data.get("text", "")},
        to=data.get("room", "default_room"),
        include_self=False,
    )


@socketio.on("participant_message")
def on_participant_message(data):
    room = data.get("room", "default_room")
    text = data.get("text", "")
    emit("new_message", save(room, "participant", text), to=room)


@socketio.on("wizard_response")
def on_wizard_response(data):
    room = data.get("room", "default_room")
    text = data.get("text", "")
    msg = save(room, "wizard", text)

    # 1) show full msg immediately to the wizard only
    emit("new_message", msg)

    # 2) stream to participant
    _stream_wizard_message(room, text)

    # 3) send final full msg to participant
    emit("new_message", msg, to=room, include_self=False)


# ───────────────────────────────────────────────  Main

if __name__ == "__main__":
    # `debug=True` stays exactly as before – hot‑reload still works
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
