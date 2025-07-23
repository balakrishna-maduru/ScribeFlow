#!/usr/bin/env python3
"""Debug script for AI service."""

import asyncio
import traceback
from app.services.ai_service import ai_service

async def debug_ai_service():
    """Debug the AI service step by step."""
    try:
        print("=== Debug AI Service ===")
        
        # Test 1: Check available providers
        print("\n1. Checking available providers...")
        providers = ai_service.get_available_providers()
        print(f"Available providers: {providers}")
        
        # Test 2: Check available models for Google
        print("\n2. Checking available models for Google...")
        models = ai_service.get_available_models("google")
        print(f"Google models: {models}")
        
        # Test 3: Try to get the Google client
        print("\n3. Getting Google client...")
        try:
            client = ai_service._get_client("google", "gemini-1.5-flash")
            print(f"✅ Google client created successfully: {type(client)}")
            
            # Debug: Check the API key being used
            print(f"Client API key: {client.api_key[:10]}..." if client.api_key else "No API key!")
            
        except Exception as e:
            print(f"❌ Failed to create Google client: {e}")
            traceback.print_exc()
            return
        
        # Test 4: Try a simple chat completion
        print("\n4. Testing chat completion...")
        messages = [
            {"role": "user", "content": "Hello! Please say 'Google API working' to confirm."}
        ]
        
        response = await ai_service.chat_completion(
            messages=messages,
            provider="google",
            model="gemini-1.5-flash",
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ Chat completion successful!")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"❌ Error in debug_ai_service: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_ai_service())
