from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SensorType(str, Enum):
    DHT_TEMPERATURE = "dht_temperature"
    DHT_HUMIDITY = "dht_humidity"
    SOIL_MOISTURE = "soil_moisture"
    SOIL_TEMPERATURE = "soil_temperature"


class SensorData(BaseModel):
    """Schema for incoming sensor data"""
    sensor_id: str = Field(..., description="Unique identifier for the sensor")
    sensor_type: SensorType = Field(..., description="Type of sensor")
    value: float = Field(..., description="Sensor reading value")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the reading")
    location: Optional[str] = Field(None, description="Location identifier (e.g., field_section_1)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional sensor metadata")

    @validator('value')
    def validate_value(cls, v, values):
        sensor_type = values.get('sensor_type')
        if sensor_type == SensorType.DHT_TEMPERATURE:
            if not -40 <= v <= 80:  # Celsius range
                raise ValueError('Temperature must be between -40°C and 80°C')
        elif sensor_type == SensorType.DHT_HUMIDITY:
            if not 0 <= v <= 100:  # Percentage
                raise ValueError('Humidity must be between 0% and 100%')
        elif sensor_type == SensorType.SOIL_MOISTURE:
            if not 0 <= v <= 100:  # Percentage
                raise ValueError('Soil moisture must be between 0% and 100%')
        elif sensor_type == SensorType.SOIL_TEMPERATURE:
            if not -20 <= v <= 60:  # Celsius range
                raise ValueError('Soil temperature must be between -20°C and 60°C')
        return v


class BatchSensorData(BaseModel):
    """Schema for batch sensor data uploads"""
    sensors: List[SensorData] = Field(..., description="List of sensor readings")
    farm_id: str = Field(..., description="Farm identifier")


class WeatherData(BaseModel):
    """Schema for weather data from third-party API"""
    temperature: float = Field(..., description="Current temperature in Celsius")
    humidity: float = Field(..., description="Current humidity percentage")
    precipitation: float = Field(..., description="Precipitation in mm")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    wind_direction: float = Field(..., description="Wind direction in degrees")
    pressure: float = Field(..., description="Atmospheric pressure in hPa")
    visibility: float = Field(..., description="Visibility in km")
    uv_index: float = Field(..., description="UV index")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: str = Field(..., description="Location name")


class MLPrediction(BaseModel):
    """Schema for ML model predictions"""
    prediction_type: str = Field(..., description="Type of prediction (e.g., irrigation_needed, crop_health)")
    predicted_value: float = Field(..., description="Predicted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence score")
    model_name: str = Field(..., description="Name of the model used")
    features_used: List[str] = Field(..., description="Features used for prediction")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LLMInsight(BaseModel):
    """Schema for LLM-generated insights"""
    insight_type: str = Field(..., description="Type of insight (e.g., irrigation_recommendation, crop_advice)")
    content: str = Field(..., description="Generated insight content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the insight")
    recommendations: List[str] = Field(default_factory=list, description="Specific recommendations")
    warnings: List[str] = Field(default_factory=list, description="Any warnings or alerts")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeedbackData(BaseModel):
    """Schema for user feedback"""
    feedback_id: str = Field(..., description="Unique feedback identifier")
    sensor_data_id: Optional[str] = Field(None, description="Associated sensor data ID")
    prediction_id: Optional[str] = Field(None, description="Associated prediction ID")
    user_rating: int = Field(..., ge=1, le=5, description="User rating (1-5)")
    feedback_text: Optional[str] = Field(None, description="User feedback text")
    is_correct: Optional[bool] = Field(None, description="Whether the prediction was correct")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FarmStatus(BaseModel):
    """Schema for overall farm status"""
    farm_id: str = Field(..., description="Farm identifier")
    overall_health_score: float = Field(..., ge=0.0, le=100.0, description="Overall farm health score")
    alerts: List[str] = Field(default_factory=list, description="Active alerts")
    recommendations: List[str] = Field(default_factory=list, description="Current recommendations")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sensor_summary: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Summary of sensor data")


class APIResponse(BaseModel):
    """Generic API response schema"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
