"""
Setup script for NHS Paperwork Automation Agent
"""

import os
import sys
import shutil
from pathlib import Path


def main():
    """Run initial setup"""
    print("🩺 NHS Paperwork Automation Agent - Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if not env_file.exists() and env_template.exists():
        print("📄 Creating .env file from template...")
        shutil.copy(env_template, env_file)
        print("✅ .env file created")
        print("⚠️ Please edit .env and add your OpenAI API key")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ .env.template not found")
        return False
    
    # Create required directories
    print("📁 Creating directories...")
    directories = [
        "data",
        "data/uploads", 
        "data/forms",
        "templates",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # Check for virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️ No virtual environment detected. Consider creating one:")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Add your OpenAI API key to .env file")
    print("3. Run demo: python demo.py")
    print("4. Start API: python start_api.py")
    print("5. Start dashboard: python start_dashboard.py")
    
    return True


if __name__ == "__main__":
    main()
