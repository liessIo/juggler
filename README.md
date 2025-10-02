# Juggler AI Chat System v2

<div align="center">
  <img src="https://img.shields.io/badge/Version-2.1.0-cyan?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Status-Active%20Development-green?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</div>

<div align="center">
  <h3>🤹 A self-hosted multi-model AI chat system for small teams</h3>
  <p>Switch between AI models seamlessly while preserving full conversation context</p>
</div>

---

## ✨ Features

- 🔐 **Multi-User Support** - Separate chat histories per user with JWT authentication
- 🤖 **Multiple AI Providers** - Ollama (local), Groq, Anthropic Claude
- 🧠 **Context Preservation** - Full conversation history maintained when switching models
- 💾 **Persistent Storage** - Conversations and messages stored in SQLite database
- 🎨 **Modern Terminal UI** - "The Expanse" inspired cyberpunk interface
- ⚡ **Optimized Performance** - Sub-100ms model loading with intelligent caching
- 🔑 **Secure Configuration** - API keys stored in database with masked display
- 📊 **Token Tracking** - Monitor usage per conversation and provider
- 🎯 **Model Selection** - Choose which models to display per provider

## 🖼️ Screenshots
JUGGLER AI SYSTEM v2.1.0
Initializing neural interface...
Loading language models...
3 providers available
12 models loaded
System ready.

Type command or query to begin_


## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Ollama (optional, for local models)
- API Keys for Groq and/or Anthropic (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/liessIo/juggler.git
cd juggler

Setup Backend

bashcd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

Configure Environment

bashcp .env.example .env
# Edit .env with your SECRET_KEY

Setup Frontend

bashcd frontend
npm install

Optional: Run Ollama (for local models)

bashollama serve
ollama pull phi3:medium

Start the Application

Backend:
bashcd backend
uvicorn app.main:app --reload
Frontend (new terminal):
bashcd frontend
npm run dev
Access the application at http://localhost:5173
🔧 Configuration
Environment Variables
Create a .env file in the backend directory:
env# Required
SECRET_KEY=your-secret-key-change-this-in-production

# Database
DATABASE_URL=sqlite:///./data/juggler.db

# Optional: Ollama (if running locally)
OLLAMA_BASE_URL=http://localhost:11434
API Keys Management
Configure provider API keys through the web interface:

Register/Login to the system
Navigate to [CONFIG] in the sidebar
Switch to "API KEYS" tab
Enter your API keys for Groq and/or Anthropic
Switch to "MODEL SELECTION" tab to choose which models to display

Note: All users share the same API keys (single-tenant design).
Model Selection
After configuring API keys:

Go to Config → Model Selection
Select a provider (Ollama, Groq, Anthropic)
Click "REFRESH MODELS" to load available models
Check the models you want to use
Click "SAVE SELECTION"

Only selected models will appear in the chat interface.
🏗️ Architecture
Tech Stack
Backend:

FastAPI - Async web framework
SQLAlchemy - ORM with SQLite (PostgreSQL ready)
JWT - Authentication
Provider Adapters - Unified interface for AI services

Frontend:

Vue 3 + TypeScript
Pinia - State management
PrimeVue - UI components
Tailwind CSS 4 - Styling
Vite - Build tool

Project Structure
juggler/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   │   ├── user.py      # User authentication
│   │   │   ├── chat.py      # Conversations & messages
│   │   │   ├── system_config.py  # API keys
│   │   │   └── model_selection.py  # Model preferences
│   │   ├── routers/         # API endpoints
│   │   │   ├── auth.py      # Authentication
│   │   │   ├── config.py    # Configuration
│   │   │   └── chat.py      # (in main.py)
│   │   ├── services/        # Business logic
│   │   │   ├── auth_service.py
│   │   │   └── provider_service.py
│   │   ├── providers/       # AI provider adapters
│   │   │   ├── base.py
│   │   │   ├── ollama_adapter.py
│   │   │   ├── groq_adapter.py
│   │   │   └── anthropic_adapter.py
│   │   ├── settings.py      # App configuration
│   │   ├── database.py      # Database setup
│   │   └── main.py          # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginForm.vue
│   │   │   └── ConfigView.vue
│   │   ├── stores/
│   │   │   └── auth.ts
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── ChatView.vue     # Main chat interface
│   │   └── App.vue
│   └── package.json
└── README.md
🎯 Implementation Status
✅ Completed (v2.1.0)
Phase A - Context Transfer:

Full conversation history sent to providers
Seamless model switching within conversations
Context maintained across sessions

Phase B - Database Persistence (Backend):

SQLite database with SQLAlchemy ORM
User authentication with JWT
Conversations and messages persistence
Provider and model tracking per message
Token usage tracking

Configuration & UX:

Secure API key management with masked display
Model selection UI with per-provider configuration
Performance optimization (6s → <100ms model loading)
Auto-focus input after message send
Remember last-used model per provider
Provider filtering (only show configured providers)

🔄 In Progress
Phase B - Database Persistence (Frontend):

Load conversation history from database
Switch between previous conversations
Display conversation list in sidebar

📋 Planned
Phase C - Advanced Context Engine:

PostgreSQL with pgvector for semantic search
Embedding pipeline for all messages
RAG (Retrieval Augmented Generation)
Long-term context memory
Intelligent context assembly

See the technical design document for Phase C details.
🐛 Known Issues

Frontend conversation history still uses in-memory storage
Conversation list sidebar needs DB integration
Long conversations (100+ messages) may experience latency

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
Development Setup

Fork the repository
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

Code Style

Backend: Follow PEP 8
Frontend: ESLint + TypeScript strict mode
Commit messages: Conventional Commits format

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.
🙏 Acknowledgments

Ollama for local AI model support
Groq for blazing-fast cloud inference
Anthropic for Claude models
The FastAPI and Vue.js communities
"The Expanse" for UI inspiration

📧 Contact
Stefan - @liessIo
Project Link: https://github.com/liessIo/juggler