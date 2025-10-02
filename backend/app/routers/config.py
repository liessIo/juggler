# backend/app/routers/config.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.system_config import SystemConfig
from app.models.model_selection import ModelSelection
from app.services.provider_service import get_provider_service
from app.routers.auth import get_current_user

router = APIRouter()

# Request/Response Models
class ConfigUpdate(BaseModel):
    groq_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    DELETE_groq_api_key: Optional[bool] = False
    DELETE_anthropic_api_key: Optional[bool] = False
    DELETE_openai_api_key: Optional[bool] = False

class ModelSelectionUpdate(BaseModel):
    provider: str
    enabled_models: List[str]

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool

# Existing endpoints
@router.get("/")
async def get_config(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Get configuration with status info"""
    config_keys = [
        "groq_api_key",
        "anthropic_api_key", 
        "openai_api_key"
    ]
    
    result = {}
    for key in config_keys:
        config = SystemConfig.get(db, key)
        if config and config.get("value"):
            # Mask the actual value for security
            result[key] = {
                "exists": True,
                "masked": "*" * 8 + config["value"][-4:] if len(config["value"]) > 4 else "****"
            }
        else:
            result[key] = {
                "exists": False,
                "masked": ""
            }
    
    return result

@router.post("/")
async def update_config(
    config_update: ConfigUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Update configuration (set or delete API keys)"""
    updates = []
    deletions = []
    
    # Handle updates
    if config_update.groq_api_key:
        SystemConfig.set(db, "groq_api_key", config_update.groq_api_key)
        updates.append("groq_api_key")
    
    if config_update.anthropic_api_key:
        SystemConfig.set(db, "anthropic_api_key", config_update.anthropic_api_key)
        updates.append("anthropic_api_key")
    
    if config_update.openai_api_key:
        SystemConfig.set(db, "openai_api_key", config_update.openai_api_key)
        updates.append("openai_api_key")
    
    # Handle deletions
    if config_update.DELETE_groq_api_key:
        SystemConfig.delete(db, "groq_api_key")
        deletions.append("groq_api_key")
    
    if config_update.DELETE_anthropic_api_key:
        SystemConfig.delete(db, "anthropic_api_key")
        deletions.append("anthropic_api_key")
    
    if config_update.DELETE_openai_api_key:
        SystemConfig.delete(db, "openai_api_key")
        deletions.append("openai_api_key")
    
    # Reinitialize provider service if keys changed
    if updates or deletions:
        provider_service = get_provider_service()
        provider_service.refresh_providers()
    
    return {
        "message": "Configuration updated",
        "updated": updates,
        "deleted": deletions
    }

@router.delete("/{key}")
async def delete_config_key(
    key: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Delete a specific configuration key"""
    allowed_keys = ["groq_api_key", "anthropic_api_key", "openai_api_key"]
    
    if key not in allowed_keys:
        raise HTTPException(status_code=400, detail=f"Key '{key}' cannot be deleted")
    
    SystemConfig.delete(db, key)
    
    # Reinitialize provider service
    provider_service = get_provider_service()
    provider_service.refresh_providers()
    
    return {"message": f"Configuration key '{key}' deleted"}

# NEW: Model Management Endpoints
# CRITICAL: /models/enabled MUST come BEFORE /models/{provider}!

@router.get("/models/enabled")
async def get_enabled_models(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Get all enabled models for the chat interface - OPTIMIZED FOR SPEED"""
    
    # PERFORMANCE FIX: Nicht provider_service.get_available_providers() aufrufen!
    # Das würde alle Provider-APIs checken (6+ Sekunden)
    # Stattdessen: Nur aus DB lesen (< 10ms)
    
    provider_names = ["ollama", "groq", "anthropic"]
    
    result = {}
    for provider_name in provider_names:
        # Hole enabled models aus DB
        enabled = ModelSelection.get_enabled_models(db, provider_name)
        
        # Provider ist "available" wenn Models konfiguriert sind
        # Echten API-Status prüfen wir nur beim tatsächlichen Chat-Send
        result[provider_name] = {
            "available": len(enabled) > 0,
            "models": enabled
        }
    
    return {"providers": result}

@router.get("/models/{provider}")
async def get_provider_models(
    provider: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Get all available models for a provider with selection status"""
    
    # Check if refresh needed
    needs_refresh = ModelSelection.needs_refresh(db, provider)
    
    if needs_refresh:
        # Fetch fresh models from provider
        provider_service = get_provider_service()
        provider_obj = provider_service.get_provider(provider)
        
        if not provider_obj:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not available")
        
        try:
            # Get models from provider API
            model_list = await provider_obj.list_models()
            
            # Transform to our format (ohne hardcoded Beschreibungen)
            models = []
            for model_id in model_list:
                models.append({
                    "id": model_id,
                    "name": model_id,
                    "description": ""  # Leer - User kann später editieren
                })
            
            # Update in database
            ModelSelection.update_available_models(db, provider, models)
            
        except Exception as e:
            # If refresh fails, use cached data
            pass
    
    # Get current selection
    all_models = ModelSelection.get_all_models(db, provider)
    
    return {
        "provider": provider,
        "models": all_models,
        "last_fetched": ModelSelection.needs_refresh(db, provider),
        "needs_refresh": needs_refresh
    }

@router.post("/models/{provider}/refresh")
async def refresh_provider_models(
    provider: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Force refresh models for a provider"""
    
    provider_service = get_provider_service()
    provider_obj = provider_service.get_provider(provider)
    
    if not provider_obj:
        raise HTTPException(status_code=404, detail=f"Provider {provider} not available")
    
    try:
        # Get fresh models from provider
        model_list = await provider_obj.list_models()
        
        # Transform to our format
        models = []
        for model_id in model_list:
            models.append({
                "id": model_id,
                "name": model_id,
                "description": ""  # Leer - User kann editieren
            })
        
        # Update in database
        ModelSelection.update_available_models(db, provider, models)
        
        return {
            "message": "Models refreshed successfully",
            "count": len(models)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh models: {str(e)}")

@router.post("/models/{provider}/selection")
async def update_model_selection(
    provider: str,
    selection: ModelSelectionUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Update which models are enabled for a provider"""
    
    success = ModelSelection.bulk_update_selection(
        db, 
        provider, 
        selection.enabled_models
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update selection")
    
    return {
        "message": "Model selection updated",
        "provider": provider,
        "enabled_count": len(selection.enabled_models)
    }