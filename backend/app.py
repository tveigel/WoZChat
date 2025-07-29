# backend/app.py
"""
Flask‑SocketIO back‑end that also serves the pre‑built React bundles.

• /api/new_room          → POST, returns {"room": "<8‑char id>"}
• /wizard[/<room>]       → wizard UI (HTML)
• /chat/<room>           → participant UI (HTML)
• /static/*              → hashed JS/CSS assets of *both* bundles
• Socket.IO WS namespace → same origin, so client just uses io()

Built for Docker: gunicorn ‑k eventlet ‑w 1 ‑b 0.0.0.0:10000 backend.app:app
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# ───────────────────────────────────────────────  Server

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PARTICIPANT_DIR = STATIC_DIR / "participant"
WIZARD_DIR = STATIC_DIR / "wizard"
ASSETS_DIR = STATIC_DIR / "static"            # merged hashed JS / CSS

app = Flask(__name__, static_folder=None)     # we serve manually
app.config["SECRET_KEY"] = "change‑me‑for‑prod"
CORS(app, resources={r"/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*")

# room id → list[ message dict ]
rooms: Dict[str, List[dict]] = {}

# Default templates for the wizard UI.
# This can be modified in-memory by the wizards.
TEMPLATES = {
    "pinned": [
        "Hello! I am the accident report assistant. How can I help you today?",
        "Understood. I've noted that down.",
        "Thank you for the information. Is there anything else?",
        "Goodbye!",
    ],
    "contextual": {
        "general": [
            "Let's start with the basics of the report.",
            "I'm sorry, I didn't understand that. Could you please rephrase?",
            "Can you provide more details on that?"
        ],
        "date_of_accident": [
            "What was the date of the accident?",
            "Can you please provide the date (e.g., YYYY-MM-DD) when the incident occurred?",
        ],
        "time_of_accident": [
            "And at what time did it happen?",
            "Please specify the time of the accident (e.g., 4:30 PM)."
        ],
        "location": [
            "Where did the accident happen?",
            "Please describe the location of the incident in as much detail as possible.",
        ],
        "description": [
            "Please describe what happened in your own words.",
            "Can you provide a step-by-step description of the events?"
        ],
        "injuries": [
            "Were there any injuries?",
            "Please describe any injuries sustained by the parties involved."
        ]
    }
}


# ───────────────────────────────────────────────  Helpers


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save(room: str, sender: str, text) -> dict:        # text may be dict
    if not isinstance(text, str):
        # Pretty‑print JSON so it still looks nice in the chat
        text = json.dumps(text, ensure_ascii=False, indent=2)
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


# ───────────────────────────────────────────────  HTTP routes


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
    # hashed JS/CSS for *both* bundles live here
    return send_from_directory(ASSETS_DIR, filename)


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
    if kind == "wizard":
        # Send the entire template structure to the wizard who just joined
        emit("templates", TEMPLATES, to=request.sid)


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
    emit("new_message", msg, to=request.sid)

    # 2) stream to participant
    _stream_wizard_message(room, text)

    # 3) send final full msg to participant
    emit("new_message", msg, to=room, include_self=False)


@socketio.on("wizard_add_template")
def on_wizard_add_template(data):
    """
    Adds a new template to the in-memory TEMPLATES object.
    data = { type: "pinned" | "contextual", field?: string, text: string }
    """
    template_type = data.get("type")
    text = data.get("text", "").strip()

    if not text:
        return  # Ignore empty templates

    if template_type == "pinned":
        if text not in TEMPLATES["pinned"]:
            TEMPLATES["pinned"].append(text)
    elif template_type == "contextual":
        field = data.get("field")
        if field:
            if field not in TEMPLATES["contextual"]:
                TEMPLATES["contextual"][field] = []
            if text not in TEMPLATES["contextual"][field]:
                TEMPLATES["contextual"][field].append(text)

    # Broadcast the complete, updated template structure to ALL wizards
    emit("templates", TEMPLATES, broadcast=True)


# ───────────────────────────────────────────────  Main

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)