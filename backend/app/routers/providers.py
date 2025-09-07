# backend/app/routers/providers.py

"""
Providers router - handles provider and model management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.auth_utils import get_current_user, TokenData
from app.services.provider_service import provider_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/status")
@limiter.limit("60/minute")
async def get_providers_status(request: Request):
    """Get status of all providers with dynamic models - PUBLIC endpoint"""
    try:
        providers_status = await provider_service.get_all_providers()
        
        # Convert to API format
        result = {}
        for name, status in providers_status.items():
            result[name] = {
                "available": status.available,
                "models": status.models,
                "last_refresh": status.last_refresh.isoformat(),
                "error": status.error if status.error else None
            }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider status: {str(e)}")

@router.post("/{provider_name}/refresh")
@limiter.limit("10/minute")
async def refresh_provider(
    request: Request,
    provider_name: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Refresh models for a specific provider"""
    if provider_name not in ["ollama", "groq", "gemini"]:
        raise HTTPException(status_code=400, detail="Invalid provider name")
    
    try:
        status = await provider_service.refresh_provider(provider_name)
        
        return {
            "provider": provider_name,
            "models": status.models,
            "refreshed_at": status.last_refresh.isoformat(),
            "count": len(status.models),
            "success": status.available,
            "error": status.error if status.error else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh {provider_name} models: {str(e)}")

@router.post("/refresh-all")
@limiter.limit("5/minute")
async def refresh_all_providers(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Refresh models for all providers"""
    try:
        results = await provider_service.refresh_all_providers()
        
        response = {
            "refreshed_at": datetime.now().isoformat(),
            "providers": {}
        }
        
        for provider, status in results.items():
            response["providers"][provider] = {
                "success": status.available,
                "models": status.models,
                "count": len(status.models),
                "error": status.error if status.error else None
            }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh providers: {str(e)}")