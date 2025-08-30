from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import time

app = FastAPI(title="Juggler - Ollama Integration")

class ChatRequest(BaseModel):
    message: str
    model: str = "llama3:8b"

class ChatResponse(BaseModel):
    response: str
    model: str
    latency_ms: int

@app.get("/")
async def root():
    return {"message": "Juggler API with Ollama", "status": "running"}

@app.get("/models")
async def get_models():
    """Get available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json()
        return {
            "models": [m['name'] for m in models['models'] if 'embed' not in m['name']]  # Filter out embedding models
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {e}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with Ollama model"""
    start_time = time.time()
    
    try:
        payload = {
            "model": request.model,
            "messages": [{"role": "user", "content": request.message}],
            "stream": False
        }
        
        response = requests.post("http://localhost:11434/api/chat", json=payload)
        result = response.json()
        
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        
        return ChatResponse(
            response=result["message"]["content"],
            model=request.model,
            latency_ms=latency_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)