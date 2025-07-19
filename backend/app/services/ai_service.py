"""AI service for managing multiple AI providers."""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
from enum import Enum

import openai
import anthropic
import google.generativeai as genai
import cohere

from app.core.config import get_settings, get_ai_config


class AIProvider(Enum):
    """AI provider enumeration."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"


class BaseAIClient(ABC):
    """Abstract base class for AI clients."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate chat completion."""
        pass
    
    @abstractmethod
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion."""
        pass


class OpenAIClient(BaseAIClient):
    """OpenAI client implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Generate chat completion using OpenAI."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using OpenAI."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")


class AnthropicClient(BaseAIClient):
    """Anthropic client implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key, model)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Generate chat completion using Anthropic."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using Anthropic."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                stream=True,
                **kwargs
            )
            async for chunk in response:
                if chunk.type == "content_block_delta":
                    yield chunk.delta.text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")


class GoogleAIClient(BaseAIClient):
    """Google AI client implementation."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Generate chat completion using Google AI."""
        try:
            # Convert messages to Google AI format
            prompt = self._convert_messages_to_prompt(messages)
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = await self.client.generate_content_async(
                prompt,
                generation_config=generation_config,
                **kwargs
            )
            return response.text
        except Exception as e:
            raise Exception(f"Google AI API error: {str(e)}")
    
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using Google AI."""
        try:
            prompt = self._convert_messages_to_prompt(messages)
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = await self.client.generate_content_async(
                prompt,
                generation_config=generation_config,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Google AI API error: {str(e)}")
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to Google AI prompt format."""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n\n".join(prompt_parts)


class CohereClient(BaseAIClient):
    """Cohere client implementation."""
    
    def __init__(self, api_key: str, model: str = "command"):
        super().__init__(api_key, model)
        self.client = cohere.AsyncClient(api_key)
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """Generate chat completion using Cohere."""
        try:
            # Convert messages to Cohere format
            prompt = self._convert_messages_to_prompt(messages)
            
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.generations[0].text
        except Exception as e:
            raise Exception(f"Cohere API error: {str(e)}")
    
    async def stream_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using Cohere."""
        try:
            prompt = self._convert_messages_to_prompt(messages)
            
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Cohere API error: {str(e)}")
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert messages to Cohere prompt format."""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n\n".join(prompt_parts)


class AIService:
    """Main AI service for managing multiple providers."""
    
    def __init__(self):
        self.settings = get_settings()
        self.ai_config = get_ai_config()
        self._clients: Dict[str, BaseAIClient] = {}
    
    def _get_client(self, provider: str, model: Optional[str] = None) -> BaseAIClient:
        """Get or create AI client for provider."""
        cache_key = f"{provider}:{model or 'default'}"
        
        if cache_key not in self._clients:
            config = self.ai_config.get(provider)
            if not config or not config.get("api_key"):
                raise ValueError(f"API key not configured for provider: {provider}")
            
            api_key = config["api_key"]
            model = model or config["models"][0]
            
            if provider == AIProvider.OPENAI.value:
                self._clients[cache_key] = OpenAIClient(api_key, model)
            elif provider == AIProvider.ANTHROPIC.value:
                self._clients[cache_key] = AnthropicClient(api_key, model)
            elif provider == AIProvider.GOOGLE.value:
                self._clients[cache_key] = GoogleAIClient(api_key, model)
            elif provider == AIProvider.COHERE.value:
                self._clients[cache_key] = CohereClient(api_key, model)
            else:
                raise ValueError(f"Unsupported AI provider: {provider}")
        
        return self._clients[cache_key]
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: str = None,
        **kwargs
    ) -> str:
        """Generate chat completion using specified provider."""
        provider = provider or self.settings.default_ai_provider
        client = self._get_client(provider, model)
        return await client.chat_completion(messages, **kwargs)
    
    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: str = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion using specified provider."""
        provider = provider or self.settings.default_ai_provider
        client = self._get_client(provider, model)
        async for chunk in client.stream_completion(messages, **kwargs):
            yield chunk
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers."""
        available = []
        for provider, config in self.ai_config.items():
            if config.get("api_key"):
                available.append(provider)
        return available
    
    def get_available_models(self, provider: str) -> List[str]:
        """Get list of available models for provider."""
        config = self.ai_config.get(provider)
        if config:
            return config.get("models", [])
        return []


# Global AI service instance
ai_service = AIService()
