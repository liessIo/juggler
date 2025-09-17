# Juggler AI Chat System v2

<div align="center">
  <img src="https://img.shields.io/badge/Version-2.0.6-cyan?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Status-MVP-green?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</div>

<div align="center">
  <h3>🤹 A self-hosted multi-model AI chat system for small teams</h3>
  <p>Switch between AI models seamlessly while preserving context</p>
</div>

---

## ✨ Features

- 🔐 **Multi-User Support** - Separate chat histories per user
- 🤖 **Multiple AI Providers** - Ollama (local), Groq, Anthropic (coming soon)
- 🎨 **Modern Terminal UI** - "The Expanse" inspired cyberpunk interface
- 🔄 **Context Preservation** - Switch models without losing conversation context
- 🔑 **Secure API Key Management** - Encrypted storage with masked display
- 📊 **Token Tracking** - Monitor usage per conversation
- 🚀 **Fast & Responsive** - Built with FastAPI and Vue 3

## 🖼️ Screenshots

```
JUGGLER AI SYSTEM v2.0.6
================================
Initializing neural interface...
Loading language model...
System ready.

> Type command or query to begin_
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Ollama (for local models)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/liessIo/juggler.git
cd juggler
```

2. **Setup Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
```

3. **Setup Frontend**
```bash
cd frontend
npm install
```

4. **Run Ollama** (if using local models)
```bash
ollama serve
```

5. **Start the Application**

Backend:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm run dev
```

Access the application at `http://localhost:5173`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Security
SECRET_KEY=your-secret-key-change-this

# Database
DATABASE_URL=sqlite:///./data/juggler.db

# Ollama (Local AI)
OLLAMA_BASE_URL=http://localhost:11434

# Optional API Keys (configured via UI)
# GROQ_API_KEY=your-groq-key
# ANTHROPIC_API_KEY=your-anthropic-key
```

### API Keys Management

API keys can be configured through the web interface:
1. Login to the system
2. Click on `[CONFIG]` in the sidebar
3. Enter your API keys
4. Keys are stored securely and displayed masked

## 🏗️ Architecture

### Tech Stack

- **Backend**: FastAPI, SQLAlchemy, JWT Authentication
- **Frontend**: Vue 3, TypeScript, PrimeVue, Tailwind CSS 4
- **Database**: SQLite (PostgreSQL ready)
- **AI Providers**: Ollama, Groq, Anthropic (via adapters)

### Project Structure

```
juggler/
├── backend/
│   ├── app/
│   │   ├── models/      # Database models
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── providers/   # AI provider adapters
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── stores/      # Pinia stores
│   │   └── router/      # Vue router
│   └── package.json
└── README.md
```

## 🎯 Roadmap

### Current Status (v2.0.6)
- ✅ Core chat functionality with Ollama
- ✅ User authentication & authorization
- ✅ Configuration management UI
- ✅ Token tracking & usage statistics

### Upcoming Features
- 🔄 **Phase 3**: Persistent chat history in database
- 🔄 **Phase 4**: Additional providers (Groq, Anthropic)
- 📝 **Phase 6**: Advanced Context Engine with RAG

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed progress.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Ollama for local AI model support
- The FastAPI and Vue.js communities
- "The Expanse" for UI inspiration

## 📧 Contact

Stefan - [@liessIo](https://github.com/liessIo)

Project Link: [https://github.com/liessIo/juggler](https://github.com/liessIo/juggler)

---

<div align="center">
  <sub>Built with ❤️ for teams who juggle multiple AI models</sub>
</div>