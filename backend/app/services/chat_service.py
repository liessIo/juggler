# backend/app/services/chat_service.py

"""
Chat service for handling AI provider interactions
"""

import logging
from fastapi import HTTPException

import ollama
from groq import Groq
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling chat interactions with AI providers"""
    
    def __init__(self):
        self.groq_client = None
    
    def initialize(self):
        """Initialize chat service clients"""
        try:
            if settings.GROQ_API_KEY:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        except Exception as e:
            logger.warning(f"Could not initialize Groq client: {e}")
        
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
    
    async def get_response(self, provider: str, model: str | None, prompt: str) -> str:
        """Get response from specified provider"""
        if provider == "ollama":
            return await self._get_ollama_response(prompt, model or "llama3:8b")
        elif provider == "groq":
            return await self._get_groq_response(prompt, model or "llama-3.1-8b-instant")
        elif provider == "gemini":
            return await self._get_gemini_response(prompt, model or "gemini-pro")
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")
    
    async def _get_ollama_response(self, prompt: str, model: str) -> str:
        """Get response from Ollama"""
        try:
            client = ollama.Client(host=settings.OLLAMA_BASE_URL)
            response = client.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")

    async def _get_groq_response(self, prompt: str, model: str) -> str:
        """Get response from Groq"""
        if not self.groq_client:
            raise HTTPException(status_code=500, detail="Groq API key not configured")
        
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
            )
            
            response = chat_completion.choices[0].message.content if chat_completion.choices else None
            
            if not response or response.strip() == "":
                logger.warning(f"Empty response from Groq for model {model}")
                return f"Groq returned empty response. Model: {model} might be having issues. Please try another model."
            
            return response
            
        except Exception as e:
            logger.error(f"Groq error with model {model}: {e}")
            raise HTTPException(status_code=500, detail=f"Groq error: {str(e)}")

    async def _get_gemini_response(self, prompt: str, model_name: str) -> str:
        """Get response from Gemini"""
        if not settings.GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")
        
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

# Global chat service instance
chat_service = ChatService()
chat_service.initialize()