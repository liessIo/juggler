from config import Config
import google.generativeai as genai

print(f"API Key configured: {Config.is_gemini_configured()}")
print(f"API Key starts with: {Config.GEMINI_API_KEY[:10]}..." if Config.GEMINI_API_KEY else "No key")

try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello")
    print(f"✅ Gemini works: {response.text}")
except Exception as e:
    print(f"❌ Gemini failed: {e}")