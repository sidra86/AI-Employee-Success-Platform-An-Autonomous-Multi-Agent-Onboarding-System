#!/usr/bin/env python3
"""
Startup script for the AI-Powered Employee Onboarding System
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        return False
    
    # Check if .env file exists
    if not Path(".env").exists() and not Path(".env.example").exists() and not Path("env_example.txt").exists():
        print("❌ Environment file not found. Please create .env from .env.example")
        return False
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    print("✅ Requirements check passed")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Set up environment variables"""
    print("🔧 Setting up environment...")
    
    if not Path(".env").exists():
        source = Path(".env.example") if Path(".env.example").exists() else Path("env_example.txt")
        if source.exists():
            with open(source, "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print(f"📝 Created .env file from {source.name}. Edit it with your API keys if needed.")
        else:
            # Create basic .env file
            with open(".env", "w") as f:
                f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
                f.write("SECRET_KEY=your_secret_key_here\n")
                f.write("DATABASE_URL=sqlite:///./onboarding.db\n")
            print("📝 Created basic .env file. Please edit it with your API keys.")
    
    print("✅ Environment setup complete")
    return True

def create_demo_data():
    """Create demo data for testing"""
    print("🎭 Creating demo data...")
    
    # This would be implemented to add sample employees and modules
    # For now, we'll just create the database structure
    try:
        from database.database import init_db
        init_db()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting the server...")
    print("📍 Server will be available on port 8000")
    print("📊 Dashboard: /dashboard")
    print("\n🔑 Make sure to set your OPENAI_API_KEY in the .env file!")
    print("\n⏹️  Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

def main():
    """Main startup function"""
    print("🤖 AI-Powered Employee Onboarding System")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies.")
        return 1
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Failed to setup environment.")
        return 1
    
    # Create demo data
    if not create_demo_data():
        print("\n❌ Failed to create demo data.")
        return 1
    
    print("\n✅ Setup complete!")
    print("\n" + "=" * 50)
    
    # Start server
    start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
