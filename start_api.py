"""
Start script for NHS Paperwork Agent FastAPI backend
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import settings, ensure_directories

if __name__ == "__main__":
    # Ensure directories exist
    ensure_directories()
    
    print(f"🩺 Starting NHS Paperwork Agent API Server")
    print(f"📡 Server will run on http://{settings.api_host}:{settings.api_port}")
    print(f"🔧 Debug mode: {settings.debug}")
    
    # Check for OpenAI API key
    if not settings.openai_api_key:
        print("⚠️ WARNING: OPENAI_API_KEY not set. AI features will not work.")
        print("Please set your OpenAI API key in the .env file")
    
    # Start the server
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
