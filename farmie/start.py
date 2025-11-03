#!/usr/bin/env python3
"""
Farm IoT Monitoring Service - Startup Script
This script helps you get started with the Farm IoT Monitoring Service
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'python-dotenv',
        'scikit-learn', 'pandas', 'numpy', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Check if .env file exists and is configured"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("   Copy .env.example to .env and configure your API keys")
        return False
    
    print("✅ .env file found")
    
    # Check if API keys are configured
    with open(env_file, 'r') as f:
        content = f.read()
        
    if 'your_openai_api_key_here' in content:
        print("⚠️  OpenAI API key not configured")
    else:
        print("✅ OpenAI API key configured")
        
    if 'your_google_api_key_here' in content:
        print("⚠️  Google API key not configured")
    else:
        print("✅ Google API key configured")
        
    if 'your_openweather_api_key_here' in content:
        print("⚠️  OpenWeather API key not configured")
    else:
        print("✅ OpenWeather API key configured")
    
    return True

def check_models():
    """Check if ML models are trained"""
    models_dir = Path("app/models/saved")
    
    if not models_dir.exists():
        print("❌ Models directory not found")
        return False
    
    required_files = [
        "irrigation_model.pkl",
        "crop_health_model.pkl", 
        "yield_model.pkl",
        "model_metadata.pkl"
    ]
    
    missing_models = []
    for file in required_files:
        if not (models_dir / file).exists():
            missing_models.append(file)
    
    if missing_models:
        print(f"⚠️  Missing model files: {', '.join(missing_models)}")
        print("   Models will be auto-trained on first run")
        return False
    
    print("✅ ML models found")
    return True

def train_models():
    """Train ML models"""
    print("🤖 Training ML models...")
    try:
        result = subprocess.run([
            sys.executable, "app/models/train.py"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Models trained successfully")
            return True
        else:
            print(f"❌ Model training failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Model training timed out")
        return False
    except Exception as e:
        print(f"❌ Model training error: {e}")
        return False

def generate_sample_data():
    """Generate sample data for testing"""
    print("📊 Generating sample data...")
    try:
        result = subprocess.run([
            sys.executable, "data/generate_sample_data.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Sample data generated")
            return True
        else:
            print(f"❌ Sample data generation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Sample data generation error: {e}")
        return False

def start_service():
    """Start the FastAPI service"""
    print("🚀 Starting Farm IoT Monitoring Service...")
    print("   Service will be available at: http://localhost:8000")
    print("   API documentation: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop the service")
    print()
    
    try:
        subprocess.run([
            sys.executable, "app/main.py"
        ])
    except KeyboardInterrupt:
        print("\n👋 Service stopped")
    except Exception as e:
        print(f"❌ Service error: {e}")

def main():
    """Main startup function"""
    print("🌱 Farm IoT Monitoring Service - Startup")
    print("=" * 50)
    
    # Check prerequisites
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("ML Models", check_models)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 20)
        if not check_func():
            all_passed = False
    
    if not all_passed:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\n🔧 Quick fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure .env file: cp .env.example .env")
        print("3. Train models: python app/models/train.py")
        return
    
    print("\n✅ All checks passed!")
    
    # Ask user what to do
    print("\n🎯 What would you like to do?")
    print("1. Start the service")
    print("2. Train models")
    print("3. Generate sample data")
    print("4. Run tests")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        start_service()
    elif choice == "2":
        train_models()
    elif choice == "3":
        generate_sample_data()
    elif choice == "4":
        print("🧪 Running tests...")
        subprocess.run([sys.executable, "test_api.py"])
    elif choice == "5":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
