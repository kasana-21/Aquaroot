from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager

try:
    from app.api import sensors, weather, feedback
    from app.schemas.models import APIResponse, ErrorResponse
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.api import sensors, weather, feedback
    from app.schemas.models import APIResponse, ErrorResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Farm IoT Monitoring Service...")
    
    # Check if models exist, if not, train them
    models_dir = "app/models/saved"
    if not os.path.exists(os.path.join(models_dir, "model_metadata.pkl")):
        logger.info("No pre-trained models found. Training models...")
        try:
            from app.models.train import FarmMLTrainer
            trainer = FarmMLTrainer(models_dir)
            trainer.train_all_models(n_samples=1000)
            logger.info("Models trained successfully!")
        except Exception as e:
            logger.error(f"Error training models: {e}")
    
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Farm IoT Monitoring Service started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Farm IoT Monitoring Service...")


# Create FastAPI application
app = FastAPI(
    title="Farm IoT Monitoring Service",
    description="""
    A comprehensive IoT farm monitoring service that:
    
    * **Receives real-time sensor data** from DHT sensors (temperature, humidity) and soil sensors (moisture, temperature)
    * **Performs ML predictions** for irrigation needs, crop health, and yield forecasting
    * **Generates AI-powered insights** using LLM services (OpenAI/Gemini) for farm recommendations
    * **Integrates weather data** from third-party APIs for contextual analysis
    * **Collects user feedback** for continuous model improvement and retraining
    
    ## Features
    
    * Real-time sensor data processing and validation
    * Machine learning predictions for farm management
    * AI-generated insights and recommendations
    * Weather integration for comprehensive analysis
    * Feedback collection and model retraining capabilities
    * Comprehensive API documentation and testing interface
    """,
    version="1.0.0",
    contact={
        "name": "Farm IoT Team",
        "email": "support@farmiot.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Add CORS middleware
# Get allowed origins from environment variable (comma-separated)
# For production, set ALLOWED_ORIGINS in Vercel environment variables
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # Default to allow all in development, but this should be set in production
    allowed_origins = ["*"]
    if os.getenv("DEBUG", "False").lower() != "true":
        logger.warning("ALLOWED_ORIGINS not set - using '*' which is insecure for production!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    # Log full error for debugging (only in debug mode)
    if os.getenv("DEBUG", "False").lower() == "true":
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
    else:
        # In production, log error without sensitive details
        logger.error(f"Unhandled exception: {type(exc).__name__}")
    
    # Never expose internal error details to clients
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )


# Include API routers
app.include_router(sensors.router)
app.include_router(weather.router)
app.include_router(feedback.router)


@app.get("/", response_model=APIResponse)
async def root():
    """
    Root endpoint - Service status and information
    """
    return APIResponse(
        success=True,
        message="Farm IoT Monitoring Service is running",
        data={
            "service": "Farm IoT Monitoring Service",
            "version": "1.0.0",
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "sensors": "/api/sensors",
                "weather": "/api/weather", 
                "feedback": "/api/feedback",
                "docs": "/docs",
                "openapi": "/openapi.json"
            }
        }
    )


@app.get("/health", response_model=APIResponse)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    """
    try:
        # Check if models are loaded
        models_dir = "app/models/saved"
        model_files = [
            "irrigation_model.pkl",
            "crop_health_model.pkl", 
            "yield_model.pkl",
            "model_metadata.pkl"
        ]
        
        models_status = {}
        for model_file in model_files:
            model_path = os.path.join(models_dir, model_file)
            models_status[model_file] = os.path.exists(model_path)
        
        all_models_loaded = all(models_status.values())
        
        # Check data directory
        data_dir_exists = os.path.exists("data")
        
        health_status = {
            "status": "healthy" if all_models_loaded and data_dir_exists else "degraded",
            "models_loaded": all_models_loaded,
            "models_status": models_status,
            "data_directory": data_dir_exists,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Health check completed",
            data=health_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return APIResponse(
            success=False,
            message="Health check failed",
            data={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/metrics", response_model=APIResponse)
async def get_metrics():
    """
    Get service metrics and statistics
    """
    try:
        # This would typically collect metrics from a monitoring system
        # For now, we'll return mock metrics
        metrics = {
            "requests_total": 1250,
            "requests_per_minute": 15.5,
            "average_response_time_ms": 245,
            "error_rate_percent": 2.1,
            "active_sensors": 12,
            "models_loaded": 3,
            "last_model_update": "2024-01-15T10:30:00Z",
            "uptime_hours": 72.5,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Metrics retrieved successfully",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/config", response_model=APIResponse)
async def get_config():
    """
    Get current service configuration (without sensitive data)
    """
    try:
        config = {
            "app_name": os.getenv("APP_NAME", "Farm IoT Monitoring Service"),
            "debug": os.getenv("DEBUG", "False").lower() == "true",
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "8000")),
            "model_retrain_threshold": int(os.getenv("MODEL_RETRAIN_THRESHOLD", "100")),
            "prediction_confidence_threshold": float(os.getenv("PREDICTION_CONFIDENCE_THRESHOLD", "0.7")),
            "weather_api_configured": bool(os.getenv("OPENWEATHER_API_KEY", "") and not os.getenv("OPENWEATHER_API_KEY", "").startswith("your_")),
            "openai_configured": bool(os.getenv("OPENAI_API_KEY", "") and not os.getenv("OPENAI_API_KEY", "").startswith("your_")),
            "google_configured": bool(os.getenv("GOOGLE_API_KEY", "") and not os.getenv("GOOGLE_API_KEY", "").startswith("your_")),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Configuration retrieved successfully",
            data=config
        )
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/predict", response_model=APIResponse)
async def predict(input_data: dict = Body(...)):
    """
    Run model prediction on input data
    """
    try:
        # Load your model and run prediction here
        # Example: from app.models.train import FarmMLTrainer
        # trainer = FarmMLTrainer("app/models/saved")
        # result = trainer.predict(input_data)
        result = {"prediction": "example"}  # Replace with actual prediction logic
        return APIResponse(success=True, message="Prediction successful", data=result)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return APIResponse(success=False, message="Prediction failed", data={"error": str(e)})


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Farm IoT Monitoring Service",
        version="1.0.0",
        description="""
        A comprehensive IoT farm monitoring service that processes real-time sensor data,
        performs ML predictions, generates AI insights, and integrates weather data
        for intelligent farm management.
        """,
        routes=app.routes,
    )
    
    # Add custom tags
    openapi_schema["tags"] = [
        {
            "name": "sensors",
            "description": "Sensor data endpoints for receiving and processing IoT device data"
        },
        {
            "name": "weather", 
            "description": "Weather data endpoints for current conditions, forecasts, and air quality"
        },
        {
            "name": "feedback",
            "description": "Feedback endpoints for user input and model retraining"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )