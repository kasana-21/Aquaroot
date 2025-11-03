#!/usr/bin/env python3
"""
Run script for Farm IoT Monitoring Service
This script ensures proper module path handling
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now we can import and run the app
if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"🌱 Starting Farm IoT Monitoring Service on {host}:{port}")
    print(f"📖 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    print("Press Ctrl+C to stop the service")
    
    # Import app after setting up the path
    from app.main import app
    
    uvicorn.run(
        "app.main:app",  # Use import string for proper reload
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
