# WebWOz – One‑Click Wizard‑of‑Oz Chat

**A production-ready research platform for simulating AI chatbots with human wizards.**

WebWOz enables researchers to conduct Wizard-of-Oz studies where human operators (wizards) simulate AI chatbot responses to investigate participant preferences and interactions. The platform provides real-time chat capabilities, template management, and seamless deployment options.

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Participant   │    │     Wizard      │    │   Flask API +   │
│   Frontend      │◄──►│   Frontend      │◄──►│   SocketIO      │
│ (Port 3000)     │    │ (Port 3001)     │    │ (Port 5000)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components

#### **Frontend Applications**
- **Participant Interface**: React app for study participants to chat with the "AI"
- **Wizard Interface**: React app for researchers to control responses and manage templates

#### **Backend Services**
- **Flask API**: RESTful endpoints for room management and template CRUD operations
- **Socket.IO Server**: Real-time bidirectional communication for chat and typing indicators
- **Template System**: Persistent storage and management of response templates organized by phases

#### **Key Features**
- **Environment Detection**: Automatically adapts URLs for development vs production
- **Template Management**: Categorized, reusable response templates with drag-and-drop reordering
- **Real-time Communication**: Live chat with typing indicators and message streaming
- **Room Management**: Unique session IDs for isolating participant-wizard pairs
- **Persistent Storage**: Template data survives deployments (with proper configuration)

## 🚀 Local Development

### Prerequisites
- **Node.js** 20+ and npm
- **Python** 3.11+ 
- **Virtual environment** (recommended)

### Setup

1. **Clone and setup environment**:
   ```bash
   git clone <your-repo>
   cd WebWOz
   
   # Create Python virtual environment
   python -m venv webwozenv
   source webwozenv/bin/activate  # On Windows: webwozenv\Scripts\activate
   
   # Install Python dependencies
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

2. **Install frontend dependencies**:
   ```bash
   # Participant frontend
   cd frontend-participant
   npm install
   cd ..
   
   # Wizard frontend  
   cd frontend-wizard
   npm install
   cd ..
   ```

### Running Locally

**Start all three services** (in separate terminals):

1. **Backend API + SocketIO**:
   ```bash
   cd backend
   python app.py
   # ✅ Running on http://localhost:5000
   ```

2. **Participant Interface**:
   ```bash
   cd frontend-participant  
   npm start
   # ✅ Available at http://localhost:3000
   ```

3. **Wizard Interface**:
   ```bash
   cd frontend-wizard
   npm start  
   # ✅ Available at http://localhost:3001
   ```

### Testing the Flow

1. **Open Wizard**: Navigate to `http://localhost:3001/wizard`
2. **Create Room**: App automatically generates a unique room ID
3. **Copy Participant Link**: Click "📋 Copy Link" button
4. **Open Participant**: Paste link in new browser tab/window
5. **Test Chat**: Send messages between interfaces
6. **Verify Templates**: Check that German templates load in wizard interface

## 🐳 Docker Deployment

### Build Configuration

The Docker setup uses a **multi-stage build** to create optimized production bundles:

```dockerfile
# Stage 1: Build React applications with namespace separation
FROM node:20 AS builder
# Builds with PUBLIC_URL="/static/p" and PUBLIC_URL="/static/w" 
# to prevent static asset conflicts

# Stage 2: Python runtime with static assets
FROM python:3.11-slim  
# Copies built assets to namespaced directories:
# - /app/backend/static/static/p/ (participant)
# - /app/backend/static/static/w/ (wizard)
```

### Local Docker Testing

```bash
# Build the image
docker build -t webwoz .

# Test locally (with required environment variables)
docker run -p 10000:10000 \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  -e NODE_ENV=production \
  webwoz

# Test the application
open http://localhost:10000/wizard
```

### Key Docker Features

- **Asset Namespacing**: Prevents JS/CSS conflicts between React bundles
- **Environment Detection**: Automatically uses same-origin URLs in production
- **Port Configuration**: Exposes port 10000 as required by Render
- **Security**: Uses environment variables for sensitive configuration

## ☁️ Render Deployment

### Environment Variables

Set these in your Render dashboard:

| Variable | Value | Purpose |
|----------|-------|---------|
| `SECRET_KEY` | `$(openssl rand -hex 32)` | Flask session security |
| `NODE_ENV` | `production` | Enables production optimizations |
| `TEMPLATE_DIR` | `/data` | Persistent storage location (optional) |
| `RENDER_EXTERNAL_URL` | `https://your-app.onrender.com` | CORS configuration |

### Persistent Storage (Optional)

For template persistence across deployments:

1. **Create Persistent Disk** in Render dashboard
2. **Mount Path**: `/data`  
3. **Set Environment**: `TEMPLATE_DIR=/data`
4. **Result**: Templates survive redeploys and container restarts

### Deployment URLs

After successful deployment:

- **Root**: `https://your-app.onrender.com` → redirects to wizard
- **Wizard Interface**: `https://your-app.onrender.com/wizard`
- **Participant Links**: Generated dynamically by "Copy Link" button

## 🔧 Environment Handling

### Development vs Production

The application automatically detects the environment and adapts behavior:

| Aspect | Development | Production |
|--------|-------------|------------|
| **Socket.IO** | `http://localhost:5000` | Same-origin (Render domain) |
| **API Calls** | `http://localhost:5000` | Same-origin (empty string) |
| **CORS** | Allow all origins | Locked to Render domain |
| **Static Assets** | React dev server | Flask serves namespaced bundles |
| **Participant Links** | `http://localhost:3000/chat/{id}` | `https://domain.com/chat/{id}` |

### Smart URL Generation

The "Copy Link" button intelligently generates participant URLs:

```javascript
// Development
if (window.location.hostname === 'localhost') {
  participantUrl = `http://localhost:3000/chat/${room}`;
} else {
  // Production  
  participantUrl = `${window.location.origin}/chat/${room}`;
}
```

## 📁 File Structure

```
WebWOz/
├── backend/                    # Flask API + SocketIO server
│   ├── app.py                 # Main application file
│   ├── requirements.txt       # Python dependencies
│   └── templates.json         # Template storage (dev)
├── frontend-participant/       # Participant chat interface
│   ├── src/app.js            # Main React component
│   ├── src/app.css           # Styling
│   └── package.json          # Dependencies
├── frontend-wizard/           # Wizard control panel
│   ├── src/
│   │   ├── app.js            # Main App component (refactored)
│   │   ├── app.css           # Styling
│   │   ├── TemplateManager.js # Template management
│   │   ├── components/       # Reusable UI components
│   │   │   ├── ChatArea.js   # Message display & export
│   │   │   ├── WizardControls.js # Setup mode & copy link
│   │   │   ├── PinnedTemplates.js # Pinned template management
│   │   │   ├── PhaseSelector.js # Phase navigation & editing
│   │   │   └── CustomResponse.js # Response textarea & send
│   │   └── hooks/            # Custom React hooks
│   │       ├── useSocket.js  # Socket connection management
│   │       └── useTemplateSync.js # Template persistence
│   └── package.json          # Dependencies
└── dockerfile                # Multi-stage production build
```

### Component Architecture

The wizard frontend has been refactored for better maintainability:

**Core Components:**
- `App.js` - Main application logic and state management (~150 lines, down from ~450)
- `ChatArea.js` - Message display, autoscroll, and chat export functionality
- `WizardControls.js` - Setup mode toggle and participant link generation
- `PinnedTemplates.js` - Drag-and-drop pinned template management
- `PhaseSelector.js` - Phase navigation with add/edit/delete capabilities
- `CustomResponse.js` - Response textarea with Enter-to-send functionality
- `TemplateManager.js` - Existing phase-based template management

**Custom Hooks:**
- `useSocket.js` - Manages SocketIO connections and real-time event handlers
- `useTemplateSync.js` - Handles automatic template synchronization with backend

This modular structure improves:
- **Code maintainability** - Each component has a single responsibility
- **Reusability** - Components can be easily reused or modified
- **Testing** - Individual components can be tested in isolation
- **Development velocity** - Easier to locate and modify specific functionality



