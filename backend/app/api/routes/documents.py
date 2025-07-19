"""Document management endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, Document, DocumentStatus
import json

router = APIRouter()


class DocumentCreate(BaseModel):
    """Document creation model."""
    title: str
    content: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []


class DocumentUpdate(BaseModel):
    """Document update model."""
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[DocumentStatus] = None


class DocumentResponse(BaseModel):
    """Document response model."""
    id: int
    title: str
    content: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    status: DocumentStatus
    word_count: int
    created_at: str
    updated_at: str
    published_at: Optional[str] = None
    published_url: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.post("/", response_model=DocumentResponse)
async def create_document(
    document_data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new document."""
    try:
        # Calculate word count
        word_count = len(document_data.content.split()) if document_data.content else 0
        
        document = Document(
            title=document_data.title,
            content=document_data.content,
            description=document_data.description,
            tags=document_data.tags,
            word_count=word_count,
            owner_id=current_user.id
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return document
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[DocumentStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's documents with optional filtering."""
    try:
        query = select(Document).where(Document.owner_id == current_user.id)
        
        # Apply filters
        if status_filter:
            query = query.where(Document.status == status_filter)
        
        if search:
            query = query.where(
                Document.title.ilike(f"%{search}%") |
                Document.content.ilike(f"%{search}%") |
                Document.description.ilike(f"%{search}%")
            )
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(Document.updated_at.desc())
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        return documents
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document."""
    try:
        result = await db.execute(
            select(Document).where(
                and_(Document.id == document_id, Document.owner_id == current_user.id)
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a document."""
    try:
        result = await db.execute(
            select(Document).where(
                and_(Document.id == document_id, Document.owner_id == current_user.id)
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Update fields
        update_data = document_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)
        
        # Recalculate word count if content changed
        if document_data.content is not None:
            document.word_count = len(document_data.content.split()) if document_data.content else 0
        
        await db.commit()
        await db.refresh(document)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document."""
    try:
        result = await db.execute(
            select(Document).where(
                and_(Document.id == document_id, Document.owner_id == current_user.id)
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        await db.delete(document)
        await db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document file."""
    try:
        # Validate file type
        allowed_types = [
            "text/plain",
            "text/markdown",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Read file content
        content = await file.read()
        
        # Process based on file type
        if file.content_type == "text/plain" or file.content_type == "text/markdown":
            text_content = content.decode("utf-8")
        else:
            # For PDF and DOCX, we'd need additional processing
            # For now, store as binary and mark for processing
            text_content = f"[Binary file: {file.filename}]"
        
        # Create document
        document_title = title or file.filename or "Uploaded Document"
        word_count = len(text_content.split()) if text_content else 0
        
        document = Document(
            title=document_title,
            content=text_content,
            word_count=word_count,
            owner_id=current_user.id,
            file_path=file.filename,
            file_type=file.content_type,
            file_size=len(content)
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return {
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "filename": file.filename,
            "size": len(content),
            "type": file.content_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post("/{document_id}/publish")
async def publish_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Publish a document."""
    try:
        result = await db.execute(
            select(Document).where(
                and_(Document.id == document_id, Document.owner_id == current_user.id)
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Update document status
        document.status = DocumentStatus.PUBLISHED
        from datetime import datetime
        document.published_at = datetime.utcnow()
        
        # Generate a simple published URL (in real app, this would be more sophisticated)
        document.published_url = f"/published/{document.id}"
        
        await db.commit()
        await db.refresh(document)
        
        return {
            "message": "Document published successfully",
            "published_url": document.published_url,
            "published_at": document.published_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish document: {str(e)}"
        )
