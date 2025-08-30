import httpx
import asyncio
import json

async def test_ollama():
    client = httpx.AsyncClient()
    
    # Test 1: Ist Ollama erreichbar?
    try:
        response = await client.get("http://localhost:11434/api/tags")
        print("✅ Ollama is running")
        print(f"Available models: {response.json()}")
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        await client.aclose()
        return
    
    # Test 2: Chat with model
    try:
        payload = {
            "model": "llama3:8b",
            "messages": [{"role": "user", "content": "Hello! Say hi back."}],
            "stream": False
        }
        
        response = await client.post("http://localhost:11434/api/chat", json=payload)
        result = response.json()
        
        print("Full response:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Chat failed: {e}")
    
    await client.aclose()

# Run the test
asyncio.run(test_ollama())