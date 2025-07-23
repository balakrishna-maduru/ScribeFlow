"""Test script to verify configuration loads correctly."""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_config():
    """Test configuration loading."""
    try:
        from app.core.config import get_settings, get_ai_config, get_active_ai_config
        
        print("🔄 Testing configuration loading...")
        
        # Test basic settings loading
        settings = get_settings()
        print(f"✅ Settings loaded successfully")
        print(f"   App Name: {settings.app_name}")
        print(f"   Version: {settings.app_version}")
        print(f"   Debug: {settings.debug}")
        print(f"   API Prefix: {settings.api_prefix}")
        
        # Test AI configuration
        ai_config = get_ai_config()
        print(f"✅ AI configuration loaded")
        print(f"   Available providers: {list(ai_config.keys())}")
        
        # Test secret key
        if len(settings.secret_key) >= 32:
            print(f"✅ Secret key is valid (length: {len(settings.secret_key)})")
        else:
            print(f"❌ Secret key too short (length: {len(settings.secret_key)})")
        
        # Test AI provider configuration
        try:
            active_config = get_active_ai_config()
            print(f"✅ Active AI provider: {active_config['provider']}")
            if active_config.get('api_key'):
                print(f"✅ API key configured for {active_config['provider']}")
            else:
                print(f"⚠️  No API key configured for {active_config['provider']}")
        except Exception as e:
            print(f"⚠️  AI provider warning: {e}")
        
        # Test database URL
        print(f"✅ Database URL: {settings.database_url}")
        
        print(f"\n🎉 Configuration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_env_vars():
    """Check environment variables."""
    print("\n🔍 Checking environment variables...")
    
    required_vars = {
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"), 
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "COHERE_API_KEY": os.getenv("COHERE_API_KEY")
    }
    
    if required_vars["SECRET_KEY"]:
        print(f"✅ SECRET_KEY is set")
    else:
        print(f"⚠️  SECRET_KEY not set (will use auto-generated)")
    
    ai_keys = [k for k, v in required_vars.items() if k.endswith("_API_KEY") and v]
    if ai_keys:
        print(f"✅ AI API keys found: {ai_keys}")
    else:
        print(f"⚠️  No AI API keys set - you'll need at least one to use AI features")

if __name__ == "__main__":
    print("ScribeFlow Configuration Test")
    print("=" * 40)
    
    # Check environment variables
    check_env_vars()
    
    # Test configuration
    success = test_config()
    
    if success:
        print(f"\n✅ Ready to run the application!")
        print(f"\nTo start the application:")
        print(f"1. Set required environment variables (at least one AI API key)")
        print(f"2. Install dependencies: pip install -r requirements.txt")
        print(f"3. Run: python -m uvicorn app.main:app --reload")
    else:
        print(f"\n❌ Please fix configuration issues before running")
    
    # Show required environment variables
    print(f"\n" + "="*50)
    from app.core.config import print_required_env_vars
    print_required_env_vars()
