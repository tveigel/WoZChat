# backend/app.py
"""
Flask‑SocketIO back‑end that also serves the pre‑built React bundles.

• /api/new_room          →# room id → list[ message dict ]
rooms: Dict[str, List[dict]] = {}

# Global templates dictionary (will be loaded after database manager is ready)
TEMPLATES: Dict[str, dict] = {}

# ───────────────────────────────────────────────  Storage helpers

# Global templates dictionary (will be loaded after database manager is ready)
TEMPLATES: Dict[str, dict] = {}

# room id → list[ message dict ]
rooms: Dict[str, List[dict]] = {}

# ───────────────────────────────────────────────  HTTP routes
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

from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# ───────────────────────────────────────────────  Server & paths

BASE_DIR      = Path(__file__).resolve().parent
STATIC_DIR    = BASE_DIR / "static"
PARTICIPANT_DIR = STATIC_DIR / "participant"
WIZARD_DIR      = STATIC_DIR / "wizard"
ASSETS_DIR      = STATIC_DIR / "static"         # merged hashed JS / CSS

# Debug: Print directory structure for troubleshooting
print(f"🔍 BASE_DIR: {BASE_DIR}")
print(f"🔍 STATIC_DIR exists: {STATIC_DIR.exists()}")
print(f"🔍 PARTICIPANT_DIR exists: {PARTICIPANT_DIR.exists()}")
print(f"🔍 WIZARD_DIR exists: {WIZARD_DIR.exists()}")
print(f"🔍 ASSETS_DIR exists: {ASSETS_DIR.exists()}")

if STATIC_DIR.exists():
    print(f"🔍 Contents of STATIC_DIR: {list(STATIC_DIR.iterdir())}")
else:
    print("⚠️ STATIC_DIR does not exist!")

# Persistent storage configuration for production deployment
# Priority: 1) DATA_DIR env var, 2) Render standard path, 3) Local fallback
RENDER_DATA_PATH = "/opt/render/project/src/data"
DEFAULT_DATA_PATH = str(BASE_DIR / "data")

# Determine the best data directory
if os.environ.get("DATA_DIR"):
    DATA_DIR = Path(os.environ.get("DATA_DIR"))
    print(f"🔍 Using DATA_DIR from environment: {DATA_DIR}")
elif Path(RENDER_DATA_PATH).parent.exists() and os.access(Path(RENDER_DATA_PATH).parent, os.W_OK):
    # On Render platform with write access
    DATA_DIR = Path(RENDER_DATA_PATH)
    print(f"🔍 Using Render standard path: {DATA_DIR}")
else:
    # Local development fallback
    DATA_DIR = Path(DEFAULT_DATA_PATH)
    print(f"🔍 Using local fallback path: {DATA_DIR}")

TEMPLATE_FILE = DATA_DIR / "templates.json"
CONVERSATIONS_DIR = DATA_DIR / "conversations"

# Ensure data directories exist with proper error handling
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Test write access
    test_file = DATA_DIR / ".write_test"
    test_file.write_text("test")
    test_file.unlink()
    
    print(f"✅ DATA_DIR: {DATA_DIR}")
    print(f"✅ CONVERSATIONS_DIR: {CONVERSATIONS_DIR}")
    print(f"✅ Write access confirmed")
    
except PermissionError as e:
    print(f"❌ Permission error creating data directories: {e}")
    print(f"❌ Attempted path: {DATA_DIR}")
    # Fallback to system temp directory for minimal functionality
    import tempfile
    DATA_DIR = Path(tempfile.gettempdir()) / "webwoz_data"
    DATA_DIR.mkdir(exist_ok=True)
    CONVERSATIONS_DIR = DATA_DIR / "conversations"
    CONVERSATIONS_DIR.mkdir(exist_ok=True)
    TEMPLATE_FILE = DATA_DIR / "templates.json"
    print(f"⚠️  Using temporary directory: {DATA_DIR}")
    
except Exception as e:
    print(f"❌ Unexpected error creating data directories: {e}")
    raise RuntimeError(f"Failed to initialize persistent storage: {e}")

print(f"🔍 Final storage configuration:")
print(f"   DATA_DIR exists: {DATA_DIR.exists()}")
print(f"   CONVERSATIONS_DIR exists: {CONVERSATIONS_DIR.exists()}")
print(f"   Write access: {os.access(DATA_DIR, os.W_OK)}")

# Initialize database manager (PostgreSQL + file fallback)
try:
    from .database import DatabaseManager
    print("✅ Database module imported successfully")
except ImportError:
    try:
        from database import DatabaseManager
        print("✅ Database module imported successfully (direct import)")
    except ImportError as e:
        print(f"❌ Database module import failed: {e}")
        DatabaseManager = None

# Initialize database manager
if DatabaseManager:
    db_manager = DatabaseManager(DATA_DIR)
    print(f"🔍 Database manager initialized: {db_manager.use_postgres and 'PostgreSQL' or 'File-based'}")
else:
    db_manager = None
    print("⚠️ Database manager not available - using legacy file storage")

# Initialize templates after database manager is ready
# (moved to after function definitions)

# Check available disk space (helpful for production monitoring)
try:
    import shutil
    total, used, free = shutil.disk_usage(DATA_DIR)
    free_gb = free / (1024**3)
    print(f"🔍 Available storage: {free_gb:.2f} GB")
    if free_gb < 1.0:
        print("⚠️  Warning: Low disk space (< 1GB available)")
except Exception as e:
    print(f"⚠️  Could not check disk space: {e}")

# Validate SECRET_KEY configuration
secret = os.environ.get("SECRET_KEY")
if not secret:
    # In development, use a default secret key
    if os.environ.get("NODE_ENV") == "production":
        raise RuntimeError("SECRET_KEY env var is mandatory in production")
    else:
        secret = "dev-secret-key-change-in-production"
        print("⚠️ Using default SECRET_KEY for development. Set SECRET_KEY env var for production.")

app      = Flask(__name__, static_folder=None)  # we serve manually
app.config["SECRET_KEY"] = secret

# CORS configuration - open for development, locked down for production
render_url = os.environ.get("RENDER_EXTERNAL_URL")
if render_url or os.environ.get("NODE_ENV") == "production":
    # Production: lock down to specific origins
    allowed_origins = []
    
    if render_url:
        allowed_origins.append(render_url)
        print(f"🔍 Using RENDER_EXTERNAL_URL: {render_url}")
    
    # Add the known Render URL as fallback
    allowed_origins.extend([
        "https://wozchat.onrender.com",
        "https://your-app.onrender.com"  # fallback
    ])
    
    print(f"🔍 Production CORS origins: {allowed_origins}")
    CORS(app, resources={r"/*": {"origins": allowed_origins}})
    socketio = SocketIO(app, cors_allowed_origins=allowed_origins)
else:
    # Development: allow localhost
    print("🔍 Development mode - allowing all origins")
    CORS(app, resources={r"/*": {"origins": "*"}})
    socketio = SocketIO(app, cors_allowed_origins="*")

# room id → list[ message dict ]
rooms: Dict[str, List[dict]] = {}

# ───────────────────────────────────────────────  Storage helpers

_template_lock = Lock()                         # file‑level synchronisation
_conversation_lock = Lock()                     # conversation file synchronisation


def _save_templates(data: dict) -> None:
    """Save templates using database manager or file fallback."""
    if db_manager:
        try:
            db_manager.save_templates(data)
            return
        except Exception as e:
            print(f"❌ Failed to save templates via database manager: {e}")
    
    # Fallback to legacy file storage
    tmp = TEMPLATE_FILE.with_suffix(".json.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        tmp.replace(TEMPLATE_FILE)
        print(f"✅ Templates saved to {TEMPLATE_FILE}")
    except Exception as e:
        print(f"❌ Failed to save templates: {e}")
        if tmp.exists():
            tmp.unlink()  # Clean up temp file


def _save_conversation(room_id: str, messages: List[dict]) -> None:
    """Save conversation history for a room atomically."""
    if not messages:
        return
        
    conversation_file = CONVERSATIONS_DIR / f"{room_id}.json"
    tmp_file = conversation_file.with_suffix(".json.tmp")
    
    try:
        conversation_data = {
            "room_id": room_id,
            "created_at": messages[0]["timestamp"] if messages else utc_now(),
            "last_updated": utc_now(),
            "message_count": len(messages),
            "messages": messages
        }
        
        with tmp_file.open("w", encoding="utf-8") as fh:
            json.dump(conversation_data, fh, ensure_ascii=False, indent=2)
        tmp_file.replace(conversation_file)
        print(f"✅ Conversation {room_id} saved with {len(messages)} messages")
    except Exception as e:
        print(f"❌ Failed to save conversation {room_id}: {e}")
        if tmp_file.exists():
            tmp_file.unlink()  # Clean up temp file


def _load_conversation(room_id: str) -> List[dict]:
    """Load conversation history for a room."""
    conversation_file = CONVERSATIONS_DIR / f"{room_id}.json"
    if conversation_file.exists():
        try:
            with conversation_file.open(encoding="utf-8") as fh:
                data = json.load(fh)
                messages = data.get("messages", [])
                print(f"✅ Loaded conversation {room_id} with {len(messages)} messages")
                return messages
        except Exception as e:
            print(f"❌ Failed to load conversation {room_id}: {e}")
    return []


def _list_all_conversations() -> List[dict]:
    """List all saved conversations with metadata."""
    conversations = []
    try:
        for conv_file in CONVERSATIONS_DIR.glob("*.json"):
            if conv_file.name.endswith(".tmp"):
                continue  # Skip temporary files
            try:
                with conv_file.open(encoding="utf-8") as fh:
                    data = json.load(fh)
                    conversations.append({
                        "room_id": data.get("room_id"),
                        "created_at": data.get("created_at"),
                        "last_updated": data.get("last_updated"),
                        "message_count": data.get("message_count", 0),
                        "file_path": str(conv_file)
                    })
            except Exception as e:
                print(f"❌ Failed to read conversation file {conv_file}: {e}")
    except Exception as e:
        print(f"❌ Failed to list conversations: {e}")
    
    # Sort by last_updated, newest first
    conversations.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
    return conversations


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
    """Load templates using database manager or file fallback."""
    if db_manager:
        try:
            return db_manager.load_templates()
        except Exception as e:
            print(f"❌ Failed to load templates from database manager: {e}")
    
    # Fallback to legacy file loading
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

# TEMPLATES will be initialized after database manager setup

# ───────────────────────────────────────────────  Misc helpers


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _persist_and_broadcast() -> None:
    """Save TEMPLATES and push the fresh set to all connected wizards."""
    global TEMPLATES
    _save_templates(TEMPLATES)
    # Broadcast to every connected client (wizard UI filters internally)
    socketio.emit("templates", TEMPLATES)


def save(room: str, sender: str, text: str) -> dict:
    """
    Save a message and ensure it's persisted continuously.
    This function guarantees that every message from the frontend-participant
    is stored in both in-memory and persistent storage.
    """
    timestamp = utc_now()
    msg = {"sender": sender, "text": text, "timestamp": timestamp}
    
    # Add to in-memory storage immediately for real-time display
    rooms.setdefault(room, []).append(msg)
    
    # Ensure continuous persistence - try database first, then file fallback
    persistence_success = False
    
    if db_manager:
        try:
            # Try PostgreSQL persistence first (Render deployment)
            saved_msg = db_manager.save_message(room, sender, text, timestamp)
            if saved_msg:
                persistence_success = True
                print(f"💾 Message saved to PostgreSQL: {room} ({sender})")
        except Exception as e:
            print(f"❌ PostgreSQL save failed for {room}: {e}")
    
    # If PostgreSQL failed or not available, use file fallback
    if not persistence_success:
        with _conversation_lock:
            try:
                _save_conversation(room, rooms[room])
                persistence_success = True
                print(f"💾 Message saved to file: {room} ({sender})")
            except Exception as e:
                print(f"❌ File save also failed for {room}: {e}")
    
    # Log if all persistence methods failed (critical error)
    if not persistence_success:
        print(f"🚨 CRITICAL: Message not persisted for room {room}! Message: {msg}")
        # Could implement emergency backup here (e.g., append to emergency log)
    
    return msg


def _load_rooms_from_disk() -> None:
    """
    Load all existing conversations into memory on startup.
    Ensures proper sync between persistent storage and in-memory cache.
    """
    print("🔄 Loading existing conversations...")
    
    if db_manager and db_manager.use_postgres:
        try:
            # Load from PostgreSQL (production/Render deployment)
            conversations = db_manager.list_conversations()
            loaded_count = 0
            for conv in conversations:
                room_id = conv['room_id']
                messages = db_manager.get_conversation(room_id)
                if messages:
                    rooms[room_id] = messages
                    loaded_count += 1
                    print(f"✅ Loaded room {room_id} with {len(messages)} messages from PostgreSQL")
            
            print(f"🔄 Loaded {loaded_count} conversations from PostgreSQL database")
            
            # Also check for any orphaned file conversations and migrate them
            await_migration_count = 0
            try:
                for conv_file in CONVERSATIONS_DIR.glob("*.json"):
                    if conv_file.name.endswith(".tmp"):
                        continue
                    
                    room_id = conv_file.stem
                    if room_id not in rooms:  # Not in PostgreSQL yet
                        file_messages = _load_conversation(room_id)
                        if file_messages:
                            # Migrate to PostgreSQL
                            for msg in file_messages:
                                try:
                                    db_manager.save_message(
                                        room_id, 
                                        msg["sender"], 
                                        msg["text"], 
                                        msg["timestamp"]
                                    )
                                except Exception as e:
                                    print(f"⚠️ Failed to migrate message for {room_id}: {e}")
                            
                            rooms[room_id] = file_messages
                            await_migration_count += 1
                            print(f"🔄 Migrated room {room_id} from file to PostgreSQL")
                
                if await_migration_count > 0:
                    print(f"✅ Migrated {await_migration_count} conversations to PostgreSQL")
                    
            except Exception as e:
                print(f"⚠️ Migration check failed: {e}")
            
            return
            
        except Exception as e:
            print(f"❌ Failed to load from PostgreSQL: {e}")
            print("📁 Falling back to file-based loading...")
    
    # Fallback to file-based loading (development or database unavailable)
    try:
        loaded_count = 0
        for conv_file in CONVERSATIONS_DIR.glob("*.json"):
            if conv_file.name.endswith(".tmp"):
                continue  # Skip temporary files
                
            room_id = conv_file.stem  # filename without extension
            messages = _load_conversation(room_id)
            if messages:
                rooms[room_id] = messages
                loaded_count += 1
                print(f"✅ Loaded room {room_id} with {len(messages)} messages from file")
        
        print(f"🔄 Loaded {loaded_count} conversations from files")
    except Exception as e:
        print(f"❌ Failed to load conversations from disk: {e}")


def _stream_wizard_message(room: str, text: str) -> None:
    words = text.split()
    for i, w in enumerate(words):
        socketio.sleep(1)  # 1 second typing speed for better visibility
        socketio.emit(
            "stream_chunk",
            {"word": w, "is_last": i == len(words) - 1},
            to=room,
        )

# ───────────────────────────────────────────────  HTTP routes


@app.post("/api/new_room")
def new_room():
    room_id = uuid.uuid4().hex[:8]
    
    # Ensure the room ID is unique (check both memory and disk)
    while room_id in rooms or (CONVERSATIONS_DIR / f"{room_id}.json").exists():
        room_id = uuid.uuid4().hex[:8]
    
    rooms[room_id] = []
    print(f"✅ Created new room: {room_id}")
    return jsonify({"room": room_id})


@app.route("/health")
def health_check():
    """Health check endpoint for deployment verification and database status"""
    # Get conversation stats
    total_conversations = len(rooms)
    total_saved_conversations = len(list(CONVERSATIONS_DIR.glob("*.json")))
    
    # Database status
    db_status = {
        "available": db_manager is not None,
        "using_postgres": db_manager.use_postgres if db_manager else False,
        "database_url_configured": bool(os.environ.get('DATABASE_URL')),
    }
    
    if db_manager and db_manager.use_postgres:
        try:
            # Test database connectivity
            db_conversations = db_manager.list_conversations()
            db_status["postgres_healthy"] = True
            db_status["postgres_conversations"] = len(db_conversations)
        except Exception as e:
            db_status["postgres_healthy"] = False
            db_status["postgres_error"] = str(e)
    
    return jsonify({
        "status": "healthy",
        "timestamp": utc_now(),
        "bot_available": BOT_AVAILABLE,
        "static_dir_exists": STATIC_DIR.exists(),
        "participant_dir_exists": PARTICIPANT_DIR.exists(),
        "wizard_dir_exists": WIZARD_DIR.exists(),
        "assets_dir_exists": ASSETS_DIR.exists(),
        "data_dir": str(DATA_DIR),
        "data_dir_exists": DATA_DIR.exists(),
        "conversations_dir_exists": CONVERSATIONS_DIR.exists(),
        "active_conversations": total_conversations,
        "saved_conversations": total_saved_conversations,
        "persistent_storage": DATA_DIR.exists() and CONVERSATIONS_DIR.exists(),
        "database": db_status
    })


@app.route("/")
def root():
    """Redirect root URL to wizard interface"""
    return redirect("/wizard")


@app.route("/wizard")
@app.route("/wizard/<room_id>")
def wizard_app(room_id: str | None = None):
    if not WIZARD_DIR.exists():
        return jsonify({"error": "Wizard app not available. Static files missing."}), 404
    return send_from_directory(WIZARD_DIR, "index.html")


@app.route("/chat/<room_id>")
def participant_app(room_id: str):
    if not PARTICIPANT_DIR.exists():
        return jsonify({"error": "Participant app not available. Static files missing."}), 404
    return send_from_directory(PARTICIPANT_DIR, "index.html")


@app.route("/static/<path:filename>")
def static_assets(filename):
    # In development, we don't serve static assets - React dev server handles this
    # In production (Docker), serve from the copied static directories
    
    if not ASSETS_DIR.exists():
        # Development mode - let React dev server handle static assets
        from flask import abort
        abort(404)
    
    # Production mode - handle separated bundles
    if filename.startswith("p/"):
        # Participant bundle assets: /static/p/static/js/file.js -> /static/static/p/static/js/file.js
        return send_from_directory(ASSETS_DIR / "p", filename[2:])
    elif filename.startswith("w/"):
        # Wizard bundle assets: /static/w/static/js/file.js -> /static/static/w/static/js/file.js  
        return send_from_directory(ASSETS_DIR / "w", filename[2:])
    else:
        # Try wizard assets first (for production builds with PUBLIC_URL=/static/w)
        wizard_file = ASSETS_DIR / "w" / filename
        if wizard_file.exists():
            return send_from_directory(ASSETS_DIR / "w", filename)
        
        # Try participant assets 
        participant_file = ASSETS_DIR / "p" / filename
        if participant_file.exists():
            return send_from_directory(ASSETS_DIR / "p", filename)
        
        # Fallback to original location if it exists
        fallback_file = ASSETS_DIR / filename
        if fallback_file.exists():
            return send_from_directory(ASSETS_DIR, filename)
        
        # File not found
        from flask import abort
        abort(404)


# ─────────────────────  ↑ existing routes unchanged – NEW below  ↑

# ───────────────────────────────────────────────  Bot Control API

@app.get("/api/bot/<room_id>/status")
def get_bot_status(room_id: str):
    """Get bot status for a specific room."""
    if not BOT_AVAILABLE or not bot_manager:
        return jsonify({
            "active": False,
            "available": False,
            "progress": "Bot not available"
        })
    
    status = bot_manager.get_bot_status(room_id)
    return jsonify(status)


@app.post("/api/bot/<room_id>/start")
def start_bot(room_id: str):
    """Start the bot for a specific room."""
    if not BOT_AVAILABLE or not bot_manager:
        return jsonify({
            "status": "error", 
            "message": "Bot service is not available. Please check the server configuration."
        })
    
    response_message = bot_manager.start_bot(room_id)
    
    if response_message and bot_manager.is_bot_active(room_id):
        # Send bot activation message to the room
        msg = save(room_id, "bot", response_message)
        msg["room"] = room_id
        socketio.emit("new_message", msg, to=room_id)
        
        # Notify wizard that bot is now active
        socketio.emit("bot_status_changed", {
            "room": room_id, 
            "active": True,
            "message": "Bot activated successfully"
        }, to=room_id)
        
        return jsonify({"status": "success", "message": response_message})
    else:
        return jsonify({"status": "error", "message": response_message or "Failed to start bot"})


@app.post("/api/bot/<room_id>/stop") 
def stop_bot(room_id: str):
    """Stop the bot for a specific room."""
    if not BOT_AVAILABLE or not bot_manager:
        return jsonify({
            "status": "error",
            "message": "Bot service is not available."
        })
    
    response_message = bot_manager.stop_bot(room_id)
    
    # Send bot deactivation message to the room
    msg = save(room_id, "bot", response_message)
    msg["room"] = room_id
    socketio.emit("new_message", msg, to=room_id)
    
    # Notify wizard that bot is now inactive
    socketio.emit("bot_status_changed", {
        "room": room_id,
        "active": False, 
        "message": "Bot deactivated"
    }, to=room_id)
    
    return jsonify({"status": "success", "message": response_message})


# ───────────────────────────────────────────────  Conversation Management API

@app.get("/api/conversations")
def list_conversations():
    """List all saved conversations with metadata."""
    conversations = _list_all_conversations()
    return jsonify({
        "conversations": conversations,
        "total_count": len(conversations)
    })


@app.get("/api/conversations/<room_id>")
def get_conversation(room_id: str):
    """Get full conversation history for a specific room."""
    messages = _load_conversation(room_id)
    if not messages:
        return jsonify({"error": "Conversation not found"}), 404
    
    return jsonify({
        "room_id": room_id,
        "message_count": len(messages),
        "messages": messages
    })


@app.get("/api/conversations/<room_id>/export")
def export_conversation(room_id: str):
    """Export conversation as downloadable JSON file."""
    messages = _load_conversation(room_id)
    if not messages:
        return jsonify({"error": "Conversation not found"}), 404
    
    conversation_data = {
        "room_id": room_id,
        "exported_at": utc_now(),
        "message_count": len(messages),
        "messages": messages
    }
    
    from flask import make_response
    response = make_response(json.dumps(conversation_data, indent=2, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=conversation_{room_id}.json'
    return response


@app.delete("/api/conversations/<room_id>")
def delete_conversation(room_id: str):
    """Delete a conversation from persistent storage."""
    conversation_file = CONVERSATIONS_DIR / f"{room_id}.json"
    
    if not conversation_file.exists():
        return jsonify({"error": "Conversation not found"}), 404
    
    try:
        conversation_file.unlink()
        # Also remove from memory if present
        if room_id in rooms:
            del rooms[room_id]
        
        return jsonify({"status": "deleted", "room_id": room_id})
    except Exception as e:
        return jsonify({"error": f"Failed to delete conversation: {e}"}), 500


@app.get("/api/conversations/stats")
def conversation_stats():
    """Get statistics about stored conversations."""
    conversations = _list_all_conversations()
    
    total_messages = sum(conv.get("message_count", 0) for conv in conversations)
    
    stats = {
        "total_conversations": len(conversations),
        "total_messages": total_messages,
        "average_messages_per_conversation": total_messages / len(conversations) if conversations else 0,
        "data_directory": str(DATA_DIR),
        "conversations_directory": str(CONVERSATIONS_DIR),
        "storage_available": DATA_DIR.exists(),
    }
    
    return jsonify(stats)


@app.get("/api/templates")
def list_templates():
    """Return the currently active template dictionary."""
    global TEMPLATES
    return jsonify(TEMPLATES)


@app.post("/api/templates")
def create_template():
    """Add a new template:  {key, value}  in JSON body."""
    global TEMPLATES
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
    
    # Ensure complete conversation history is available
    # Load from persistent storage if not in memory
    if room not in rooms or not rooms[room]:
        if db_manager:
            try:
                messages = db_manager.get_conversation(room)
                if messages:
                    rooms[room] = messages
                    print(f"🔄 Loaded conversation {room} from database for joining {kind}")
            except Exception as e:
                print(f"❌ Failed to load conversation from database: {e}")
                # Try file fallback
                messages = _load_conversation(room)
                if messages:
                    rooms[room] = messages
                    print(f"🔄 Loaded conversation {room} from file for joining {kind}")
        else:
            # File-only mode
            messages = _load_conversation(room)
            if messages:
                rooms[room] = messages
                print(f"🔄 Loaded conversation {room} from file for joining {kind}")
    
    # Send complete message history to the joining user
    if room in rooms and rooms[room]:
        print(f"📤 Sending {len(rooms[room])} messages to {kind} in {room}")
        for msg in rooms[room]:
            msg_with_room = {**msg, "room": room}
            emit("new_message", msg_with_room)
    else:
        print(f"📭 No message history found for room {room}")
    
    if kind == "wizard":
        # Send templates to wizard
        global TEMPLATES
        emit("templates", TEMPLATES)
        
        # Send bot status to wizard
        if BOT_AVAILABLE and bot_manager:
            bot_status = bot_manager.get_bot_status(room)
            emit("bot_status_changed", {
                "room": room,
                "active": bot_status["active"],
                "available": bot_status["available"],
                "progress": bot_status.get("progress", "")
            })
        else:
            emit("bot_status_changed", {
                "room": room,
                "active": False,
                "available": False,
                "progress": "Bot service unavailable"
            })


@socketio.on("leave")
def on_leave(data):
    room = data.get("room", "default_room")
    leave_room(room)
    print(f"User left {room}")


@socketio.on("participant_typing")
def on_participant_typing(data):
    room = data.get("room", "default_room")
    emit(
        "participant_is_typing",
        {"text": data.get("text", ""), "room": room},
        to=room,
        include_self=False,
    )


@socketio.on("participant_message")
def on_participant_message(data):
    room = data.get("room", "default_room")
    text = data.get("text", "")
    
    # Check if bot is active for this room
    if BOT_AVAILABLE and bot_manager and bot_manager.is_bot_active(room):
        # Let bot handle the message
        bot_response = bot_manager.process_message(room, text)
        
        # Save participant message
        msg = save(room, "participant", text)
        msg["room"] = room
        emit("new_message", msg, to=room)
        
        # Send bot response if available
        if bot_response:
            bot_msg = save(room, "bot", bot_response)
            bot_msg["room"] = room
            emit("new_message", bot_msg, to=room)
            
            # Check if bot completed the form and deactivated
            if not bot_manager.is_bot_active(room):
                socketio.emit("bot_status_changed", {
                    "room": room,
                    "active": False,
                    "message": "Bot session completed"
                }, to=room)
    else:
        # Normal participant message handling
        msg = save(room, "participant", text)
        msg["room"] = room
        emit("new_message", msg, to=room)


@socketio.on("wizard_response")
def on_wizard_response(data):
    room = data.get("room", "default_room")
    text = data.get("text", "")
    msg = save(room, "wizard", text)
    msg["room"] = room  # Include room in message

    # 1) show full msg immediately to the wizard only
    emit("new_message", msg)

    # 2) send final full msg to participant immediately (no streaming for now)
# ───────────────────────────────────────────────  Initialization

# Import bot manager with error handling
try:
    from .bot_integration import bot_manager
    BOT_AVAILABLE = True
    print("✅ Bot integration imported successfully")
except ImportError as e:
    print(f"⚠️ Bot integration not available with relative import: {e}")
    try:
        from bot_integration import bot_manager
        BOT_AVAILABLE = True
        print("✅ Bot integration imported successfully (direct import)")
    except ImportError as e2:
        print(f"⚠️ Bot integration not available: {e2}")
        import traceback
        traceback.print_exc()
        bot_manager = None
        BOT_AVAILABLE = False

# Initialize templates and load conversations after all functions are defined
TEMPLATES = _load_templates()
print(f"✅ Templates loaded: {len(TEMPLATES)} categories")

# Load existing conversations from persistent storage on startup
_load_rooms_from_disk()
print(f"🔄 Server initialization complete")

# ───────────────────────────────────────────────  Main

if __name__ == "__main__":
    # `debug=True` stays exactly as before – hot‑reload still works
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
