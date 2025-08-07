# Documentation

This folder contains all project documentation files.

## Contents

### 📋 [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
Pre-deployment verification checklist for production environments.

### 🔄 [PERSISTENCE_SUMMARY.md](./PERSISTENCE_SUMMARY.md)
Overview of the persistent storage implementation and architecture.

### 🐘 [POSTGRESQL_INTEGRATION.md](./POSTGRESQL_INTEGRATION.md)
Complete guide for PostgreSQL database integration and configuration.

### 🚀 [PRODUCTION_GUIDE.md](./PRODUCTION_GUIDE.md)
Comprehensive production deployment and management guide.

### ☁️ [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)
Step-by-step guide for deploying to Render platform.

## Quick Start

1. Start with [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for initial deployment
2. Review [POSTGRESQL_INTEGRATION.md](./POSTGRESQL_INTEGRATION.md) for database setup
3. Follow [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) before going live
4. Reference [PRODUCTION_GUIDE.md](./PRODUCTION_GUIDE.md) for ongoing management

## Architecture Overview

The project uses a hybrid storage system:
- **Primary**: PostgreSQL database for production
- **Fallback**: File-based storage for development
- **Real-time**: WebSocket communication via Flask-SocketIO

For detailed technical information, see [PERSISTENCE_SUMMARY.md](./PERSISTENCE_SUMMARY.md).
