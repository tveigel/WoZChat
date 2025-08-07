# 🚀 Production Deployment Checklist for WebWOz

## ✅ Pre-Deployment Verification

Run this checklist before deploying to Render:

### 1. Local Testing Complete
- [x] ✅ Persistent storage working locally
- [x] ✅ Templates save and load correctly  
- [x] ✅ Conversations save automatically
- [x] ✅ API endpoints respond correctly
- [x] ✅ Health check shows persistent_storage: true
- [x] ✅ Data management script works

### 2. Production Files Ready
- [x] ✅ `render.yaml` configured
- [x] ✅ `verify_production.sh` executable
- [x] ✅ `manage_data.py` for data management
- [x] ✅ Enhanced error handling in app.py
- [x] ✅ Production documentation complete

### 3. Repository Status
- [ ] 🔄 All changes committed to Git
- [ ] 🔄 Repository pushed to GitHub
- [ ] 🔄 Repository connected to Render

## 🔧 Render Service Configuration

### Environment Variables to Set:
```bash
NODE_ENV=production
SECRET_KEY=[generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"]
DATA_DIR=/opt/render/project/src/data
DATABASE_URL=[your PostgreSQL connection string from Render]
```

**Important**: The `DATABASE_URL` should be the PostgreSQL connection string you got from Render. It looks like:
`postgresql://username:password@hostname:port/database_name`

### Service Settings:
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `./verify_production.sh && gunicorn -k eventlet -w 1 -b 0.0.0.0:10000 backend.app:app`
- **Plan**: Starter (minimum) or Standard (recommended for studies)

## 📊 Post-Deployment Tests

Once deployed, verify these URLs work:

1. **Health Check**: `https://your-service.onrender.com/health`
   - Should show `"persistent_storage": true`

2. **Create Test Room**: 
   ```bash
   curl -X POST https://your-service.onrender.com/api/new_room
   ```

3. **Check Statistics**:
   ```bash
   curl https://your-service.onrender.com/api/conversations/stats
   ```

4. **Test Data Management**:
   ```bash
   python manage_data.py --url https://your-service.onrender.com --action health
   ```

## 🎯 Ready for User Study

### Your WebWOz service now has:

✅ **Automatic Persistence**
- Every message saves immediately to disk
- Templates persist across restarts
- No manual export needed

✅ **Production-Ready Storage**
- Robust error handling
- Write permission verification
- Disk space monitoring

✅ **Data Management Tools**
- REST API for accessing conversations
- Automated backup scripts
- Individual conversation export

✅ **Monitoring & Health Checks**
- Real-time storage status
- Conversation statistics
- Service health verification

✅ **Render Platform Optimized**
- Automatic storage path detection
- Production environment handling
- Deployment verification scripts

## 🚨 Important Notes

1. **Storage Persistence**: 
   - Free tier = ephemeral storage (lost on restart)
   - Paid plans = can add persistent disk
   - Conversations auto-save regardless

2. **Data Access**:
   - Use API endpoints to download data
   - `manage_data.py` script for bulk operations
   - Individual conversation exports available

3. **Monitoring**:
   - Check `/health` endpoint regularly
   - Monitor `/api/conversations/stats` during study
   - Set up alerts for service issues

## 🎉 You're Ready!

Your WebWOz application is now production-ready with reliable persistent storage for your user study. The system will automatically save every conversation as it happens, ensuring no data loss.

**Next Step**: Deploy to Render and test with a few sample conversations before starting your study!
