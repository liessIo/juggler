# backend/app/routers/config.py
"""Configuration management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models.config import SystemConfig
from app.models.user import User
from app.routers.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/config", tags=["configuration"])

class ConfigUpdate(BaseModel):
    groq_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

class ConfigStatusResponse(BaseModel):
    groq_api_key: Dict[str, Any]
    anthropic_api_key: Dict[str, Any]
    openai_api_key: Dict[str, Any]

@router.get("/", response_model=ConfigStatusResponse)
async def get_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ConfigStatusResponse:
    """Get current configuration status with masked values"""
    
    # Define the keys we're managing
    api_keys = ["groq_api_key", "anthropic_api_key", "openai_api_key"]
    result = {}
    
    for key_name in api_keys:
        # Try to get the config from database
        db_config = db.query(SystemConfig).filter(SystemConfig.key == key_name).first()
        
        if db_config and db_config.value:
            # Key exists and has value
            value = db_config.value
            # Mask the value for security
            if len(value) > 8:
                masked = value[:4] + "****" + value[-4:]
            else:
                masked = "****"
            
            result[key_name] = {
                "exists": True,
                "masked": masked
            }
        else:
            # Key doesn't exist or is empty
            result[key_name] = {
                "exists": False,
                "masked": ""
            }
    
    return ConfigStatusResponse(**result)

@router.post("/")
async def update_config(
    config: ConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update configuration - supports partial updates and deletion"""
    
    updates_made = []
    
    for key, value in config.dict().items():
        # Skip empty values (no change)
        if value == "":
            continue
            
        # Handle deletion with special value
        if value == "DELETE" or value == "delete":
            db_config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if db_config:
                db.delete(db_config)
                updates_made.append(f"Deleted {key}")
            continue
        
        # Update or create the config
        db_config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if db_config:
            db_config.value = value
            updates_made.append(f"Updated {key}")
        else:
            db_config = SystemConfig(key=key, value=value)
            db.add(db_config)
            updates_made.append(f"Created {key}")
    
    db.commit()
    
    if updates_made:
        return {"message": "Configuration updated", "changes": updates_made}
    else:
        return {"message": "No changes made"}

@router.delete("/{key_name}")
async def delete_config_key(
    key_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific configuration key"""
    
    # Validate key name
    valid_keys = ["groq_api_key", "anthropic_api_key", "openai_api_key"]
    if key_name not in valid_keys:
        raise HTTPException(status_code=400, detail="Invalid configuration key")
    
    db_config = db.query(SystemConfig).filter(SystemConfig.key == key_name).first()
    if db_config:
        db.delete(db_config)
        db.commit()
        return {"message": f"Configuration key '{key_name}' deleted"}
    else:
        return {"message": f"Configuration key '{key_name}' not found"}