# WebWOz – One‑Click Wizard‑of‑Oz Chat

**A production-ready research platform for simulating AI chatbots with human wizards and automated rule-based bots.**

WebWOz enables researchers to conduct Wizard-of-Oz studies where human operators (wizards) simulate AI chatbot responses to investigate participant preferences and interactions. The platform provides real-time chat capabilities, template management, **automated rule-based bot integration**, and seamless deployment options.

## ✨ Key Features

- **🧙‍♂️ Wizard-of-Oz Studies**: Human operators control chat responses in real-time
- **🤖 Automated Rule-Based Bot**: Pre-configured bot for structured data collection (e.g., accident reports)
- **📝 Template Management**: Organized, reusable response templates with categories and phases
- **⚡ Real-time Communication**: Live chat with typing indicators and instant message delivery
- **🎯 Session Management**: Unique room IDs for isolating participant-wizard pairs
- **📊 Data Export**: Export chat logs and form data for analysis
- **🔄 Hybrid Mode**: Seamlessly switch between manual wizard control and automated bot responses

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Participant   │    │     Wizard      │    │   Flask API +   │
│   Frontend      │◄──►│   Frontend      │◄──►│   SocketIO      │
│ (Port 3000)     │    │ (Port 3001)     │    │ (Port 5000)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │  Rule-Based Bot │
                                               │   Integration   │
                                               │ (accident_report)│
                                               └─────────────────┘
```

### Components

#### **Frontend Applications**
- **Participant Interface**: React app for study participants to chat with the "AI"
- **Wizard Interface**: React app for researchers to control responses, manage templates, and control bots

#### **Backend Services**
- **Flask API**: RESTful endpoints for room management, template CRUD, and bot control
- **Socket.IO Server**: Real-time bidirectional communication for chat and typing indicators
- **Template System**: Persistent storage and management of response templates organized by phases
- **Bot Integration**: Automated rule-based conversation system with form validation

#### **Rule-Based Bot System**
- **LangGraph Workflow**: State machine for structured conversation flows
- **Form Validation**: Real-time input validation with error handling and retry logic
- **Progress Tracking**: Visual progress indicators and completion status
- **Data Collection**: Structured data extraction with JSON export
- **Hybrid Control**: Seamless handoff between automated bot and human wizard

#### **Key Features**
- **Environment Detection**: Automatically adapts URLs for development vs production
- **Template Management**: Categorized, reusable response templates with drag-and-drop reordering
- **Real-time Communication**: Live chat with typing indicators and message streaming
- **Room Management**: Unique session IDs for isolating participant-wizard pairs
- **Persistent Storage**: Template data and bot sessions survive deployments
- **Bot Control**: Start/stop automated conversations with real-time status updates

## 🤖 Rule-Based Bot Integration

### Overview

WebWOz includes a sophisticated rule-based bot system designed for structured data collection. The bot uses **LangGraph** to manage conversation flows and can handle complex form-filling scenarios with validation, error handling, and progress tracking.

### Bot Features

#### **🎯 Structured Conversations**
- **State Management**: Uses LangGraph to maintain conversation state across interactions
- **Form Workflow**: Guides participants through predefined question sequences
- **Dynamic Routing**: Conditional logic for follow-up questions and branching paths
- **Error Recovery**: Automatic retry mechanisms with helpful error messages

#### **� Data Collection**
- **Input Validation**: Real-time validation of user responses (dates, times, choices, etc.)
- **Multiple Question Types**: Support for text, numbers, dates, single/multiple choice, and complex groups
- **Progress Tracking**: Visual progress indicators showing completion status
- **Data Export**: Structured JSON output with form metadata

#### **🔄 Wizard Integration**
- **Hybrid Mode**: Seamless switching between automated bot and human wizard control
- **Real-time Status**: Live bot status updates in the wizard interface
- **Manual Override**: Wizards can stop the bot and take control at any time
- **Session Persistence**: Bot state is maintained across page refreshes

### Bot Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Rule-Based Bot System                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  LangGraph  │    │ Validator   │    │ Question    │     │
│  │  Workflow   │◄──►│  Engine     │◄──►│ Definitions │     │
│  │             │    │             │    │   (JSON)    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   State     │    │   Form      │    │   Progress  │     │
│  │ Management  │    │ Data Store  │    │  Tracker    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Use Cases

#### **📊 Research Data Collection**
- **Accident Reports**: Pre-configured for collecting detailed accident information
- **Survey Forms**: Structured questionnaires with validation
- **User Studies**: Consistent data collection across participants
- **A/B Testing**: Compare human wizard vs automated bot performance

#### **🔬 Conversation Analysis**
- **Response Times**: Measure time between bot questions and user responses
- **Error Patterns**: Track validation failures and common mistakes
- **Completion Rates**: Monitor form abandonment and success rates
- **User Behavior**: Analyze interaction patterns with structured vs free-form chat

### Bot Configuration

#### **Question Definition Format**
```json
{
  "title": "Accident Report Form",
  "questions": [
    {
      "id": "date_of_accident",
      "question": "What is the date of the accident?",
      "type": "date",
      "required": true,
      "validation": {
        "min_date": "2020-01-01",
        "max_date": "2025-12-31"
      }
    },
    {
      "id": "description",
      "question": "Please describe what happened:",
      "type": "multiline_text",
      "required": true
    },
    {
      "id": "severity",
      "question": "How would you rate the severity?",
      "type": "single_choice",
      "choices": ["Minor", "Moderate", "Severe", "Critical"],
      "required": true
    }
  ]
}
```

#### **Supported Question Types**
- **`text`**: Single-line text input with optional length validation
- **`multiline_text`**: Multi-line text areas for longer responses
- **`date`**: Date picker with validation and format checking
- **`time`**: Time input with 24-hour format support
- **`number`**: Numeric input with min/max validation
- **`boolean`**: Yes/No questions with follow-up logic
- **`single_choice`**: Radio button selections
- **`multiple_choice`**: Checkbox selections with min/max limits
- **`group`**: Nested question groups for complex data structures

### Bot API Endpoints

#### **Status Management**
```bash
# Get bot status for a room
GET /api/bot/{room_id}/status
# Returns: {"active": false, "available": true, "progress": "Not started"}

# Start bot session
POST /api/bot/{room_id}/start
# Returns: {"status": "success", "message": "Bot activated successfully"}

# Stop bot session  
POST /api/bot/{room_id}/stop
# Returns: {"status": "success", "message": "Bot deactivated"}
```

#### **Real-time Events**
```javascript
// Bot status changes
socket.on('bot_status_changed', (data) => {
  console.log(`Bot ${data.active ? 'activated' : 'deactivated'} in room ${data.room}`);
});

// Bot messages (same as wizard/participant messages)
socket.on('new_message', (message) => {
  if (message.sender === 'bot') {
    // Handle bot response
  }
});
```

### Bot Usage Workflow

#### **1. Wizard Setup**
1. **Create Room**: Wizard opens the interface and gets a unique room ID
2. **Share Link**: Participant receives chat link and joins the room
3. **Bot Control**: Wizard sees bot controls in the interface

#### **2. Bot Activation**
1. **Start Bot**: Wizard clicks "Start Accident Report Bot"
2. **Initial Message**: Bot sends welcome message and first question
3. **Status Update**: Wizard interface shows "Bot Active" status

#### **3. Conversation Flow**
1. **Question Display**: Bot presents structured questions to participant
2. **Input Validation**: Real-time validation with helpful error messages
3. **Progress Tracking**: Visual progress indicator updates with each completed question
4. **Adaptive Logic**: Bot follows conditional paths based on responses

#### **4. Completion or Override**
1. **Form Completion**: Bot provides summary and deactivates automatically
2. **Manual Override**: Wizard can stop bot and take control at any time
3. **Data Export**: Structured data available for download and analysis


(Workflow visualization)[]
### Development and Customization

#### **Adding New Question Types**
```python
# In validator.py
def _parse_custom_type(reply: str, q_def: Dict[str, Any]) -> Any:
    """Add validation logic for custom question type"""
    # Custom validation logic here
    return processed_value

# In bot_naive.py  
def handle_custom_question(self, state: FormState) -> FormState:
    """Add custom question handling logic"""
    # Custom handling logic here
    return updated_state
```

#### **Custom Workflow Logic**
```python
# Modify routing logic in bot_naive.py
def route_after_validation(self, state: FormState) -> Literal[...]:
    """Custom routing based on responses"""
    # Add conditional logic for custom workflows
    return next_node
```

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
   
   # Install Python dependencies (includes bot dependencies)
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
5. **Test Manual Chat**: Send messages between interfaces to verify basic functionality
6. **Test Bot Integration**: 
   - In wizard interface, look for "🤖 Rule-Based Bot" section
   - Click "Start Accident Report Bot" to activate automated conversation
   - In participant interface, respond to bot questions
   - Verify validation, progress tracking, and form completion
   - Test manual override by clicking "Stop Bot" in wizard interface
7. **Verify Templates**: Check that templates load properly in wizard interface

### Bot Testing Checklist

- [ ] Bot status shows as "Available" in wizard interface
- [ ] Bot can be started and shows activation message
- [ ] Participant receives structured questions from bot
- [ ] Input validation works (try invalid dates, choices, etc.)
- [ ] Progress indicator updates with each completed question
- [ ] Bot can be stopped manually by wizard
- [ ] Form completion generates summary message
- [ ] Chat log export includes both manual and bot messages

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
│   ├── bot_integration.py     # Rule-based bot integration
│   ├── requirements.txt       # Python dependencies (includes bot libs)
│   ├── templates.json         # Template storage (dev)
│   └── accident_report/       # Bot system components
│       ├── questionnaire/
│       │   └── questions.json # Bot question definitions
│       └── rule_based/
│           ├── bot_naive.py   # LangGraph workflow implementation
│           └── validator.py   # Input validation engine
├── frontend-participant/       # Participant chat interface
│   ├── src/app.js            # Main React component
│   ├── src/app.css           # Styling
│   └── package.json          # Dependencies
├── frontend-wizard/           # Wizard control panel
│   ├── src/
│   │   ├── app.js            # Main App component (refactored)
│   │   ├── app.css           # Styling (includes bot controls)
│   │   ├── TemplateManager.js # Template management
│   │   ├── components/       # Reusable UI components
│   │   │   ├── BotControls.js # Bot start/stop/status interface
│   │   │   ├── ChatArea.js   # Message display & export
│   │   │   ├── WizardControls.js # Setup mode & copy link
│   │   │   ├── PinnedTemplates.js # Pinned template management
│   │   │   ├── PhaseSelector.js # Phase navigation & editing
│   │   │   └── CustomResponse.js # Response textarea & send
│   │   └── hooks/            # Custom React hooks
│   │       ├── useSocket.js  # Socket connection management
│   │       └── useTemplateSync.js # Template persistence
└── dockerfile                # Multi-stage production build (includes bot)
```
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
- `BotControls.js` - **NEW**: Bot start/stop controls with real-time status updates
- `PinnedTemplates.js` - Drag-and-drop pinned template management
- `PhaseSelector.js` - Phase navigation with add/edit/delete capabilities
- `CustomResponse.js` - Response textarea with Enter-to-send functionality
- `TemplateManager.js` - Existing phase-based template management

**Custom Hooks:**
- `useSocket.js` - Manages SocketIO connections and real-time event handlers
- `useTemplateSync.js` - Handles automatic template synchronization with backend

**Bot Integration:**
- `bot_integration.py` - **NEW**: Core bot session management and API integration
- `BotControls.js` - **NEW**: React component for bot control interface
- `accident_report/` - **NEW**: Complete rule-based bot system with LangGraph workflows

This modular structure improves:
- **Code maintainability** - Each component has a single responsibility
- **Reusability** - Components can be easily reused or modified
- **Testing** - Individual components can be tested in isolation
- **Development velocity** - Easier to locate and modify specific functionality
- **Bot Integration** - Clean separation between manual wizard and automated bot functionality




###Neo4J helper:
Start Neo4j	sudo neo4j start
Access UI	Go to http://localhost:7474
Run script	cypher-shell -u neo4j -p your_pw < script.cypher
Visualize graph	MATCH (n) RETURN n in the browser
Stop Neo4j	sudo neo4j stop

