# Temporäre test_main.py
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Juggler API Test")

@app.get("/")
async def root():
    return {"message": "Juggler API is running", "status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)