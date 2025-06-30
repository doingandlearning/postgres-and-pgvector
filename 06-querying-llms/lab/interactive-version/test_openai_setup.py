#!/usr/bin/env python3
"""
Test OpenAI API Setup
Simple script to verify your OpenAI API key is working
"""

import os
import requests
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv loaded successfully")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables")

def test_openai_api():
    """Test basic OpenAI API connectivity"""
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("\nTo fix this:")
        print("1. Get an API key from https://platform.openai.com/api-keys")
        print("2. Set it as an environment variable:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("3. Or create a .env file with:")
        print("   OPENAI_API_KEY=your-key-here")
        return False
    
    print(f"✅ API key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Test API call
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Say 'Hello, RAG world!' if you can read this."}
        ],
        "max_tokens": 20,
        "temperature": 0.1
    }
    
    try:
        print("🔄 Testing OpenAI API connection...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            print(f"✅ OpenAI API test successful!")
            print(f"📝 Response: {message}")
            return True
        else:
            print(f"❌ OpenAI API Error: {response.status_code}")
            print(f"📝 Error details: {response.text}")
            
            if response.status_code == 401:
                print("\n💡 This usually means:")
                print("   - Invalid API key")
                print("   - API key has expired")
                print("   - Extra spaces in the API key")
            elif response.status_code == 429:
                print("\n💡 This usually means:")
                print("   - Rate limit exceeded")
                print("   - Quota exceeded")
                print("   - Insufficient credits")
            elif response.status_code == 400:
                print("\n💡 This usually means:")
                print("   - Malformed request")
                print("   - Invalid model name")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        print("\n💡 Check your internet connection")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🚀 OpenAI API Setup Test")
    print("=" * 40)
    
    success = test_openai_api()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Setup complete! You're ready to use the RAG assistant.")
        print("\n💡 Next steps:")
        print("   python rag_assistant.py --query 'Test question' --no-context")
        print("   python run_rag_scenarios.py")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        print("\n💡 Need help?")
        print("   - Check https://platform.openai.com/account/usage for API usage")
        print("   - Verify your API key at https://platform.openai.com/api-keys")
        print("   - Make sure you have credits/billing set up")

if __name__ == "__main__":
    main() 