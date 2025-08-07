# backend/database.py
"""
Database configuration and models for WebWOz PostgreSQL integration.
Provides both PostgreSQL and file-based storage with automatic fallback.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path

try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Index
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.dialects.postgresql import UUID
    import uuid
    
    SQLALCHEMY_AVAILABLE = True
    print("✅ SQLAlchemy and PostgreSQL dependencies available")
except ImportError as e:
    print(f"⚠️ SQLAlchemy not available: {e}")
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for graceful fallback
    class declarative_base:
        def __init__(self): pass
    class Column:
        def __init__(self, *args, **kwargs): pass
    Integer = String = Text = DateTime = Boolean = UUID = Index = None

# Database models
Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    extra_data = Column(Text)  # JSON field for additional data (renamed from metadata)

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(String(50), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # 'participant', 'wizard', 'bot'
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    message_order = Column(Integer, nullable=False)  # Order within conversation
    
    # Composite index for efficient conversation queries
    __table_args__ = (
        Index('idx_room_message_order', 'room_id', 'message_order'),
        Index('idx_room_timestamp', 'room_id', 'timestamp'),
    )

class Template(Base):
    __tablename__ = 'templates'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(100), nullable=False, default='General')
    key = Column(String(200), nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class DatabaseManager:
    """
    Hybrid database manager that supports both PostgreSQL and file-based storage.
    Automatically falls back to file storage if PostgreSQL is unavailable.
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.conversations_dir = data_dir / "conversations"
        self.template_file = data_dir / "templates.json"
        
        # Initialize database connection
        self.engine = None
        self.Session = None
        self.use_postgres = False
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection with fallback to file storage."""
        if not SQLALCHEMY_AVAILABLE:
            print("📁 Using file-based storage (SQLAlchemy not available)")
            return
        
        # Try to connect to PostgreSQL
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            try:
                # Handle Render's postgres:// URL format
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'postgresql://', 1)
                
                self.engine = create_engine(
                    database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False,  # Set to True for SQL debugging
                    connect_args={
                        "options": "-c timezone=utc"  # Ensure UTC timezone
                    }
                )
                
                # Test connection
                with self.engine.connect() as conn:
                    conn.execute('SELECT 1')
                
                # Create tables
                Base.metadata.create_all(self.engine)
                self.Session = sessionmaker(bind=self.engine)
                self.use_postgres = True
                
                print(f"✅ PostgreSQL connected successfully")
                print(f"🔍 Database URL: {database_url.split('@')[0]}@[REDACTED]")
                
            except Exception as e:
                print(f"❌ PostgreSQL connection failed: {e}")
                print("📁 Falling back to file-based storage")
                self.use_postgres = False
        else:
            print("📁 Using file-based storage (DATABASE_URL not configured)")
    
    def get_session(self) -> Optional[Session]:
        """Get database session if PostgreSQL is available."""
        if self.use_postgres and self.Session:
            return self.Session()
        return None
    
    def save_message(self, room_id: str, sender: str, text: str, timestamp: str = None) -> dict:
        """Save a message using PostgreSQL or file storage."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        
        msg = {
            "sender": sender,
            "text": text,
            "timestamp": timestamp
        }
        
        if self.use_postgres:
            return self._save_message_postgres(room_id, msg)
        else:
            return self._save_message_file(room_id, msg)
    
    def _save_message_postgres(self, room_id: str, msg: dict) -> dict:
        """Save message to PostgreSQL."""
        try:
            session = self.get_session()
            if not session:
                return self._save_message_file(room_id, msg)
            
            # Get or create conversation
            conversation = session.query(Conversation).filter_by(room_id=room_id).first()
            if not conversation:
                conversation = Conversation(room_id=room_id, message_count=0)
                session.add(conversation)
            
            # Add message
            message_order = conversation.message_count + 1
            message = Message(
                room_id=room_id,
                sender=msg["sender"],
                text=msg["text"],
                timestamp=datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00')),
                message_order=message_order
            )
            session.add(message)
            
            # Update conversation
            conversation.message_count = message_order
            conversation.last_updated = datetime.now(timezone.utc)
            
            session.commit()
            session.close()
            
            print(f"✅ Message saved to PostgreSQL: {room_id} ({message_order})")
            return msg
            
        except Exception as e:
            print(f"❌ PostgreSQL save failed: {e}")
            if session:
                session.rollback()
                session.close()
            # Fallback to file storage
            return self._save_message_file(room_id, msg)
    
    def _save_message_file(self, room_id: str, msg: dict) -> dict:
        """Save message to file storage (fallback)."""
        try:
            self.conversations_dir.mkdir(parents=True, exist_ok=True)
            conversation_file = self.conversations_dir / f"{room_id}.json"
            
            # Load existing conversation
            if conversation_file.exists():
                with conversation_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
            else:
                messages = []
            
            # Add new message
            messages.append(msg)
            
            # Save updated conversation
            conversation_data = {
                "room_id": room_id,
                "created_at": messages[0]["timestamp"] if messages else msg["timestamp"],
                "last_updated": msg["timestamp"],
                "message_count": len(messages),
                "messages": messages
            }
            
            tmp_file = conversation_file.with_suffix(".json.tmp")
            with tmp_file.open("w", encoding="utf-8") as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            tmp_file.replace(conversation_file)
            
            print(f"✅ Message saved to file: {room_id} ({len(messages)})")
            return msg
            
        except Exception as e:
            print(f"❌ File save failed: {e}")
            raise
    
    def get_conversation(self, room_id: str) -> List[dict]:
        """Get conversation messages."""
        if self.use_postgres:
            return self._get_conversation_postgres(room_id)
        else:
            return self._get_conversation_file(room_id)
    
    def _get_conversation_postgres(self, room_id: str) -> List[dict]:
        """Get conversation from PostgreSQL."""
        try:
            session = self.get_session()
            if not session:
                return self._get_conversation_file(room_id)
            
            messages = session.query(Message).filter_by(room_id=room_id)\
                .order_by(Message.message_order).all()
            
            result = [
                {
                    "sender": msg.sender,
                    "text": msg.text,
                    "timestamp": msg.timestamp.isoformat(timespec="seconds")
                }
                for msg in messages
            ]
            
            session.close()
            return result
            
        except Exception as e:
            print(f"❌ PostgreSQL read failed: {e}")
            if session:
                session.close()
            return self._get_conversation_file(room_id)
    
    def _get_conversation_file(self, room_id: str) -> List[dict]:
        """Get conversation from file storage."""
        conversation_file = self.conversations_dir / f"{room_id}.json"
        if conversation_file.exists():
            try:
                with conversation_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("messages", [])
            except Exception as e:
                print(f"❌ File read failed: {e}")
        return []
    
    def list_conversations(self) -> List[dict]:
        """List all conversations with metadata."""
        if self.use_postgres:
            return self._list_conversations_postgres()
        else:
            return self._list_conversations_file()
    
    def _list_conversations_postgres(self) -> List[dict]:
        """List conversations from PostgreSQL."""
        try:
            session = self.get_session()
            if not session:
                return self._list_conversations_file()
            
            conversations = session.query(Conversation).order_by(Conversation.last_updated.desc()).all()
            
            result = [
                {
                    "room_id": conv.room_id,
                    "created_at": conv.created_at.isoformat(timespec="seconds"),
                    "last_updated": conv.last_updated.isoformat(timespec="seconds"),
                    "message_count": conv.message_count,
                    "storage_type": "postgresql"
                }
                for conv in conversations
            ]
            
            session.close()
            return result
            
        except Exception as e:
            print(f"❌ PostgreSQL list failed: {e}")
            if session:
                session.close()
            return self._list_conversations_file()
    
    def _list_conversations_file(self) -> List[dict]:
        """List conversations from file storage."""
        conversations = []
        try:
            for conv_file in self.conversations_dir.glob("*.json"):
                if conv_file.name.endswith(".tmp"):
                    continue
                try:
                    with conv_file.open(encoding="utf-8") as f:
                        data = json.load(f)
                        conversations.append({
                            **data,
                            "storage_type": "file",
                            "file_path": str(conv_file)
                        })
                except Exception as e:
                    print(f"❌ Failed to read {conv_file}: {e}")
        except Exception as e:
            print(f"❌ Failed to list conversations: {e}")
        
        conversations.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return conversations
    
    def get_stats(self) -> dict:
        """Get conversation statistics."""
        conversations = self.list_conversations()
        total_messages = sum(conv.get("message_count", 0) for conv in conversations)
        
        return {
            "total_conversations": len(conversations),
            "total_messages": total_messages,
            "average_messages_per_conversation": total_messages / len(conversations) if conversations else 0,
            "storage_type": "postgresql" if self.use_postgres else "file",
            "database_connected": self.use_postgres,
            "data_directory": str(self.data_dir),
            "conversations_directory": str(self.conversations_dir),
        }
    
    def save_templates(self, templates: dict) -> None:
        """Save templates to storage."""
        if self.use_postgres:
            self._save_templates_postgres(templates)
        else:
            self._save_templates_file(templates)
    
    def _save_templates_postgres(self, templates: dict) -> None:
        """Save templates to PostgreSQL."""
        try:
            session = self.get_session()
            if not session:
                return self._save_templates_file(templates)
            
            # Clear existing templates
            session.query(Template).delete()
            
            # Add new templates
            for category, items in templates.items():
                for key, value in items.items():
                    template = Template(
                        category=category,
                        key=key,
                        value=value,
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(template)
            
            session.commit()
            session.close()
            print("✅ Templates saved to PostgreSQL")
            
        except Exception as e:
            print(f"❌ PostgreSQL template save failed: {e}")
            if session:
                session.rollback()
                session.close()
            self._save_templates_file(templates)
    
    def _save_templates_file(self, templates: dict) -> None:
        """Save templates to file storage."""
        try:
            tmp_file = self.template_file.with_suffix(".json.tmp")
            with tmp_file.open("w", encoding="utf-8") as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            tmp_file.replace(self.template_file)
            print("✅ Templates saved to file")
        except Exception as e:
            print(f"❌ Template file save failed: {e}")
            raise
    
    def load_templates(self) -> dict:
        """Load templates from storage."""
        if self.use_postgres:
            return self._load_templates_postgres()
        else:
            return self._load_templates_file()
    
    def _load_templates_postgres(self) -> dict:
        """Load templates from PostgreSQL."""
        try:
            session = self.get_session()
            if not session:
                return self._load_templates_file()
            
            templates = session.query(Template).all()
            
            result = {}
            for template in templates:
                if template.category not in result:
                    result[template.category] = {}
                result[template.category][template.key] = template.value
            
            session.close()
            
            if not result:
                # No templates in database, create defaults
                default_templates = {
                    "General": {
                        "greeting": "Hello! How can I help you today?",
                        "understanding": "I understand. Let me look into that for you.",
                        "no_info": "I'm sorry, I don't have information about that.",
                        "goodbye": "Thank you for chatting with me. Goodbye!",
                    }
                }
                self._save_templates_postgres(default_templates)
                return default_templates
            
            return result
            
        except Exception as e:
            print(f"❌ PostgreSQL template load failed: {e}")
            if session:
                session.close()
            return self._load_templates_file()
    
    def _load_templates_file(self) -> dict:
        """Load templates from file storage."""
        if self.template_file.exists():
            try:
                with self.template_file.open(encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Template file load failed: {e}")
        
        # Return defaults
        default_templates = {
            "General": {
                "greeting": "Hello! How can I help you today?",
                "understanding": "I understand. Let me look into that for you.",
                "no_info": "I'm sorry, I don't have information about that.",
                "goodbye": "Thank you for chatting with me. Goodbye!",
            }
        }
        self._save_templates_file(default_templates)
        return default_templates
