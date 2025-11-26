from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.schemas.models import (
    SensorData, BatchSensorData, MLPrediction, LLMInsight, 
    FarmStatus, APIResponse, ErrorResponse
)
from app.services.llm import LLMService
from app.services.third_party import ThirdPartyService
from app.utils.helpers import DataProcessor, ModelManager, DataStorage, AlertManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/sensors", tags=["sensors"])

# Initialize services
llm_service = LLMService()
weather_service = ThirdPartyService()
model_manager = ModelManager()
data_storage = DataStorage()
alert_manager = AlertManager()


@router.post("/data", response_model=APIResponse)
async def receive_sensor_data(
    sensor_data: SensorData,
    background_tasks: BackgroundTasks
):
    """
    Receive real-time sensor data from IoT devices
    """
    try:
        logger.info(f"Received sensor data: {sensor_data.sensor_id} - {sensor_data.sensor_type}")
        
        # Validate sensor data
        is_valid, errors = DataProcessor.validate_sensor_data(sensor_data.dict())
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid sensor data: {errors}")
        
        # Check for alerts
        alerts = alert_manager.check_alerts({sensor_data.sensor_type: sensor_data.value})
        
        # Prepare data for ML prediction
        sensor_dict = sensor_data.dict()
        features = DataProcessor.prepare_features_for_prediction(sensor_dict)
        
        # Get weather data for context
        weather_data = weather_service.get_weather_data()
        # Get short-term forecast (used by LLM for decisions)
        forecast_data = weather_service.get_weather_forecast(days=3)
        
        # Make ML predictions
        predictions = {}
        
        # Irrigation prediction
        irrigation_pred = model_manager.predict_irrigation_need(features)
        predictions['irrigation'] = irrigation_pred
        
        # Crop health prediction
        crop_health_pred = model_manager.predict_crop_health(features)
        predictions['crop_health'] = crop_health_pred
        
        # Yield prediction
        yield_pred = model_manager.predict_yield(features)
        predictions['yield'] = yield_pred
        
        # Generate LLM insights
        insights = {}

        # Irrigation insight (uses current weather + forecast)
        irrigation_insight = llm_service.generate_irrigation_insight(
            sensor_dict, irrigation_pred, weather_data, forecast_data
        )
        insights['irrigation'] = irrigation_insight
        
        # Crop health insight
        crop_health_insight = llm_service.generate_crop_health_insight(
            sensor_dict, crop_health_pred, weather_data, forecast_data
        )
        insights['crop_health'] = crop_health_insight
        
        # Yield insight
        yield_insight = llm_service.generate_yield_insight(
            sensor_dict, yield_pred, weather_data, forecast_data
        )
        insights['yield'] = yield_insight
        
        # Prepare response data
        response_data = {
            'sensor_data': sensor_data.dict(),
            'predictions': predictions,
            'insights': insights,
            'weather_context': weather_data,
            'forecast_context': forecast_data,
            'alerts': alerts,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Save data in background
        background_tasks.add_task(data_storage.save_sensor_data, response_data)
        
        # Also save predictions separately to Firestore if available
        if hasattr(data_storage, 'firestore_service') and data_storage.firestore_service:
            for pred_type, pred_data in predictions.items():
                pred_record = {
                    'sensor_id': sensor_data.sensor_id,
                    'prediction_type': pred_type,
                    'predicted_value': pred_data.get('predicted_value'),
                    'confidence': pred_data.get('confidence'),
                    'model_name': pred_data.get('model_name'),
                    'features_used': pred_data.get('features_used', []),
                    'timestamp': datetime.utcnow().isoformat()
                }
                background_tasks.add_task(data_storage.firestore_service.save_prediction, pred_record)
        
        return APIResponse(
            success=True,
            message="Sensor data processed successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=APIResponse)
async def receive_batch_sensor_data(
    batch_data: BatchSensorData,
    background_tasks: BackgroundTasks
):
    """
    Receive batch sensor data from multiple sensors
    """
    try:
        logger.info(f"Received batch data for farm: {batch_data.farm_id}")
        
        processed_sensors = []
        all_alerts = []
        all_predictions = {}
        all_insights = {}
        
        # Get weather data once for all sensors
        weather_data = weather_service.get_weather_data()
        # Get short-term forecast once for all sensors
        forecast_data = weather_service.get_weather_forecast(days=3)
        
        for sensor_data in batch_data.sensors:
            # Validate each sensor data
            is_valid, errors = DataProcessor.validate_sensor_data(sensor_data.dict())
            if not is_valid:
                logger.warning(f"Invalid sensor data for {sensor_data.sensor_id}: {errors}")
                continue
            
            # Check for alerts
            alerts = alert_manager.check_alerts({sensor_data.sensor_type: sensor_data.value})
            all_alerts.extend(alerts)
            
            # Prepare features and make predictions
            sensor_dict = sensor_data.dict()
            features = DataProcessor.prepare_features_for_prediction(sensor_dict, weather_data)
            
            # Make predictions for this sensor
            sensor_predictions = {
                'irrigation': model_manager.predict_irrigation_need(features),
                'crop_health': model_manager.predict_crop_health(features),
                'yield': model_manager.predict_yield(features)
            }
            
            # Generate insights (using current weather + forecast)
            sensor_insights = {
                'irrigation': llm_service.generate_irrigation_insight(
                    sensor_dict,
                    sensor_predictions['irrigation'],
                    weather_data,
                    forecast_data,
                ),
                'crop_health': llm_service.generate_crop_health_insight(
                    sensor_dict,
                    sensor_predictions['crop_health'],
                    weather_data,
                    forecast_data,
                ),
                'yield': llm_service.generate_yield_insight(
                    sensor_dict,
                    sensor_predictions['yield'],
                    weather_data,
                    forecast_data,
                )
            }
            
            processed_sensors.append({
                'sensor_data': sensor_dict,
                'predictions': sensor_predictions,
                'insights': sensor_insights,
                'alerts': alerts
            })
        
        # Calculate overall farm status
        farm_status = _calculate_farm_status(processed_sensors, all_alerts)
        
        response_data = {
            'farm_id': batch_data.farm_id,
            'processed_sensors': processed_sensors,
            'farm_status': farm_status,
            'weather_context': weather_data,
            'total_sensors': len(batch_data.sensors),
            'processed_count': len(processed_sensors),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Save batch data in background
        background_tasks.add_task(data_storage.save_sensor_data, response_data)
        
        return APIResponse(
            success=True,
            message=f"Batch data processed successfully for {len(processed_sensors)} sensors",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error processing batch sensor data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/status/{farm_id}", response_model=FarmStatus)
async def get_farm_status(farm_id: str):
    """
    Get current farm status based on recent sensor data
    """
    try:
        # Try to get real data from Firestore if available
        if hasattr(data_storage, 'firestore_service') and data_storage.firestore_service:
            recent_data = data_storage.firestore_service.query_sensor_data(
                farm_id=farm_id,
                limit=100
            )
            
            if recent_data:
                # Calculate averages from real data
                temps = []
                humids = []
                moistures = []
                
                for record in recent_data:
                    sensor_data = record.get('sensor_data', {})
                    sensor_type = sensor_data.get('sensor_type', '')
                    value = sensor_data.get('value', 0)
                    
                    if 'temperature' in sensor_type:
                        temps.append(value)
                    elif 'humidity' in sensor_type:
                        humids.append(value)
                    elif 'moisture' in sensor_type:
                        moistures.append(value)
                
                # Calculate averages
                sensor_summary = {}
                if temps:
                    sensor_summary['temperature'] = {
                        "avg": round(sum(temps) / len(temps), 1),
                        "min": round(min(temps), 1),
                        "max": round(max(temps), 1)
                    }
                if humids:
                    sensor_summary['humidity'] = {
                        "avg": round(sum(humids) / len(humids), 1),
                        "min": round(min(humids), 1),
                        "max": round(max(humids), 1)
                    }
                if moistures:
                    sensor_summary['soil_moisture'] = {
                        "avg": round(sum(moistures) / len(moistures), 1),
                        "min": round(min(moistures), 1),
                        "max": round(max(moistures), 1)
                    }
                
                # Calculate health score from crop health predictions
                health_scores = [r.get('predictions', {}).get('crop_health', {}).get('predicted_value', 50) 
                                for r in recent_data if r.get('predictions', {}).get('crop_health')]
                avg_health = sum(health_scores) / len(health_scores) if health_scores else 75.5
                
                return FarmStatus(
                    farm_id=farm_id,
                    overall_health_score=round(avg_health, 1),
                    alerts=[],
                    recommendations=[
                        "Consider irrigation for field A",
                        "Monitor soil moisture levels"
                    ],
                    last_updated=datetime.utcnow(),
                    sensor_summary=sensor_summary
                )
        
        # Fallback to mock status
        mock_status = FarmStatus(
            farm_id=farm_id,
            overall_health_score=75.5,
            alerts=["High temperature detected in field A"],
            recommendations=[
                "Consider irrigation for field A",
                "Monitor soil moisture levels"
            ],
            last_updated=datetime.utcnow(),
            sensor_summary={
                "temperature": {"avg": 25.5, "min": 20.1, "max": 30.2},
                "humidity": {"avg": 65.3, "min": 45.2, "max": 80.1},
                "soil_moisture": {"avg": 45.8, "min": 30.2, "max": 65.4}
            }
        )
        
        return mock_status
        
    except Exception as e:
        logger.error(f"Error getting farm status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/predictions/{sensor_id}", response_model=List[MLPrediction])
async def get_sensor_predictions(sensor_id: str, limit: int = 10):
    """
    Get recent predictions for a specific sensor
    """
    try:
        # Try to get real predictions from Firestore if available
        if hasattr(data_storage, 'firestore_service') and data_storage.firestore_service:
            predictions_data = data_storage.firestore_service.get_predictions(
                sensor_id=sensor_id,
                limit=limit
            )
            
            if predictions_data:
                predictions = []
                for pred_data in predictions_data:
                    # Convert Firestore prediction data to MLPrediction format
                    predictions.append(MLPrediction(
                        prediction_type=pred_data.get('prediction_type', 'unknown'),
                        predicted_value=pred_data.get('predicted_value', 0),
                        confidence=pred_data.get('confidence', 0.5),
                        model_name=pred_data.get('model_name', 'unknown'),
                        features_used=pred_data.get('features_used', []),
                        timestamp=datetime.fromisoformat(pred_data.get('timestamp', datetime.utcnow().isoformat()))
                    ))
                return predictions
        
        # Fallback to mock predictions
        mock_predictions = [
            MLPrediction(
                prediction_type="irrigation_needed",
                predicted_value=1,
                confidence=0.85,
                model_name="irrigation_model",
                features_used=["temperature", "humidity", "soil_moisture"],
                timestamp=datetime.utcnow()
            ),
            MLPrediction(
                prediction_type="crop_health",
                predicted_value=78.5,
                confidence=0.92,
                model_name="crop_health_model",
                features_used=["temperature", "humidity", "soil_moisture", "soil_temperature"],
                timestamp=datetime.utcnow()
            )
        ]
        
        return mock_predictions[:limit]
        
    except Exception as e:
        logger.error(f"Error getting sensor predictions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_active_alerts():
    """
    Get all active alerts across the farm
    """
    try:
        # This would typically query a database for active alerts
        # For now, we'll return mock alerts
        mock_alerts = [
            {
                "type": "high_threshold",
                "sensor_type": "temperature",
                "value": 32.5,
                "threshold": 30.0,
                "message": "Temperature is above maximum threshold",
                "severity": "warning",
                "timestamp": datetime.utcnow().isoformat(),
                "sensor_id": "temp_sensor_001"
            },
            {
                "type": "low_threshold",
                "sensor_type": "soil_moisture",
                "value": 18.5,
                "threshold": 20.0,
                "message": "Soil moisture is below minimum threshold",
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat(),
                "sensor_id": "moisture_sensor_002"
            }
        ]
        
        return mock_alerts
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/data-files", response_model=List[str])
async def get_data_files():
    """
    Get list of saved data files
    """
    try:
        files = data_storage.get_data_files()
        return files
        
    except Exception as e:
        logger.error(f"Error getting data files: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def _calculate_farm_status(processed_sensors: List[Dict], alerts: List[Dict]) -> Dict[str, Any]:
    """Calculate overall farm status from processed sensor data"""
    if not processed_sensors:
        return {
            "overall_health_score": 50.0,
            "alert_count": len(alerts),
            "critical_alerts": len([a for a in alerts if a.get('severity') == 'critical']),
            "recommendations": ["No sensor data available"]
        }
    
    # Calculate average crop health score
    health_scores = []
    for sensor in processed_sensors:
        if 'crop_health' in sensor['predictions']:
            health_scores.append(sensor['predictions']['crop_health']['predicted_value'])
    
    avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 50.0
    
    # Count alerts by severity
    critical_alerts = len([a for a in alerts if a.get('severity') == 'critical'])
    warning_alerts = len([a for a in alerts if a.get('severity') == 'warning'])
    
    # Generate recommendations based on predictions
    recommendations = []
    irrigation_needed = any(
        sensor['predictions'].get('irrigation', {}).get('predicted_value', 0) == 1
        for sensor in processed_sensors
    )
    
    if irrigation_needed:
        recommendations.append("Irrigation recommended for multiple fields")
    
    if avg_health_score < 60:
        recommendations.append("Crop health below optimal - check soil conditions")
    
    if critical_alerts > 0:
        recommendations.append("Address critical alerts immediately")
    
    return {
        "overall_health_score": round(avg_health_score, 1),
        "alert_count": len(alerts),
        "critical_alerts": critical_alerts,
        "warning_alerts": warning_alerts,
        "recommendations": recommendations,
        "sensor_count": len(processed_sensors)
    }


