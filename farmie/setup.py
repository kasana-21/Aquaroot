#!/usr/bin/env python3
"""
Quick setup script for Farm IoT Monitoring Service
This script sets up the service with mock models for immediate testing
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🌱 Farm IoT Monitoring Service - Quick Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the farmie project root directory")
        return
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("✅ Virtual environment created")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return
    
    # Determine Python executable
    if os.name == 'nt':  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    print("📦 Installing lightweight dependencies...")
    try:
        subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to install full requirements, trying minimal set...")
        try:
            subprocess.run([str(pip_exe), "install", "-r", "requirements-minimal.txt"], 
                          check=True, capture_output=True)
            print("✅ Minimal dependencies installed successfully")
            print("ℹ️  LLM features will use fallback mode")
        except subprocess.CalledProcessError as e2:
            print(f"❌ Failed to install even minimal dependencies: {e2}")
            print("\n🔧 Manual installation options:")
            print("1. Install system dependencies:")
            print("   sudo pacman -S python-pip python-venv")
            print("2. Try installing packages individually:")
            print("   venv/bin/pip install fastapi uvicorn pydantic python-dotenv requests")
            print("3. Use conda instead:")
            print("   conda create -n farmie python=3.11")
            print("   conda activate farmie")
            print("   conda install fastapi uvicorn pydantic")
            return
    
    print("\n🤖 Generating mock ML models...")
    try:
        subprocess.run([str(python_exe), "app/models/train.py"], check=True)
        print("✅ Mock models generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate models: {e}")
        return
    
    print("\n📊 Generating sample data...")
    try:
        subprocess.run([str(python_exe), "data/generate_sample_data.py"], check=True)
        print("✅ Sample data generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate sample data: {e}")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 To start the service:")
    print("   cd farmie")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\python run.py")
    else:  # Unix/Linux/macOS
        print("   venv/bin/python run.py")
    print("\n📖 To view API documentation:")
    print("   Visit http://localhost:8000/docs")
    print("\n🧪 To run tests:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\python test_api.py")
    else:  # Unix/Linux/macOS
        print("   venv/bin/python test_api.py")
    
    print("\n📝 Note: This setup uses mock ML models.")
    print("   For production use, replace the .pkl files in app/models/saved/")
    print("   with real trained models from online notebooks.")

if __name__ == "__main__":
    main()
