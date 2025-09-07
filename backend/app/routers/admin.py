# backend/app/routers/admin.py

"""
Admin router - handles admin functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from app.models.auth_utils import get_current_user, TokenData

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(
    current_user: TokenData = Depends(get_current_user)
):
    """Get admin statistics - requires admin role"""
    # Simple admin check - in production, check user role in database
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "total_users": "N/A",  # Would query database
        "total_conversations": "N/A",
        "timestamp": datetime.utcnow().isoformat()
    }