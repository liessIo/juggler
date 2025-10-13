# backend/app/routers/config.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.system_config import SystemConfig, ProviderConfigSchema, ProviderConfigRequest, ProviderConfigResponse
from app.models.user import User
from app.services.auth_service import get_current_user
from app.models.model_selection import ModelSelection
from app.services.provider_service import get_provider_service
from sqlalchemy.orm.attributes import flag_modified
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def mask_api_key(key: str) -> str:
    """Mask API key for display"""
    if not key or len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def get_provider_config(db: Session, provider: str) -> Dict:
    """Get provider configuration with backwards compatibility"""
    # Try new schema first
    config = SystemConfig.get(db, provider)
    if config and isinstance(config, dict):
        return config
    
    # Backwards compatibility: old format was just the API key string
    old_key = SystemConfig.get(db, f"{provider}_api_key")
    if old_key:
        # Migrate to new format
        new_config = {
            "api_key": old_key,
            "active": True,
            "last_used": None
        }
        SystemConfig.set(db, provider, new_config)
        SystemConfig.delete(db, f"{provider}_api_key")
        return new_config
    
    # Ollama special case (no API key needed)
    if provider == "ollama":
        return {"api_key": None, "active": True, "last_used": None}
    
    return None


def set_provider_config(db: Session, provider: str, config: Dict):
    """Set provider configuration"""
    SystemConfig.set(db, provider, config)


@router.get("/")
async def get_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, ProviderConfigResponse]:
    """
    Get all provider configurations with masked API keys
    """
    providers = ["groq", "anthropic", "openai", "ollama"]
    result = {}
    
    for provider in providers:
        config = get_provider_config(db, provider)
        
        if config:
            result[provider] = ProviderConfigResponse(
                exists=bool(config.get("api_key")),
                active=config.get("active", True),
                masked=mask_api_key(config.get("api_key")) if config.get("api_key") else None,
                last_used=config.get("last_used")
            )
        else:
            result[provider] = ProviderConfigResponse(
                exists=False,
                active=False,
                masked=None,
                last_used=None
            )
    
    return result


@router.post("/")
async def update_config(
    request: ProviderConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, List[str]]:
    """
    Update provider configurations
    Supports both new schema (ProviderConfigSchema) and old format (simple strings)
    """
    updated = []
    deleted = []
    
    # Handle new format (preferred)
    for provider in ["groq", "anthropic", "openai", "ollama"]:
        new_config = getattr(request, provider, None)
        
        if new_config:
            # Get existing config
            existing = get_provider_config(db, provider)
            if not existing:
                existing = {"api_key": None, "active": True, "last_used": None}
            
            # Update fields
            if new_config.api_key is not None:
                existing["api_key"] = new_config.api_key
            if new_config.active is not None:
                existing["active"] = new_config.active
            
            set_provider_config(db, provider, existing)
            updated.append(provider)
    
    # Backwards compatibility: Handle old format (simple API key strings)
    old_format_keys = {
        "groq_api_key": "groq",
        "anthropic_api_key": "anthropic",
        "openai_api_key": "openai"
    }
    
    for field, provider in old_format_keys.items():
        value = getattr(request, field, None)
        if value:
            existing = get_provider_config(db, provider)
            if not existing:
                existing = {"api_key": None, "active": True, "last_used": None}
            existing["api_key"] = value
            set_provider_config(db, provider, existing)
            updated.append(provider)
    
    # Handle delete flags (backwards compatibility)
    delete_flags = {
        "DELETE_groq_api_key": "groq",
        "DELETE_anthropic_api_key": "anthropic",
        "DELETE_openai_api_key": "openai"
    }
    
    for field, provider in delete_flags.items():
        if getattr(request, field, False):
            if SystemConfig.delete(db, provider):
                deleted.append(provider)
    
    return {
        "updated": updated,
        "deleted": deleted
    }


@router.get("/models/enabled")
async def get_enabled_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all enabled models across all ACTIVE providers
    This is FAST - reads only from DB, no API calls
    """
    providers = ["ollama", "groq", "anthropic"]
    result = {}
    
    for provider in providers:
        # Check if provider is active
        config = get_provider_config(db, provider)
        if not config or not config.get("active", True):
            continue  # Skip inactive providers
        
        enabled = ModelSelection.get_enabled_models(db, provider)
        if enabled:
            result[provider] = {"models": enabled}
    
    return {"providers": result}


@router.get("/models/{provider}")
async def get_provider_models(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available models for a provider"""
    # Check if provider is active
    config = get_provider_config(db, provider)
    if not config or not config.get("active", True):
        return {
            "models": {},
            "needs_refresh": False,
            "provider_inactive": True
        }
    
    models = ModelSelection.get_all_models(db, provider)
    needs_refresh = ModelSelection.needs_refresh(db, provider)
    
    if not models:
        return {
            "models": {},
            "needs_refresh": True
        }
    
    return {
        "models": models,
        "needs_refresh": needs_refresh
    }


@router.post("/models/{provider}/refresh")
async def refresh_provider_models(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh model list from provider API"""
    # Check if provider is active
    config = get_provider_config(db, provider)
    if not config or not config.get("active", True):
        raise HTTPException(status_code=400, detail="Provider is not active")
    
    try:
        # Get provider service instance
        provider_service = get_provider_service()
        
        # Get models from provider
        if provider not in provider_service.providers:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not initialized")
        
        adapter = provider_service.providers[provider]
        models = await adapter.list_models()
        
        # Store in database
        model_dict = []
        for model in models:
            model_dict.append({
                "id": model["id"],
                "name": model.get("name", model["id"]),
                "description": model.get("description", "")
            })
        
        ModelSelection.update_available_models(db, provider, model_dict)
        
        return {"count": len(models)}
        
    except Exception as e:
        logger.error(f"Error refreshing models for {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{provider}/selection")
async def update_model_selection(
    provider: str,
    enabled_models: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update which models are enabled for a provider"""
    # Check if provider is active
    config = get_provider_config(db, provider)
    if not config or not config.get("active", True):
        raise HTTPException(status_code=400, detail="Provider is not active")
    
    # Use bulk_update_selection method
    success = ModelSelection.bulk_update_selection(db, provider, enabled_models)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"No models found for {provider}")
    
    # Get count of enabled models
    enabled = ModelSelection.get_enabled_models(db, provider)
    
    return {"enabled_count": len(enabled)}