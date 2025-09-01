"""
Start script for NHS Paperwork Agent Streamlit Dashboard
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import settings, ensure_directories

if __name__ == "__main__":
    # Ensure directories exist
    ensure_directories()
    
    print(f"🩺 Starting NHS Paperwork Agent Dashboard")
    print(f"🖥️ Dashboard will run on http://{settings.streamlit_host}:{settings.streamlit_port}")
    print(f"🔗 Make sure the API server is running on http://localhost:{settings.api_port}")
    
    # Set environment variable for API URL
    os.environ["API_BASE_URL"] = f"http://localhost:{settings.api_port}"
    
    # Start Streamlit
    dashboard_path = os.path.join("src", "dashboard", "app.py")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", dashboard_path,
        "--server.port", str(settings.streamlit_port),
        "--server.address", settings.streamlit_host,
        "--server.headless", "false"
    ])
