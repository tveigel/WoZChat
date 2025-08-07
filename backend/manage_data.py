#!/usr/bin/env python3
"""
Production data management script for WebWOz on Render.
Provides easy access to conversation data and backup functionality.
"""

import json
import requests
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class WebWozDataManager:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def check_health(self) -> Dict:
        """Check service health and storage status."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {}
    
    def get_stats(self) -> Dict:
        """Get conversation statistics."""
        try:
            response = self.session.get(f"{self.base_url}/api/conversations/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get stats: {e}")
            return {}
    
    def list_conversations(self) -> List[Dict]:
        """List all conversations."""
        try:
            response = self.session.get(f"{self.base_url}/api/conversations")
            response.raise_for_status()
            data = response.json()
            return data.get('conversations', [])
        except Exception as e:
            print(f"❌ Failed to list conversations: {e}")
            return []
    
    def get_conversation(self, room_id: str) -> Optional[Dict]:
        """Get specific conversation."""
        try:
            response = self.session.get(f"{self.base_url}/api/conversations/{room_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get conversation {room_id}: {e}")
            return None
    
    def export_conversation(self, room_id: str, output_file: str) -> bool:
        """Export specific conversation to file."""
        try:
            response = self.session.get(f"{self.base_url}/api/conversations/{room_id}/export")
            response.raise_for_status()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✅ Exported conversation {room_id} to {output_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to export conversation {room_id}: {e}")
            return False
    
    def backup_all_conversations(self, output_dir: str) -> bool:
        """Backup all conversations to a directory."""
        conversations = self.list_conversations()
        if not conversations:
            print("⚠️  No conversations found to backup")
            return False
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        success_count = 0
        for conv in conversations:
            room_id = conv['room_id']
            filename = f"conversation_{room_id}_{timestamp}.json"
            filepath = output_path / filename
            
            if self.export_conversation(room_id, str(filepath)):
                success_count += 1
        
        # Create summary file
        summary = {
            "backup_timestamp": datetime.now().isoformat(),
            "total_conversations": len(conversations),
            "successful_exports": success_count,
            "conversations": conversations
        }
        
        summary_file = output_path / f"backup_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Backup complete: {success_count}/{len(conversations)} conversations exported")
        print(f"📁 Backup directory: {output_path}")
        return success_count == len(conversations)

def main():
    parser = argparse.ArgumentParser(description="WebWOz Production Data Manager")
    parser.add_argument("--url", required=True, help="Base URL of the WebWOz service")
    parser.add_argument("--action", choices=["health", "stats", "list", "export", "backup"], 
                       required=True, help="Action to perform")
    parser.add_argument("--room-id", help="Room ID for export action")
    parser.add_argument("--output", help="Output file/directory")
    
    args = parser.parse_args()
    
    manager = WebWozDataManager(args.url)
    
    if args.action == "health":
        health = manager.check_health()
        print("🏥 Service Health:")
        print(json.dumps(health, indent=2))
        
    elif args.action == "stats":
        stats = manager.get_stats()
        print("📊 Conversation Statistics:")
        print(json.dumps(stats, indent=2))
        
    elif args.action == "list":
        conversations = manager.list_conversations()
        print(f"💬 Found {len(conversations)} conversations:")
        for conv in conversations:
            print(f"  - {conv['room_id']}: {conv['message_count']} messages "
                  f"(last updated: {conv['last_updated']})")
    
    elif args.action == "export":
        if not args.room_id:
            print("❌ --room-id required for export action")
            sys.exit(1)
        
        output_file = args.output or f"conversation_{args.room_id}.json"
        manager.export_conversation(args.room_id, output_file)
    
    elif args.action == "backup":
        output_dir = args.output or f"webwoz_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        manager.backup_all_conversations(output_dir)

if __name__ == "__main__":
    main()
