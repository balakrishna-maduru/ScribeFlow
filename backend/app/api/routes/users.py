"""User management endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, AIProvider

router = APIRouter()


class UserUpdate(BaseModel):
    """User update model."""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    preferred_ai_provider: Optional[AIProvider] = None
    preferred_model: Optional[str] = None


class UserProfile(BaseModel):
    """User profile response model."""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    avatar_url: Optional[str] = None
    preferred_ai_provider: AIProvider
    preferred_model: str
    is_active: bool
    is_verified: bool
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return current_user


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    try:
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        await db.commit()
        await db.refresh(current_user)
        
        return current_user
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics."""
    from sqlalchemy import select, func
    from app.models import Document, AISession
    
    try:
        # Get document stats
        doc_count_result = await db.execute(
            select(func.count(Document.id)).where(Document.owner_id == current_user.id)
        )
        total_documents = doc_count_result.scalar()
        
        # Get total word count
        word_count_result = await db.execute(
            select(func.sum(Document.word_count)).where(Document.owner_id == current_user.id)
        )
        total_words = word_count_result.scalar() or 0
        
        # Get AI session count
        ai_sessions_result = await db.execute(
            select(func.count(AISession.id)).where(AISession.user_id == current_user.id)
        )
        total_ai_sessions = ai_sessions_result.scalar()
        
        # Get published documents count
        published_docs_result = await db.execute(
            select(func.count(Document.id)).where(
                Document.owner_id == current_user.id,
                Document.status == "published"
            )
        )
        published_documents = published_docs_result.scalar()
        
        return {
            "total_documents": total_documents,
            "published_documents": published_documents,
            "draft_documents": total_documents - published_documents,
            "total_words": total_words,
            "total_ai_sessions": total_ai_sessions,
            "preferred_provider": current_user.preferred_ai_provider.value,
            "preferred_model": current_user.preferred_model
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )


@router.delete("/account")
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user account and all associated data."""
    try:
        # This is a simplified version. In production, you'd want to:
        # 1. Soft delete or archive data
        # 2. Handle related data properly
        # 3. Send confirmation emails
        # 4. Implement a grace period
        
        await db.delete(current_user)
        await db.commit()
        
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
