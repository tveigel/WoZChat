# 🐘 PostgreSQL Integration for WebWOz

## ✅ What's Been Added

### 1. **Hybrid Storage System**
- **Primary**: PostgreSQL database for production reliability
- **Fallback**: File-based storage if database unavailable
- **Automatic**: Seamless switching between storage types

### 2. **Database Schema**
```sql
-- Conversations table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    metadata TEXT
);

-- Messages table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(50) NOT NULL,
    sender VARCHAR(20) NOT NULL,
    text TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_order INTEGER NOT NULL
);

-- Templates table
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL DEFAULT 'General',
    key VARCHAR(200) NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. **Enhanced Features**
- **Atomic operations** prevent data corruption
- **Connection pooling** for performance
- **Automatic table creation** on first run
- **Error handling** with graceful fallbacks

## 🔧 Render Setup Steps

### 1. Create PostgreSQL Database
1. In your Render dashboard, go to "New +" → "PostgreSQL"
2. Choose your plan (Free tier available for testing)
3. Note the connection details provided

### 2. Get Connection String
Render provides the connection string in this format:
```
postgresql://username:password@hostname:port/database_name
```

### 3. Add to Environment Variables
In your Render web service settings, add:
```bash
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

### 4. Deploy
Your application will automatically:
- Connect to PostgreSQL
- Create required tables
- Fall back to file storage if connection fails

## 📊 Benefits of PostgreSQL

### **Production Ready**
- ✅ ACID compliance
- ✅ Concurrent user support
- ✅ Data integrity guarantees
- ✅ Backup and recovery

### **Scalability**
- ✅ Handles thousands of conversations
- ✅ Efficient indexing for fast queries
- ✅ Connection pooling for performance
- ✅ No file system limitations

### **User Study Advantages**
- ✅ Real-time conversation statistics
- ✅ Powerful querying capabilities
- ✅ Data export in multiple formats
- ✅ Reliable data persistence

## 🧪 Testing Locally

### Option 1: Use Render PostgreSQL
Set your DATABASE_URL environment variable to your Render PostgreSQL connection string.

### Option 2: Local PostgreSQL
```bash
# Install PostgreSQL locally
sudo apt-get install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb webwoz_dev

# Set environment variable
export DATABASE_URL=postgresql://localhost/webwoz_dev
```

### Option 3: File Fallback
Don't set DATABASE_URL - the application will use file-based storage automatically.

## 🔍 Monitoring

### Check Database Connection
```bash
curl https://your-app.onrender.com/health
```

Look for:
```json
{
  "database_connected": true,
  "storage_type": "postgresql"
}
```

### View Statistics
```bash
curl https://your-app.onrender.com/api/conversations/stats
```

### Database Queries (via Render Dashboard)
```sql
-- Total conversations
SELECT COUNT(*) FROM conversations;

-- Messages per day
SELECT DATE(timestamp), COUNT(*) 
FROM messages 
GROUP BY DATE(timestamp) 
ORDER BY DATE(timestamp);

-- Most active conversations
SELECT room_id, message_count 
FROM conversations 
ORDER BY message_count DESC 
LIMIT 10;
```

## 🚀 Deployment Impact

### **Minimal Changes Required**
- ✅ All existing functionality preserved
- ✅ API endpoints unchanged
- ✅ File export still works
- ✅ Backward compatibility maintained

### **Enhanced Reliability**
- ✅ Data survives service restarts
- ✅ Multiple concurrent users supported
- ✅ Transaction safety for data integrity
- ✅ Professional-grade data storage

Your WebWOz application now has enterprise-grade data persistence ready for large-scale user studies! 🎉

## 🔄 Migration from File Storage

Existing file-based conversations will continue to work. The system will:
1. Load existing file conversations on startup
2. Store new conversations in PostgreSQL
3. Gradually migrate to full database storage

No data loss occurs during the transition!
