from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.schemas.models import WeatherData, APIResponse
from app.services.third_party import ThirdPartyService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/weather", tags=["weather"])

# Initialize weather service
weather_service = ThirdPartyService()


@router.get("/current", response_model=WeatherData)
async def get_current_weather(
    latitude: Optional[float] = Query(None, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, description="Longitude coordinate")
):
    """
    Get current weather data for a specific location
    """
    try:
        logger.info(f"Fetching current weather for lat: {latitude}, lon: {longitude}")
        
        weather_data = weather_service.get_weather_data(latitude, longitude)
        
        return WeatherData(**weather_data)
        
    except Exception as e:
        logger.error(f"Error fetching current weather: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/forecast", response_model=List[Dict[str, Any]])
async def get_weather_forecast(
    latitude: Optional[float] = Query(None, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, description="Longitude coordinate"),
    days: int = Query(5, ge=1, le=10, description="Number of forecast days")
):
    """
    Get weather forecast for a specific location
    """
    try:
        logger.info(f"Fetching weather forecast for lat: {latitude}, lon: {longitude}, days: {days}")
        
        forecast_data = weather_service.get_weather_forecast(latitude, longitude, days)
        
        return forecast_data
        
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/historical", response_model=List[Dict[str, Any]])
async def get_historical_weather(
    latitude: Optional[float] = Query(None, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, description="Longitude coordinate"),
    days_back: int = Query(7, ge=1, le=30, description="Number of days back to fetch")
):
    """
    Get historical weather data for a specific location
    """
    try:
        logger.info(f"Fetching historical weather for lat: {latitude}, lon: {longitude}, days_back: {days_back}")
        
        historical_data = weather_service.get_historical_weather(latitude, longitude, days_back)
        
        return historical_data
        
    except Exception as e:
        logger.error(f"Error fetching historical weather: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/air-quality", response_model=Dict[str, Any])
async def get_air_quality(
    latitude: Optional[float] = Query(None, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, description="Longitude coordinate")
):
    """
    Get air quality data for a specific location
    """
    try:
        logger.info(f"Fetching air quality for lat: {latitude}, lon: {longitude}")
        
        air_quality_data = weather_service.get_air_quality(latitude, longitude)
        
        return air_quality_data
        
    except Exception as e:
        logger.error(f"Error fetching air quality: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/summary", response_model=Dict[str, Any])
async def get_weather_summary(
    latitude: Optional[float] = Query(None, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, description="Longitude coordinate")
):
    """
    Get comprehensive weather summary including current conditions, forecast, and air quality
    """
    try:
        logger.info(f"Fetching weather summary for lat: {latitude}, lon: {longitude}")
        
        # Fetch all weather data
        current_weather = weather_service.get_weather_data(latitude, longitude)
        forecast = weather_service.get_weather_forecast(latitude, longitude, 3)  # 3-day forecast
        air_quality = weather_service.get_air_quality(latitude, longitude)
        
        # Calculate summary statistics
        forecast_temps = [day['temperature'] for day in forecast[:8]]  # Next 24 hours
        avg_temp = sum(forecast_temps) / len(forecast_temps) if forecast_temps else current_weather['temperature']
        min_temp = min(forecast_temps) if forecast_temps else current_weather['temperature']
        max_temp = max(forecast_temps) if forecast_temps else current_weather['temperature']
        
        # Calculate precipitation probability
        precipitation_days = sum(1 for day in forecast[:8] if day.get('precipitation', 0) > 0)
        precipitation_probability = (precipitation_days / len(forecast[:8])) * 100 if forecast[:8] else 0
        
        # Generate weather insights
        insights = _generate_weather_insights(current_weather, forecast, air_quality)
        
        summary = {
            'current': current_weather,
            'forecast_summary': {
                'avg_temperature': round(avg_temp, 1),
                'min_temperature': round(min_temp, 1),
                'max_temperature': round(max_temp, 1),
                'precipitation_probability': round(precipitation_probability, 1),
                'forecast_period': '24 hours'
            },
            'air_quality': air_quality,
            'insights': insights,
            'timestamp': datetime.utcnow().isoformat(),
            'location': current_weather.get('location', 'Unknown')
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching weather summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/farm-recommendations", response_model=Dict[str, Any])
async def get_farm_recommendations(
    latitude: Optional[float] = Query(None, description="Latitude coordinate"),
    longitude: Optional[float] = Query(None, description="Longitude coordinate"),
    crop_type: str = Query("general", description="Type of crop being grown")
):
    """
    Get farm-specific recommendations based on weather conditions
    """
    try:
        logger.info(f"Fetching farm recommendations for lat: {latitude}, lon: {longitude}, crop: {crop_type}")
        
        # Get current weather and forecast
        current_weather = weather_service.get_weather_data(latitude, longitude)
        forecast = weather_service.get_weather_forecast(latitude, longitude, 5)
        
        # Generate farm-specific recommendations
        recommendations = _generate_farm_recommendations(current_weather, forecast, crop_type)
        
        return {
            'weather_data': current_weather,
            'recommendations': recommendations,
            'crop_type': crop_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating farm recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _generate_weather_insights(current_weather: Dict, forecast: List[Dict], air_quality: Dict) -> List[str]:
    """Generate weather insights based on current and forecast data"""
    insights = []
    
    # Temperature insights
    temp = current_weather['temperature']
    if temp > 30:
        insights.append("High temperature detected - monitor crop stress")
    elif temp < 10:
        insights.append("Low temperature - risk of frost damage")
    
    # Humidity insights
    humidity = current_weather['humidity']
    if humidity > 80:
        insights.append("High humidity - increased disease risk")
    elif humidity < 30:
        insights.append("Low humidity - increased irrigation needs")
    
    # Precipitation insights
    precipitation = current_weather['precipitation']
    if precipitation > 5:
        insights.append("Heavy precipitation - check drainage systems")
    
    # Wind insights
    wind_speed = current_weather['wind_speed']
    if wind_speed > 15:
        insights.append("High wind speed - protect sensitive crops")
    
    # Air quality insights
    aqi = air_quality.get('aqi', 1)
    if aqi > 3:
        insights.append("Poor air quality - consider crop protection measures")
    
    # Forecast insights
    forecast_precip = sum(day.get('precipitation', 0) for day in forecast[:3])
    if forecast_precip > 10:
        insights.append("Heavy rain forecast - prepare for waterlogging")
    
    return insights


def _generate_farm_recommendations(current_weather: Dict, forecast: List[Dict], crop_type: str) -> Dict[str, Any]:
    """Generate farm-specific recommendations based on weather and crop type"""
    recommendations = {
        'irrigation': [],
        'pest_management': [],
        'harvest_timing': [],
        'general': []
    }
    
    temp = current_weather['temperature']
    humidity = current_weather['humidity']
    precipitation = current_weather['precipitation']
    wind_speed = current_weather['wind_speed']
    
    # Irrigation recommendations
    if precipitation < 2 and humidity < 50:
        recommendations['irrigation'].append("Consider irrigation - low precipitation and humidity")
    
    if precipitation > 10:
        recommendations['irrigation'].append("Reduce irrigation - high precipitation expected")
    
    # Pest management recommendations
    if humidity > 70:
        recommendations['pest_management'].append("High humidity - monitor for fungal diseases")
    
    if temp > 25 and humidity > 60:
        recommendations['pest_management'].append("Optimal conditions for pest activity - increase monitoring")
    
    # Harvest timing recommendations
    forecast_precip = sum(day.get('precipitation', 0) for day in forecast[:3])
    if forecast_precip < 5 and wind_speed < 10:
        recommendations['harvest_timing'].append("Good conditions for harvesting in next 3 days")
    
    if forecast_precip > 15:
        recommendations['harvest_timing'].append("Avoid harvesting - heavy rain forecast")
    
    # General recommendations
    if temp > 30:
        recommendations['general'].append("Provide shade or cooling for heat-sensitive crops")
    
    if wind_speed > 15:
        recommendations['general'].append("Secure equipment and protect crops from wind damage")
    
    # Crop-specific recommendations
    if crop_type.lower() == 'tomato':
        if humidity > 80:
            recommendations['pest_management'].append("Tomatoes: High humidity increases blight risk")
    elif crop_type.lower() == 'lettuce':
        if temp > 25:
            recommendations['general'].append("Lettuce: High temperature may cause bolting")
    
    return recommendations


