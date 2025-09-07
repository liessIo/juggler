# Juggler 🤹‍♂️

**Juggler** is a self-hosted, multi-model AI chat system with sophisticated provider adapters that seamlessly switch between different AI providers while preserving conversation context through intelligent context packaging.

## Why Juggler?

Most AI chat apps lock you into a single provider and make you start over when you switch. Juggler uses advanced context transfer technology to move fluidly between local and cloud AI models without losing the thread. Whether you want the speed of Groq, the reasoning of Gemini, or the privacy of Ollama on your own machine, Juggler's context packages ensure perfect conversation continuity.

## Architecture Overview

Juggler uses a sophisticated **Provider Adapter Pattern** with intelligent context management:

### Backend Architecture
- **FastAPI Core**: Modular REST API with async provider adapters
- **Provider Adapters**: Standardized interface for AI providers (Ollama, Groq, Gemini)
- **Context Packages**: Smart context transfer system with token budget management
- **Canonical Message Format**: Unified message handling across all providers
- **SQLite Database**: User management, conversation storage, audit logging
- **Advanced Security**: JWT authentication, rate limiting, input sanitization

### Frontend Architecture  
- **Vue.js 3**: Composition API with TypeScript
- **Pinia State Management**: Reactive store for chat and authentication
- **Centralized Configuration**: Environment-based settings
- **Clean Component Structure**: Single-purpose components with clear separation

### Key Features
- **Intelligent Context Switching**: Preserves conversation context when switching providers
- **Token Budget Management**: Automatically optimizes context within model limits
- **Real-time Provider Health**: Dynamic model loading and status monitoring
- **Advanced Authentication**: Secure user management with session handling
- **Production Ready**: Comprehensive error handling, logging, and monitoring

## Current Implementation Status

### ✅ Completed Features
- **Clean Frontend Architecture**: Reduced from 2000+ to 800 lines
- **Modular Backend**: Complete provider adapter system
- **Three Provider Adapters**: Ollama, Groq, Gemini with context packages
- **Authentication System**: JWT-based with refresh tokens
- **Database Integration**: SQLite with comprehensive models
- **Configuration Management**: Centralized config with environment variables
- **API Endpoints**: Full REST API with proper error handling

### 📁 Current File Structure

```
juggler/
├── README.md
├── .env
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── config.py                  # Application settings
│   │   ├── database.py                # SQLite database and models
│   │   ├── middleware.py              # CORS, rate limiting, security
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── auth_utils.py          # JWT authentication utilities
│   │   │   ├── chat_models.py         # Pydantic models for chat
│   │   │   └── security_models.py     # SQLAlchemy database models
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Base provider interface
│   │   │   ├── ollama_adapter.py      # Ollama provider adapter
│   │   │   ├── groq_adapter.py        # Groq provider adapter
│   │   │   └── gemini_adapter.py      # Gemini provider adapter
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # Authentication endpoints
│   │   │   ├── chat.py                # Chat endpoints
│   │   │   ├── providers.py           # Provider management
│   │   │   └── admin.py               # Admin endpoints
│   │   ├── security/
│   │   │   ├── auth.py                # Advanced security features
│   │   │   ├── deps.py                # Security dependencies
│   │   │   └── incident_response.py   # Security incident handling
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── chat_service.py        # Chat orchestration service
│   │       └── provider_service.py    # Provider management service
│   └── core/
│       └── config.py                  # Advanced configuration system
├── frontend/
│   ├── src/
│   │   ├── App.vue                    # Main application component
│   │   ├── main.ts                    # Vue application entry point
│   │   ├── components/
│   │   │   └── ChatInterface.vue      # Complete chat interface
│   │   ├── config/
│   │   │   └── index.ts               # Frontend configuration
│   │   ├── services/
│   │   │   └── auth.service.ts        # Authentication service
│   │   ├── stores/
│   │   │   └── chatStore.ts           # Chat state management
│   │   ├── types/
│   │   │   └── chat.ts                # TypeScript definitions
│   │   └── views/
│   │       └── LoginView.vue          # Login interface
│   ├── package.json
│   └── vite.config.ts
└── data/                              # SQLite database files
```

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** 
- **Ollama** (for local models)

## Installation & Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

### 3. Environment Configuration

Create `.env` file in the project root:

```env
# AI Provider API Keys
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here

# Ollama Configuration  
OLLAMA_BASE_URL=http://localhost:11434

# Application Settings
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Security (generate secure keys for production)
SECRET_KEY=your-secret-key-here
```

### 4. Install Ollama (Local AI Models)

```bash
# macOS
brew install ollama

# Start Ollama server
ollama serve

# Install a model (separate terminal)
ollama pull llama3.2:3b
```

## Running the Application

### Start Backend
```bash
cd backend
source venv/bin/activate
python -m app.main
```

### Start Frontend  
```bash
cd frontend
npm run dev
```

**Access**: http://localhost:5173

## API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/api/docs
- **Alternative Docs**: http://localhost:8000/api/redoc

### Key Endpoints

- `GET /api/health` - Health check
- `GET /api/providers/status` - Provider availability and models
- `POST /api/auth/login` - User authentication
- `POST /api/chat/send` - Send message to AI provider
- `POST /api/providers/{provider}/refresh` - Refresh provider models

## Provider Setup

### Groq (Recommended - Fast & Free Tier)
1. Visit: https://console.groq.com/keys
2. Create account and generate API key
3. Add to `.env`: `GROQ_API_KEY=your_key`

### Google Gemini  
1. Visit: https://makersuite.google.com/app/apikey
2. Create API key (billing required)
3. Add to `.env`: `GEMINI_API_KEY=your_key`

### Ollama (Local)
- Automatically detected when server is running
- Models: `ollama pull llama3.2:3b`

## Advanced Features

### Context Package System
Juggler's sophisticated context management:

1. **Token Budget Allocation**:
   - 10% system instructions
   - 20% structured facts  
   - 30% conversation summary
   - 30% recent messages
   - 10% current query

2. **Smart Context Transfer**:
   - Preserves conversation meaning across providers
   - Optimizes for each model's context window
   - Maintains structured facts and entities

3. **Provider-Specific Optimization**:
   - Ollama: Local model optimization
   - Groq: Fast inference optimization  
   - Gemini: Large context utilization

### Security Features

- **JWT Authentication** with refresh tokens
- **Rate Limiting** per user and endpoint
- **Input Sanitization** for XSS prevention
- **Audit Logging** for security events
- **Session Management** with automatic cleanup

## Usage Guide

### Basic Chat
1. **Login** with test credentials (testuser/Test123!)
2. **Select Provider** from dropdown
3. **Choose Model** for that provider
4. **Start Chatting** - context preserved across switches

### Provider Switching
1. **Mid-conversation switching** maintains context
2. **Automatic model selection** for new providers
3. **Context optimization** for target model's capabilities

### Model Management
- **Refresh Models**: Update available models per provider
- **Health Monitoring**: Real-time provider status
- **Performance Metrics**: Latency and token usage tracking

## Development

### Adding New Providers

1. **Create Adapter** (`backend/app/providers/new_provider_adapter.py`):
```python
# backend/app/providers/new_provider_adapter.py
from .base import BaseProvider

class NewProviderAdapter(BaseProvider):
    async def initialize(self) -> bool:
        # Implementation
    
    async def send_message(self, context_package, model_id, **kwargs):
        # Implementation
```

2. **Register in Services** (`backend/app/services/provider_service.py`)
3. **Update Frontend** provider dropdown

### Code Quality

- **TypeScript**: Strict typing throughout frontend
- **Python Type Hints**: Full backend type coverage
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured logging for debugging

## Testing

### Backend Health Check
```bash
curl http://localhost:8000/api/health
```

### Provider Status
```bash
curl http://localhost:8000/api/providers/status
```

### Frontend Build
```bash
cd frontend
npm run build
```

## Troubleshooting

### Backend Issues

**Import Errors**
- Run from `backend/` directory: `python -m app.main`
- Check virtual environment activation

**Provider Connection Failed**  
- Verify API keys in `.env`
- Check Ollama server: `ollama serve`
- Review provider adapter logs

**Database Errors**
- Initialize database: `python app/database.py`
- Check file permissions in `data/` directory

### Frontend Issues

**Build Errors**
- Update dependencies: `npm install`
- Check TypeScript errors: `npm run type-check`

**API Connection Failed**
- Verify backend is running on port 8000
- Check CORS settings in `app/middleware.py`
- Review browser console for errors

## Production Deployment

### Security Checklist
- [ ] Generate secure `SECRET_KEY`
- [ ] Set `DEBUG=false`
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure rate limiting
- [ ] Review audit logs

### Performance Optimization
- [ ] Enable database connection pooling
- [ ] Configure provider request caching
- [ ] Set up reverse proxy (nginx)
- [ ] Monitor resource usage
- [ ] Optimize context package sizes

## Roadmap

### Phase 1 (Current) ✅
- [x] Core provider adapter system
- [x] Context package implementation
- [x] Ollama, Groq, Gemini integration
- [x] Authentication and security
- [x] Clean frontend architecture

### Phase 2 (Next)
- [ ] OpenAI and Anthropic providers  
- [ ] Advanced context summarization with AI
- [ ] Docker deployment configuration
- [ ] Conversation export/import
- [ ] Enhanced UI with provider comparison

### Phase 3 (Future)
- [ ] Multi-user collaboration features
- [ ] Plugin system for custom providers
- [ ] Advanced analytics and insights
- [ ] Mobile application
- [ ] Enterprise features

## Contributing

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/new-feature`
3. **Develop** following existing patterns
4. **Test** thoroughly with all providers
5. **Submit** pull request with detailed description

## License

MIT License - see LICENSE file for details

## Support & Community

- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: In-code documentation and API docs
- **Health Endpoint**: http://localhost:8000/api/health for status

---

**Current Status**: Production-ready multi-provider AI chat with advanced context management
**Last Updated**: September 2025