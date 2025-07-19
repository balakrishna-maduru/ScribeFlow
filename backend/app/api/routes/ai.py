"""AI interaction endpoints."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.services.ai_service import ai_service
from app.models import User

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # "system", "user", "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat completion request model."""
    messages: List[ChatMessage]
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat completion response model."""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class ProvidersResponse(BaseModel):
    """Available providers response model."""
    providers: List[str]
    default_provider: str


class ModelsResponse(BaseModel):
    """Available models response model."""
    models: List[str]
    provider: str


@router.get("/providers", response_model=ProvidersResponse)
async def get_providers(
    current_user: User = Depends(get_current_user)
):
    """Get available AI providers."""
    try:
        providers = ai_service.get_available_providers()
        from app.core.config import get_settings
        settings = get_settings()
        
        return ProvidersResponse(
            providers=providers,
            default_provider=settings.default_ai_provider
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get providers: {str(e)}"
        )


@router.get("/providers/{provider}/models", response_model=ModelsResponse)
async def get_models(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Get available models for a provider."""
    try:
        models = ai_service.get_available_models(provider)
        if not models:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provider '{provider}' not found or no models available"
            )
        
        return ModelsResponse(
            models=models,
            provider=provider
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get models: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate chat completion."""
    try:
        # Convert Pydantic models to dict for AI service
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Use user's preferred provider if not specified
        provider = request.provider or current_user.preferred_ai_provider.value
        model = request.model or current_user.preferred_model
        
        if request.stream:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Streaming not supported in this endpoint. Use /ai/chat/stream"
            )
        
        response_content = await ai_service.chat_completion(
            messages=messages,
            provider=provider,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return ChatResponse(
            content=response_content,
            provider=provider,
            model=model
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_completion_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate streaming chat completion."""
    from fastapi.responses import StreamingResponse
    import json
    
    try:
        # Convert Pydantic models to dict for AI service
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Use user's preferred provider if not specified
        provider = request.provider or current_user.preferred_ai_provider.value
        model = request.model or current_user.preferred_model
        
        async def generate():
            try:
                async for chunk in ai_service.stream_completion(
                    messages=messages,
                    provider=provider,
                    model=model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    yield f"data: {json.dumps({'content': chunk, 'provider': provider, 'model': model})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


@router.post("/analyze-text")
async def analyze_text(
    text: str,
    analysis_type: str = "grammar",  # grammar, style, clarity, tone
    current_user: User = Depends(get_current_user)
):
    """Analyze text with AI."""
    try:
        # Create analysis prompt based on type
        analysis_prompts = {
            "grammar": "Please analyze the following text for grammatical errors and suggest improvements:",
            "style": "Please analyze the writing style of the following text and provide suggestions for improvement:",
            "clarity": "Please analyze the clarity of the following text and suggest ways to make it clearer:",
            "tone": "Please analyze the tone of the following text and describe it:"
        }
        
        if analysis_type not in analysis_prompts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid analysis type. Must be one of: {list(analysis_prompts.keys())}"
            )
        
        prompt = analysis_prompts[analysis_type]
        messages = [
            {"role": "system", "content": "You are a professional writing assistant."},
            {"role": "user", "content": f"{prompt}\n\n{text}"}
        ]
        
        provider = current_user.preferred_ai_provider.value
        model = current_user.preferred_model
        
        response = await ai_service.chat_completion(
            messages=messages,
            provider=provider,
            model=model
        )
        
        return {
            "analysis_type": analysis_type,
            "original_text": text,
            "analysis": response,
            "provider": provider,
            "model": model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
