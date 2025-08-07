#!/bin/bash
# Production deployment verification script for Render
# This script helps verify that persistent storage is working correctly on Render

echo "🚀 WebWOz Production Deployment Verification"
echo "=============================================="

# Check if we're running on Render
if [ -n "$RENDER" ]; then
    echo "✅ Running on Render platform"
    echo "📍 Render service: $RENDER_SERVICE_NAME"
    echo "📍 Git commit: $RENDER_GIT_COMMIT"
else
    echo "⚠️  Not running on Render (local development)"
fi

# Check environment variables
echo ""
echo "🔧 Environment Configuration:"
echo "NODE_ENV: ${NODE_ENV:-'not set'}"
echo "SECRET_KEY: ${SECRET_KEY:+[REDACTED]} ${SECRET_KEY:-'❌ NOT SET'}"
echo "DATA_DIR: ${DATA_DIR:-'using default'}"

# Check data directory
DATA_DIR=${DATA_DIR:-"/opt/render/project/src/data"}
echo ""
echo "📁 Storage Configuration:"
echo "Data directory: $DATA_DIR"

if [ -d "$DATA_DIR" ]; then
    echo "✅ Data directory exists"
    echo "📊 Permissions: $(stat -c '%A' "$DATA_DIR")"
    echo "📊 Owner: $(stat -c '%U:%G' "$DATA_DIR")"
    
    # Check subdirectories
    if [ -d "$DATA_DIR/conversations" ]; then
        echo "✅ Conversations directory exists"
        CONV_COUNT=$(find "$DATA_DIR/conversations" -name "*.json" -not -name "*.tmp" | wc -l)
        echo "📊 Saved conversations: $CONV_COUNT"
    else
        echo "⚠️  Conversations directory not found"
    fi
    
    if [ -f "$DATA_DIR/templates.json" ]; then
        echo "✅ Templates file exists"
    else
        echo "⚠️  Templates file not found"
    fi
else
    echo "❌ Data directory does not exist"
    echo "Creating data directory..."
    mkdir -p "$DATA_DIR/conversations"
    if [ $? -eq 0 ]; then
        echo "✅ Data directory created successfully"
    else
        echo "❌ Failed to create data directory"
        exit 1
    fi
fi

# Check disk space (important for user studies)
echo ""
echo "💾 Disk Space:"
df -h "$DATA_DIR" 2>/dev/null || df -h /

echo ""
echo "🎯 Production Readiness Checklist:"
echo "- Environment variables: ${SECRET_KEY:+✅}${SECRET_KEY:-❌}"
echo "- Data directory: $([ -d "$DATA_DIR" ] && echo "✅" || echo "❌")"
echo "- Write permissions: $([ -w "$DATA_DIR" ] && echo "✅" || echo "❌")"

# Test write access
echo ""
echo "🧪 Testing write access..."
TEST_FILE="$DATA_DIR/test_write.tmp"
if echo "test" > "$TEST_FILE" 2>/dev/null && rm "$TEST_FILE" 2>/dev/null; then
    echo "✅ Write access confirmed"
else
    echo "❌ Write access failed"
    exit 1
fi

echo ""
echo "🚀 Deployment verification complete!"

# If on Render, output helpful URLs
if [ -n "$RENDER_EXTERNAL_URL" ]; then
    echo ""
    echo "🔗 Service URLs:"
    echo "Health check: $RENDER_EXTERNAL_URL/health"
    echo "Conversations API: $RENDER_EXTERNAL_URL/api/conversations"
    echo "Statistics: $RENDER_EXTERNAL_URL/api/conversations/stats"
fi
