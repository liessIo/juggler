# Juggler - Multi-Model AI Chat System

A sophisticated self-hosted AI chat system with encrypted API key management and seamless provider switching between Ollama, Groq, and Gemini models.

## 🔐 Security-First Architecture

Juggler features a comprehensive encryption system that securely stores user API keys using PyNaCl encryption with per-user key derivation. No more plain-text API keys in environment variables.

## ✨ Key Features

- **Multi-Provider Support**: Seamlessly switch between Ollama (local), Groq (cloud), and Gemini models
- **Encrypted API Key Storage**: Industry-standard PyNaCl encryption with user-specific key derivation
- **Per-User Isolation**: Each user maintains their own encrypted credentials and chat history
- **Context-Aware Switching**: Sophisticated context package system preserves conversation context across providers
- **Token Budget Management**: Intelligent context allocation with configurable token budgeting
- **Real-Time Chat**: FastAPI-based backend with async processing
- **JWT Authentication**: Secure user authentication with refresh token support
- **Audit Logging**: Comprehensive security event tracking

## 🏗️ Architecture

### Backend (FastAPI)
- **Provider Adapter Pattern**: Clean abstraction layer for different AI providers
- **Encrypted Key Management**: PyNaCl-based encryption with PBKDF2 key derivation
- **SQLAlchemy ORM**: Production-ready database models with proper relationships
- **JWT Authentication**: Secure session management with refresh tokens
- **Rate Limiting**: Per-user request throttling and security controls

### Frontend (Vue.js 3)
- **TypeScript**: Type-safe frontend development
- **Pinia State Management**: Reactive state handling
- **Component Architecture**: Modular, reusable components
- **Real-time Updates**: Live chat interface with provider switching

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Ollama (optional, for local models)

### Backend Setup

```bash
# Clone repository
git clone <repository-url>
cd juggler/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (see Configuration section)

# Initialize database
python -m app.database

# Start backend
python -m app.main
```

### Frontend Setup

```bash
cd juggler/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Security (CHANGE THESE FOR PRODUCTION!)
DEBUG=true
SECRET_KEY=change-me                    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JUGGLER_API_TOKEN=change-me             # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# AI Provider API Keys (Optional - users can add their own)
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=your_gemini_key_here

# Ollama (Local Models)
OLLAMA_BASE_URL=http://localhost:11434

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/juggler.db

# Application
FRONTEND_ORIGIN=http://localhost:5173
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_PERIOD=60
```

### Production Deployment Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong, randomly generated value
- [ ] Change `JUGGLER_API_TOKEN` to a strong, randomly generated value  
- [ ] Set `DEBUG=false`
- [ ] Update `DATABASE_URL` to use PostgreSQL for production
- [ ] Set appropriate `FRONTEND_ORIGIN` for your domain
- [ ] Configure `REDIS_URL` if using caching
- [ ] Review all API keys and tokens for production values

## 🔐 API Key Management

### For Users

Users can securely store their own API keys through the web interface or API:

```bash
# Login and get JWT token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Store encrypted API key
curl -X POST "http://localhost:8000/api/chat/api-keys/groq" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "gsk_your_key", "key_name": "My Groq Key"}'

# List stored keys (metadata only)
curl -X GET "http://localhost:8000/api/chat/api-keys" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Security Features

- **PyNaCl Encryption**: Military-grade encryption for API key storage
- **User-Specific Keys**: Each user gets unique encryption keys derived from their user ID
- **Salt-Based Derivation**: PBKDF2 with 100,000 iterations for key strengthening
- **Metadata Only**: List operations never expose actual API keys
- **Audit Logging**: All key operations are logged for security monitoring

## 🤖 Supported Providers

### Ollama (Local Models)
- **Setup**: Install Ollama and download models
- **No API Key Required**: Uses local HTTP connection
- **Models**: llama3, mistral, codellama, and more
- **Benefits**: Complete privacy, no external API costs

### Groq (Cloud - Fast Inference)
- **Setup**: Get API key from [console.groq.com](https://console.groq.com)
- **Models**: Llama 3.1 (8B, 70B), Mixtral 8x7B, Gemma 2 9B
- **Benefits**: Extremely fast inference, cost-effective

### Gemini (Google AI)
- **Setup**: Get API key from [Google AI Studio](https://aistudio.google.com)
- **Models**: Gemini Pro, Gemini Pro Vision
- **Benefits**: Large context windows, multimodal capabilities

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Token refresh

### Chat System
- `POST /api/chat/send` - Send message to AI provider
- `GET /api/chat/conversations` - List user conversations
- `GET /api/chat/conversation/{id}` - Get specific conversation

### Provider Management
- `GET /api/chat/providers` - List available providers for user
- `POST /api/chat/providers/{provider}/refresh` - Refresh provider models

### API Key Management
- `POST /api/chat/api-keys/{provider}` - Store encrypted API key
- `GET /api/chat/api-keys` - List stored keys (metadata only)
- `DELETE /api/chat/api-keys/{provider}` - Delete API key

### System
- `GET /api/health` - Health check
- `GET /api/providers/status` - System provider status

## 🧪 Testing

### Test the Encryption System

```bash
cd backend

# Test encryption functionality
python test_key_manager.py

# Test with different users
python -c "
from app.models.security_models import store_encrypted_api_key, get_decrypted_api_key
from app.security.key_manager import initialize_key_manager
from app.database import get_db_context

initialize_key_manager('test-secret-123')

with get_db_context() as db:
    key = store_encrypted_api_key('user123', 'groq', 'gsk_test123', 'Test Key')
    db.add(key)
    db.commit()

decrypted = get_decrypted_api_key('user123', 'groq')
print(f'Success: {decrypted == \"gsk_test123\"}')
"
```

### Test the Chat System

```bash
# Test with Ollama (no API key required)
curl -X POST "http://localhost:8000/api/chat/send" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, world!",
    "provider": "ollama",
    "model": "llama3:8b"
  }'
```

## 🔧 Development

### Project Structure

```
juggler/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models and schemas
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── providers/       # AI provider adapters
│   │   ├── security/        # Authentication and encryption
│   │   └── main.py          # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Vue components
│   │   ├── stores/          # Pinia state management
│   │   ├── services/        # API services
│   │   └── views/           # Page components
│   └── package.json
└── .env                     # Environment configuration
```

### Adding New Providers

1. Create adapter in `backend/app/providers/`
2. Implement `BaseProvider` interface
3. Add provider initialization in `provider_service.py`
4. Update frontend to support new provider

### Database Migrations

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## 🐛 Known Issues

### Groq Provider Health Check
- **Issue**: Groq provider shows as "down" despite valid API keys
- **Status**: Under investigation
- **Workaround**: Use Ollama or Gemini providers
- **Debug**: Check backend logs for Groq initialization errors

## 🛡️ Security

### Encryption Implementation
- **Algorithm**: PyNaCl (NaCl/libsodium) secretbox
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Salt**: 16-byte cryptographically secure random salt per key
- **Authentication**: Built-in authentication with NaCl secretbox

### Security Best Practices
- API keys never stored in plain text
- User-specific encryption keys prevent cross-user access
- JWT tokens for secure session management
- Rate limiting and input sanitization
- Comprehensive audit logging
- Environment-based security controls

## 📈 Roadmap

### Immediate Priorities
- [ ] Fix Groq provider health check issue
- [ ] Complete frontend integration with encrypted key management
- [ ] Add Gemini provider testing

### Short Term
- [ ] Configuration system consolidation
- [ ] Enhanced error handling and monitoring
- [ ] User interface for API key management
- [ ] Provider switching UI improvements

### Long Term
- [ ] PostgreSQL migration for production
- [ ] Redis caching layer
- [ ] Advanced context package optimization
- [ ] Multi-tenant support
- [ ] Analytics and insights dashboard

## 📝 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📞 Support

[Add support information here]

---

**Security Note**: This system implements strong encryption for API key storage. Always use strong, randomly generated secrets in production and never commit real API keys to version control.