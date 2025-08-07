# Render Deployment Guide with Persistent Storage

## Required Configuration for Persistent Storage

### 1. Environment Variables

Set these environment variables in your Render service:

```bash
# Required for production
SECRET_KEY=your-secret-key-here
NODE_ENV=production

# Persistent storage configuration
DATA_DIR=/opt/render/project/src/data

# Optional: Custom template directory (defaults to DATA_DIR)
TEMPLATE_DIR=/opt/render/project/src/data
```

### 2. Render Service Settings

- **Build Command**: `npm run build-all`
- **Start Command**: `gunicorn -k eventlet -w 1 -b 0.0.0.0:10000 backend.app:app`
- **Environment**: Python 3.11+

### 3. Persistent Disk (Optional but Recommended for Production)

For large-scale user studies, consider adding a persistent disk:

1. Go to your Render service settings
2. Add a persistent disk (e.g., 10GB)
3. Mount it to `/opt/render/project/src/data`
4. Update the `DATA_DIR` environment variable if needed

## Storage Structure

The application will create the following structure:

```
/opt/render/project/src/data/
├── templates.json              # Template storage
└── conversations/              # Conversation history
    ├── room1234.json          # Individual conversation files
    ├── room5678.json
    └── ...
```

## API Endpoints for Data Management

### Conversation Management

- `GET /api/conversations` - List all conversations with metadata
- `GET /api/conversations/{room_id}` - Get specific conversation
- `GET /api/conversations/{room_id}/export` - Download conversation as JSON
- `DELETE /api/conversations/{room_id}` - Delete conversation
- `GET /api/conversations/stats` - Get storage statistics

### Health Check

- `GET /health` - Check service health and storage status

## Features

### Automatic Persistence

- **Templates**: Automatically saved when created/updated via the UI
- **Conversations**: Every message is automatically saved to disk
- **Recovery**: All conversations are loaded from disk on server restart

### Data Export

Individual conversations can be exported as JSON files through the API, providing backup capabilities for your user study data.

### Monitoring

Use the `/health` endpoint to monitor storage status and ensure persistent storage is working correctly.

## Backup Recommendations

For critical user studies:

1. Regularly download conversation data via the API
2. Monitor storage usage through the stats endpoint
3. Set up automated backups if using persistent disks
4. Test recovery by restarting the service and verifying data persistence

## Example Usage

```bash
# Check storage status
curl https://your-app.onrender.com/health

# List all conversations
curl https://your-app.onrender.com/api/conversations

# Export specific conversation
curl https://your-app.onrender.com/api/conversations/abc12345/export -o conversation.json

# Get storage statistics
curl https://your-app.onrender.com/api/conversations/stats
```
