# Juggler AI Chat System v3.1.0

<div align="center">
  <img src="https://img.shields.io/badge/Version-3.1.0-cyan?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-green?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Phase-C%20Beta-yellow?style=for-the-badge" alt="Phase">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</div>

<div align="center">
  <h3>Juggler - Self-hosted Multi-Model AI Chat with Context Engine</h3>
  <p>Switch between AI models seamlessly while preserving full conversation context. Compare responses. Branch conversations.</p>
</div>

---

## Features

- **Multi-Provider Support** - Ollama (local), Groq, Anthropic Claude
- **Context Preservation** - Full conversation history maintained when switching models
- **Conversation Branching** - Generate variants and explore alternative response paths
- **Persistent Storage** - PostgreSQL with pgvector for semantic search
- **Message Variants** - Generate alternatives and select preferred responses
- **Context Snapshots** - Reproducible responses with stored context
- **Token Tracking** - Monitor usage per conversation and provider
- **Multi-User** - Separate chat histories with JWT authentication
- **Modern UI** - The Expanse inspired sci-fi design with Tailwind CSS
- **Performance** - Sub-100ms model loading with intelligent caching

## What's New in v3.1.0

- **Variant Selection Flow**: Create new messages instead of updating originals
- **Conversation Branching**: Both conversation paths remain visible (active/inactive)
- **Alternatives Table**: 3-column grid UI for comparing responses
- **Context Engine (Phase C)**: PostgreSQL + pgvector + message embeddings
- **Reproducibility**: Context snapshots for exact response replication

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15 with pgvector extension
- Ollama (optional, for local models)

### Installation

**1. Clone Repository**

```bash
git clone https://github.com/liessIo/juggler.git
cd juggler
```

**2. Backend Setup**

```bash
cd backend

# Virtual Environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  (Windows)

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with DATABASE_URL and API keys

# Database
alembic upgrade head

# Start
uvicorn app.main:app --reload
```

**3. Frontend Setup**

```bash
cd frontend

# Dependencies
npm install

# Environment
cp .env.example .env

# Start
npm run dev
```

**4. Optional: Ollama**

```bash
ollama serve
ollama pull phi3:medium
```

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Configuration

### Environment Variables (.env)

```env
# Backend
DATABASE_URL=postgresql://user:password@localhost/juggler_v3
ENABLE_CONTEXT_ENGINE=true
SECRET_KEY=your-secret-key-change-in-production

# Providers
GROQ_API_KEY=your-groq-key
ANTHROPIC_API_KEY=your-anthropic-key

# CORS
CORS_ORIGINS=["http://localhost:5173"]
```

### API Key Management

1. Register/Login to the system
2. Navigate to Configuration (⚙️)
3. Go to "API KEYS" tab
4. Enter your API keys for providers
5. Toggle providers Active/Inactive as needed
6. Go to "MODEL SELECTION" tab
7. Select which models to display in chat

## Architecture

### Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- PostgreSQL 15 + pgvector (vector search)
- SQLAlchemy 2.0 (ORM)
- JWT Authentication
- sentence-transformers (embeddings)

**Frontend:**
- Vue 3 + Composition API + TypeScript
- Pinia (state management)
- Tailwind CSS v4 (styling)
- Vite (build tool)
- Axios (HTTP client)

### Database Schema (Key Tables)

```
conversations
  - id, user_id, title, created_at, total_tokens

messages
  - id, conversation_id, role, content
  - provider, model, tokens_input, tokens_output

message_variants
  - id, original_message_id, content, provider, model
  - is_canonical, context_hash

message_embeddings (Phase C)
  - id, message_id, embedding (Vector 384)

context_snapshots (Phase C)
  - id, generating_message_id, context_hash
  - snapshot_data, snapshot_metadata
```

### Variant Selection Flow

```
User clicks "Select" on Alternative
       ↓
POST /api/chat/variants/select
       ↓
Backend: Create NEW message (don't update original)
       ↓
Response includes deactivated_message_id
       ↓
Frontend: Mark old message as is_active=false
Frontend: Add new message as is_active=true
       ↓
Result: Both messages visible (active/inactive)
        Conversation branching preserved
```

## Implementation Status

### Phase A: Context Transfer ✅ COMPLETE

- Full conversation history sent to providers
- Seamless model switching
- Provider info stored per message
- Context maintained across sessions

### Phase B: Database Persistence ✅ COMPLETE

- PostgreSQL with message relationships
- Conversation history loading
- Multi-user support with JWT
- Token tracking per message
- Recent conversations sidebar

### Phase C: Context Engine ✅ IN PROGRESS

- **Implemented**: PostgreSQL migration, pgvector, message embeddings, context snapshots
- **Implemented**: Message variants, variant selection, conversation branching
- **In Progress**: Semantic search, RAG, intelligent context assembly
- **Planned**: Streaming responses, advanced context orchestration

## Project Structure

```
juggler/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── chat.py
│   │   │   ├── message_variants.py
│   │   │   ├── context_engine.py
│   │   │   └── schemas.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   └── config.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── provider_service.py
│   │   │   └── context_orchestrator.py
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   ├── ollama_adapter.py
│   │   │   ├── groq_adapter.py
│   │   │   └── anthropic_adapter.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── settings.py
│   │   └── __init__.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginForm.vue
│   │   │   ├── ChatView.vue
│   │   │   └── ConfigView.vue
│   │   ├── stores/
│   │   │   └── auth.ts
│   │   ├── utils/
│   │   │   └── axios.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
├── README.md
├── CONTEXT_TRANSFER_COMPLETE.md
└── .gitignore
```

## API Endpoints

### Chat

```
POST /api/chat/send
  Send message and get response

POST /api/chat/rerun
  Generate variant with different model

POST /api/chat/variants/select
  Select variant and create new message

GET /api/chat/conversations
  List user conversations

GET /api/chat/conversations/{id}/messages
  Get messages for conversation

GET /api/chat/messages/{message_id}/context
  Get context used for message
```

### Configuration

```
GET /api/config/models/enabled
  Get enabled models per provider

POST /api/config/api-keys
  Update API keys

GET /api/providers/health
  Get provider health status
```

### Authentication

```
POST /api/auth/register
  Create user account

POST /api/auth/login
  Login and get JWT token

POST /api/auth/logout
  Logout
```

## Backlog (Priority)

**High**:
- [ ] Auto-embedding on message save
- [ ] Semantic context retrieval (pgvector search)
- [ ] Streaming responses (WebSocket)
- [ ] Circuit breaker integration

**Medium**:
- [ ] Multi-user conversation sharing
- [ ] Advanced context reranking
- [ ] Analytics dashboard
- [ ] Message search/filtering

**Low**:
- [ ] Voice input/output
- [ ] Plugin system
- [ ] Advanced RAG features

## Known Issues

- Embeddings not auto-generated on message save (manual phase)
- Context assembly is static (no semantic search yet)
- No streaming responses (full response wait required)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open Pull Request

**Code Style**:
- Backend: PEP 8
- Frontend: ESLint + TypeScript strict mode
- Commits: Conventional Commits

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Ollama for local AI support
- Groq for fast cloud inference
- Anthropic for Claude models
- FastAPI and Vue.js communities
- The Expanse for design inspiration

## Contact

Stefan - [@liessIo](https://github.com/liessIo)  
Project: [github.com/liessIo/juggler](https://github.com/liessIo/juggler)

---

## Documentation

- [CONTEXT_TRANSFER_COMPLETE.md](./CONTEXT_TRANSFER_COMPLETE.md) - Full architecture review and technical design
- [QUICKSTART.md](./QUICKSTART.md) - Detailed setup guide