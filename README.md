# Juggler 🤹‍♂️

**Juggler** is a self-hosted, multi-model AI chat system that seamlessly switches between different AI providers without losing conversation context.

## Why Juggler?

Most AI chat apps lock you into a single provider and make you start over when you switch. Juggler lets you move fluidly between local and cloud AI models — without losing the thread. Whether you want the speed of Groq, the reasoning of Gemini, or the privacy of Ollama on your own machine, Juggler keeps the conversation going and your data under your control.

## Features

* **Provider Switching**: Switch between Ollama (local) and Groq/Gemini (cloud) mid-conversation
* **Context Preservation**: Full conversation history maintained across provider switches  
* **Token Monitoring**: Real-time latency and token usage tracking
* **Self-Hosted**: Run your own instance with complete data privacy
* **Modern UI**: Clean Vue.js interface with provider status indicators

## Current Architecture

* **Frontend**: Vue.js + TypeScript + Pinia (state management)
* **Backend**: FastAPI with async provider adapters
* **Database**: Per-user SQLite instances
* **Providers**: Ollama (local LLMs), Groq (cloud), Gemini (cloud)
* **Context Transfer**: Full conversation history preservation

## Quick Start

### Prerequisites

- Python 3.12+ 
- Node.js 18+
- Ollama (for local models)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Configuration

Create `.env` file in the root directory:

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
```

### Install Ollama (for local models)

```bash
# macOS
brew install ollama

# Start Ollama server
ollama serve

# Install a model (in another terminal)
ollama pull llama3:8b
```

### Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn multi_provider_api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access the application at: http://localhost:5173

## API Keys Setup

### Groq (Recommended - Fast & Cheap)
1. Visit https://console.groq.com/keys
2. Create account and generate API key
3. Add to `.env` as `GROQ_API_KEY`

### Google Gemini (Optional)
1. Visit https://makersuite.google.com/app/apikey
2. Create API key (requires billing setup)
3. Add to `.env` as `GEMINI_API_KEY`

## Usage

1. **Start a conversation** with any available provider
2. **Switch providers** mid-conversation using the dropdown
3. **Monitor performance** with latency and token counts
4. **Export conversations** for later reference

## Project Structure

```
juggler/
├── README.md
├── .env
├── requirements.txt
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── providers/
│   ├── multi_provider_api.py
│   └── config.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── stores/
│   │   └── types/
│   └── package.json
└── .gitignore
```

## Privacy by Design

* Zero data sharing between users
* Local conversation storage only
* API keys stored securely in environment variables
* No external services required for core functionality
* Conversation data remains on your machine

## Development

### Adding New Providers

1. Create provider adapter in `backend/providers/`
2. Add provider configuration to `config.py`
3. Update provider health checks in `multi_provider_api.py`
4. Add provider UI components in Vue frontend

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Backend Issues

**"Could not load AI providers"**
- Check if backend is running on port 8000
- Verify CORS settings in `multi_provider_api.py`
- Check API keys in `.env` file

**Ollama connection failed**
- Ensure Ollama server is running: `ollama serve`
- Check if models are installed: `ollama list`
- Verify OLLAMA_BASE_URL in `.env`

### Frontend Issues

**"Network Error"**
- Ensure backend is running
- Check browser console for CORS errors
- Verify frontend is accessing correct backend URL

## Roadmap

- [x] Multi-provider chat with context preservation
- [x] Ollama + Groq integration  
- [x] Vue.js frontend with provider switching
- [ ] OpenAI and Anthropic providers
- [ ] Advanced context summarization
- [ ] Docker deployment setup
- [ ] Conversation export/import
- [ ] User authentication system
- [ ] Group chat capabilities

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the API documentation at http://localhost:8000/docs

---

**Tagline**: "Keep all your models in the air."