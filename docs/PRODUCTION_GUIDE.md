# 🚀 WebWOz Production Deployment on Render - Complete Guide

## 📋 Pre-Deployment Checklist

### 1. Repository Setup
- [ ] All code committed to GitHub
- [ ] `render.yaml` in repository root
- [ ] Environment variables documented
- [ ] Production scripts executable

### 2. Render Service Configuration

#### Option A: Using render.yaml (Recommended)
1. Place the `render.yaml` file in your repository root
2. Connect your GitHub repository to Render
3. Render will automatically use the configuration

#### Option B: Manual Configuration
If not using render.yaml, configure manually:

- **Build Command**:
  ```bash
  pip install -r backend/requirements.txt && 
  cd frontend-participant && npm install && npm run build && 
  cd ../frontend-wizard && npm install && npm run build &&
  mkdir -p backend/static/participant backend/static/wizard &&
  cp -r frontend-participant/build/* backend/static/participant/ &&
  cp -r frontend-wizard/build/* backend/static/wizard/
  ```

- **Start Command**:
  ```bash
  ./verify_production.sh && gunicorn -k eventlet -w 1 -b 0.0.0.0:10000 backend.app:app
  ```

### 3. Required Environment Variables

Set these in your Render service dashboard:

| Variable | Value | Description |
|----------|--------|-------------|
| `NODE_ENV` | `production` | Enables production mode |
| `SECRET_KEY` | `[generate secure key]` | Flask session security |
| `DATA_DIR` | `/opt/render/project/src/data` | Storage location |

**To generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 💾 Storage Configuration Options

### Option 1: Ephemeral Storage (Free Tier)
- Data persists during service lifetime
- Lost on restarts/deployments
- Good for testing, not production studies

### Option 2: Persistent Disk (Paid Plans)
- Data persists across restarts
- Recommended for user studies
- Add to render.yaml:
```yaml
disks:
  - name: webwoz-data
    mountPath: /opt/render/project/src/data
    sizeGB: 10
```

## 🔧 Deployment Steps

### 1. Connect Repository
1. Go to Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the repository with WebWOz

### 2. Configure Service
- **Name**: `webwoz-chat` (or your preferred name)
- **Environment**: `Python 3`
- **Plan**: Start with `Starter` (upgrade to `Standard` for persistent disk)
- **Build & Start Commands**: See above or use render.yaml

### 3. Set Environment Variables
Add the required environment variables in the service settings.

### 4. Deploy
Click "Create Web Service" - Render will build and deploy automatically.

## 📊 Post-Deployment Verification

### 1. Service Health Check
Visit: `https://your-service.onrender.com/health`

Expected response:
```json
{
  "status": "healthy",
  "persistent_storage": true,
  "data_dir_exists": true,
  "conversations_dir_exists": true,
  "saved_conversations": 0
}
```

### 2. Test Conversation Storage
1. Create a test conversation:
   ```bash
   curl -X POST https://your-service.onrender.com/api/new_room
   ```
2. Visit the chat room and send messages
3. Check persistence:
   ```bash
   curl https://your-service.onrender.com/api/conversations/stats
   ```

### 3. Verify Data Access
Test the data management API:
```bash
# Using the provided script
python manage_data.py --url https://your-service.onrender.com --action stats
```

## 🔄 Data Management in Production

### Regular Backups
Schedule regular backups of your conversation data:

```bash
# Backup all conversations
python manage_data.py --url https://your-service.onrender.com --action backup --output study_backup_$(date +%Y%m%d)

# Export specific conversation
python manage_data.py --url https://your-service.onrender.com --action export --room-id abc123 --output participant_001.json
```

### Monitoring During User Study
Monitor your study progress:

```bash
# Check statistics
curl https://your-service.onrender.com/api/conversations/stats

# List all conversations
curl https://your-service.onrender.com/api/conversations | jq '.conversations[] | {room_id, message_count, last_updated}'
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "Permission Denied" Errors
- Check DATA_DIR environment variable
- Verify service has write permissions
- Check logs: `curl https://your-service.onrender.com/health`

#### 2. "Storage Not Found" Errors
- Ensure DATA_DIR path is correct
- Check if persistent disk is properly mounted
- Verify build completed successfully

#### 3. Data Not Persisting
- Confirm persistent disk configuration
- Check if using ephemeral storage (free tier)
- Verify conversations are being saved: `/api/conversations/stats`

### Debug Commands
Add these to troubleshoot storage issues:

```bash
# Check storage status
curl https://your-service.onrender.com/health

# List conversations
curl https://your-service.onrender.com/api/conversations

# Get detailed stats
curl https://your-service.onrender.com/api/conversations/stats
```

## 📈 Scaling for Large Studies

### Performance Considerations
- **Concurrent Users**: Single worker handles ~50-100 concurrent users
- **Storage**: Plan ~1KB per message, estimate total storage needs
- **Bandwidth**: Consider message frequency and user count

### Recommended Render Plans
- **Small Study** (< 50 users): Starter plan
- **Medium Study** (50-200 users): Standard plan + persistent disk
- **Large Study** (200+ users): Pro plan + larger persistent disk

### Monitoring Metrics
Set up monitoring for:
- Service health (`/health` endpoint)
- Storage usage (`/api/conversations/stats`)
- Response times
- Error rates

## 🎯 User Study Best Practices

### Before Starting
1. Deploy and test with dummy conversations
2. Verify data export functionality
3. Set up monitoring/backup procedures
4. Test service restart (data should persist)

### During Study
1. Monitor storage usage regularly
2. Backup data daily during active collection
3. Check service health periodically
4. Keep conversation export scripts ready

### After Study
1. Export all conversation data
2. Create final backup
3. Document any issues encountered
4. Archive data according to your institution's policies

## 📞 Support and Resources

- **Render Docs**: https://render.com/docs
- **Service Logs**: Available in Render dashboard
- **Health Check**: `https://your-service.onrender.com/health`
- **API Documentation**: See PERSISTENCE_SUMMARY.md

Your WebWOz service is now ready for production deployment with reliable conversation persistence! 🎉
