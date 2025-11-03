import os
import joblib
import random
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Utility class for data processing and validation"""
    
    @staticmethod
    def validate_sensor_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate sensor data for anomalies"""
        errors = []
        
        # Check required fields
        required_fields = ['sensor_id', 'sensor_type', 'value', 'timestamp']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        # Validate sensor type
        valid_types = ['dht_temperature', 'dht_humidity', 'soil_moisture', 'soil_temperature']
        if data['sensor_type'] not in valid_types:
            errors.append(f"Invalid sensor type: {data['sensor_type']}")
        
        # Validate value ranges
        sensor_type = data['sensor_type']
        value = data['value']
        
        if sensor_type == 'dht_temperature':
            if not -40 <= value <= 80:
                errors.append(f"Temperature out of range: {value}°C")
        elif sensor_type == 'dht_humidity':
            if not 0 <= value <= 100:
                errors.append(f"Humidity out of range: {value}%")
        elif sensor_type == 'soil_moisture':
            if not 0 <= value <= 100:
                errors.append(f"Soil moisture out of range: {value}%")
        elif sensor_type == 'soil_temperature':
            if not -20 <= value <= 60:
                errors.append(f"Soil temperature out of range: {value}°C")
        
        # Validate timestamp
        try:
            if isinstance(data['timestamp'], str):
                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            elif isinstance(data['timestamp'], datetime):
                pass
            else:
                errors.append("Invalid timestamp format")
        except ValueError:
            errors.append("Invalid timestamp format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def detect_anomalies(sensor_data: List[Dict[str, Any]], 
                        window_size: int = 10) -> List[Dict[str, Any]]:
        """Detect anomalies in sensor data using statistical methods"""
        anomalies = []
        
        if len(sensor_data) < window_size:
            return anomalies
        
        # Group by sensor type
        sensor_groups = {}
        for data in sensor_data:
            sensor_type = data['sensor_type']
            if sensor_type not in sensor_groups:
                sensor_groups[sensor_type] = []
            sensor_groups[sensor_type].append(data)
        
        for sensor_type, data_list in sensor_groups.items():
            if len(data_list) < window_size:
                continue
            
            # Sort by timestamp
            data_list.sort(key=lambda x: x['timestamp'])
            values = [d['value'] for d in data_list]
            
            # Calculate rolling statistics (simplified without numpy)
            for i in range(window_size, len(values)):
                window_values = values[i-window_size:i]
                current_value = values[i]
                
                # Calculate mean
                mean_val = sum(window_values) / len(window_values)
                
                # Calculate standard deviation
                variance = sum((x - mean_val) ** 2 for x in window_values) / len(window_values)
                std_val = variance ** 0.5
                
                # Detect outliers (values beyond 2 standard deviations)
                if std_val > 0 and abs(current_value - mean_val) > 2 * std_val:
                    anomalies.append({
                        'sensor_id': data_list[i]['sensor_id'],
                        'sensor_type': sensor_type,
                        'value': current_value,
                        'expected_range': [mean_val - 2*std_val, mean_val + 2*std_val],
                        'timestamp': data_list[i]['timestamp'],
                        'anomaly_type': 'statistical_outlier'
                    })
        
        return anomalies
    
    @staticmethod
    def prepare_features_for_prediction(sensor_data: Dict[str, Any], 
                                      weather_data: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Prepare features for ML model prediction"""
        features = []
        
        # Extract sensor values
        sensor_values = {
            'temperature': sensor_data.get('temperature', 20.0),
            'humidity': sensor_data.get('humidity', 50.0),
            'soil_moisture': sensor_data.get('soil_moisture', 50.0),
            'soil_temperature': sensor_data.get('soil_temperature', 18.0)
        }
        
        # Add weather data if available
        if weather_data:
            sensor_values.update({
                'precipitation': weather_data.get('precipitation', 0.0),
                'wind_speed': weather_data.get('wind_speed', 3.0)
            })
        else:
            sensor_values.update({
                'precipitation': 0.0,
                'wind_speed': 3.0
            })
        
        # Calculate derived features
        temp_humidity_interaction = sensor_values['temperature'] * sensor_values['humidity'] / 100
        moisture_temp_ratio = sensor_values['soil_moisture'] / (sensor_values['temperature'] + 1)
        
        # Add time-based features
        timestamp = sensor_data.get('timestamp', datetime.utcnow())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        month = timestamp.month
        
        # Combine all features
        features = [
            sensor_values['temperature'],
            sensor_values['humidity'],
            sensor_values['soil_moisture'],
            sensor_values['soil_temperature'],
            sensor_values['precipitation'],
            sensor_values['wind_speed'],
            temp_humidity_interaction,
            moisture_temp_ratio,
            hour,
            day_of_year,
            month
        ]
        
        return [features]  # Return as list of lists for compatibility


class ModelManager:
    """Utility class for managing ML models"""
    
    def __init__(self, models_dir: str = "app/models/saved"):
        self.models_dir = models_dir
        self.models = {}
        self.scalers = {}
        self.metadata = {}
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models and scalers"""
        try:
            # Load model metadata
            metadata_path = os.path.join(self.models_dir, 'model_metadata.pkl')
            if os.path.exists(metadata_path):
                self.metadata = joblib.load(metadata_path)
                logger.info("Model metadata loaded successfully")
            
            # Load models and scalers
            model_files = {
                'irrigation': 'irrigation_model.pkl',
                'crop_health': 'crop_health_model.pkl',
                'yield': 'yield_model.pkl'
            }
            
            scaler_files = {
                'irrigation': 'irrigation_scaler.pkl',
                'crop_health': 'crop_health_scaler.pkl',
                'yield': 'yield_scaler.pkl'
            }
            
            for model_name, filename in model_files.items():
                model_path = os.path.join(self.models_dir, filename)
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"{model_name} model loaded successfully")
            
            for scaler_name, filename in scaler_files.items():
                scaler_path = os.path.join(self.models_dir, filename)
                if os.path.exists(scaler_path):
                    self.scalers[scaler_name] = joblib.load(scaler_path)
                    logger.info(f"{scaler_name} scaler loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def predict_irrigation_need(self, features: List[List[float]]) -> Dict[str, Any]:
        """Predict irrigation need"""
        if 'irrigation' not in self.models or 'irrigation' not in self.scalers:
            logger.warning("Irrigation model not loaded, returning default prediction")
            return {
                'predicted_value': 0,
                'confidence': 0.5,
                'model_name': 'default',
                'features_used': ['temperature', 'humidity', 'soil_moisture', 'soil_temperature']
            }
        
        try:
            # Scale features
            features_scaled = self.scalers['irrigation'].transform(features)
            
            # Make prediction
            prediction_array = self.models['irrigation'].predict(features_scaled)
            prediction = int(prediction_array[0]) if len(prediction_array) > 0 else 0
            
            # Get prediction probabilities
            prediction_proba = self.models['irrigation'].predict_proba(features_scaled)
            
            # Calculate confidence as the maximum probability
            if prediction_proba is not None and len(prediction_proba) > 0:
                confidence = float(np.max(prediction_proba[0]))
            else:
                confidence = 0.5
            
            return {
                'predicted_value': prediction,
                'confidence': confidence,
                'model_name': 'irrigation_model',
                'features_used': self.metadata.get('feature_columns', [])
            }
            
        except Exception as e:
            logger.error(f"Error making irrigation prediction: {e}")
            return {
                'predicted_value': 0,
                'confidence': 0.5,
                'model_name': 'error',
                'features_used': []
            }
    
    def predict_crop_health(self, features: List[List[float]]) -> Dict[str, Any]:
        """Predict crop health score"""
        if 'crop_health' not in self.models or 'crop_health' not in self.scalers:
            logger.warning("Crop health model not loaded, returning default prediction")
            return {
                'predicted_value': 50.0,
                'confidence': 0.5,
                'model_name': 'default',
                'features_used': ['temperature', 'humidity', 'soil_moisture', 'soil_temperature']
            }
        
        try:
            # Scale features
            features_scaled = self.scalers['crop_health'].transform(features)
            
            # Make prediction
            prediction = self.models['crop_health'].predict(features_scaled)[0]
            
            # Calculate confidence based on prediction variance (simplified)
            confidence = 0.8  # This could be improved with proper uncertainty quantification
            
            return {
                'predicted_value': float(prediction),
                'confidence': confidence,
                'model_name': 'crop_health_model',
                'features_used': self.metadata.get('feature_columns', [])
            }
            
        except Exception as e:
            logger.error(f"Error making crop health prediction: {e}")
            return {
                'predicted_value': 50.0,
                'confidence': 0.5,
                'model_name': 'error',
                'features_used': []
            }
    
    def predict_yield(self, features: List[List[float]]) -> Dict[str, Any]:
        """Predict crop yield"""
        if 'yield' not in self.models or 'yield' not in self.scalers:
            logger.warning("Yield model not loaded, returning default prediction")
            return {
                'predicted_value': 2000.0,
                'confidence': 0.5,
                'model_name': 'default',
                'features_used': ['temperature', 'humidity', 'soil_moisture', 'soil_temperature']
            }
        
        try:
            # Scale features
            features_scaled = self.scalers['yield'].transform(features)
            
            # Make prediction
            prediction = self.models['yield'].predict(features_scaled)[0]
            
            # Calculate confidence based on prediction variance (simplified)
            confidence = 0.8  # This could be improved with proper uncertainty quantification
            
            return {
                'predicted_value': float(prediction),
                'confidence': confidence,
                'model_name': 'yield_model',
                'features_used': self.metadata.get('feature_columns', [])
            }
            
        except Exception as e:
            logger.error(f"Error making yield prediction: {e}")
            return {
                'predicted_value': 2000.0,
                'confidence': 0.5,
                'model_name': 'error',
                'features_used': []
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            'loaded_models': list(self.models.keys()),
            'loaded_scalers': list(self.scalers.keys()),
            'metadata': self.metadata,
            'models_dir': self.models_dir
        }


class DataStorage:
    """Utility class for data storage and retrieval using Firestore"""
    
    def __init__(self, use_firestore: bool = True):
        """
        Initialize data storage
        Args:
            use_firestore: If True, use Firestore. If False, use file storage (legacy mode)
        """
        self.use_firestore = use_firestore
        self.firestore_service = None
        
        if use_firestore:
            try:
                from app.services.firestore import FirestoreService
                self.firestore_service = FirestoreService()
                logger.info("DataStorage initialized with Firestore")
            except Exception as e:
                logger.warning(f"Failed to initialize Firestore, falling back to file storage: {e}")
                self.use_firestore = False
        
        # Fallback to file storage if Firestore not available
        if not self.use_firestore:
            self.data_dir = "data"
            os.makedirs(self.data_dir, exist_ok=True)
            logger.info("DataStorage initialized with file storage (legacy mode)")
    
    def save_sensor_data(self, sensor_data: Dict[str, Any], filename: Optional[str] = None):
        """Save sensor data to Firestore or file"""
        if self.use_firestore and self.firestore_service:
            try:
                document_id = None
                if filename:
                    # Extract document ID from filename (remove .json extension)
                    document_id = filename.replace('.json', '').replace('sensor_data_', '')
                
                doc_id = self.firestore_service.save_sensor_data(sensor_data, document_id)
                logger.info(f"Sensor data saved to Firestore: {doc_id}")
            except Exception as e:
                logger.error(f"Error saving sensor data to Firestore: {e}")
                # Fallback to file storage
                self._save_sensor_data_to_file(sensor_data, filename)
        else:
            self._save_sensor_data_to_file(sensor_data, filename)
    
    def _save_sensor_data_to_file(self, sensor_data: Dict[str, Any], filename: Optional[str] = None):
        """Legacy file storage method"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"sensor_data_{timestamp}.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            import json
            with open(filepath, 'w') as f:
                json.dump(sensor_data, f, indent=2, default=str)
            logger.info(f"Sensor data saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving sensor data: {e}")
    
    def load_sensor_data(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load sensor data from Firestore or file"""
        if self.use_firestore and self.firestore_service:
            try:
                document_id = filename.replace('.json', '').replace('sensor_data_', '')
                return self.firestore_service.get_sensor_data(document_id)
            except Exception as e:
                logger.error(f"Error loading sensor data from Firestore: {e}")
                return self._load_sensor_data_from_file(filename)
        else:
            return self._load_sensor_data_from_file(filename)
    
    def _load_sensor_data_from_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Legacy file loading method"""
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            import json
            with open(filepath, 'r') as f:
                data = json.load(f)
            logger.info(f"Sensor data loaded from {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error loading sensor data: {e}")
            return None
    
    def save_prediction_results(self, predictions: Dict[str, Any], filename: Optional[str] = None):
        """Save prediction results to Firestore or file"""
        if self.use_firestore and self.firestore_service:
            try:
                document_id = None
                if filename:
                    document_id = filename.replace('.json', '').replace('predictions_', '')
                
                doc_id = self.firestore_service.save_prediction(predictions, document_id)
                logger.info(f"Prediction results saved to Firestore: {doc_id}")
            except Exception as e:
                logger.error(f"Error saving predictions to Firestore: {e}")
                self._save_prediction_results_to_file(predictions, filename)
        else:
            self._save_prediction_results_to_file(predictions, filename)
    
    def _save_prediction_results_to_file(self, predictions: Dict[str, Any], filename: Optional[str] = None):
        """Legacy file storage method"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"predictions_{timestamp}.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            import json
            with open(filepath, 'w') as f:
                json.dump(predictions, f, indent=2, default=str)
            logger.info(f"Prediction results saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving prediction results: {e}")
    
    def get_data_files(self) -> List[str]:
        """Get list of data files or Firestore document IDs"""
        if self.use_firestore and self.firestore_service:
            try:
                # Get recent sensor data documents
                recent_data = self.firestore_service.query_sensor_data(limit=100)
                # Return document IDs
                return [doc.get('id', '') for doc in recent_data]
            except Exception as e:
                logger.error(f"Error listing data from Firestore: {e}")
                return []
        else:
            try:
                files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
                return sorted(files)
            except Exception as e:
                logger.error(f"Error listing data files: {e}")
                return []


class AlertManager:
    """Utility class for managing alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = {
            'temperature': {'min': 5, 'max': 35},
            'humidity': {'min': 20, 'max': 90},
            'soil_moisture': {'min': 20, 'max': 80},
            'soil_temperature': {'min': 5, 'max': 30}
        }
    
    def check_alerts(self, sensor_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for alert conditions in sensor data"""
        alerts = []
        
        for sensor_type, thresholds in self.alert_thresholds.items():
            if sensor_type in sensor_data:
                value = sensor_data[sensor_type]
                
                if value < thresholds['min']:
                    alerts.append({
                        'type': 'low_threshold',
                        'sensor_type': sensor_type,
                        'value': value,
                        'threshold': thresholds['min'],
                        'message': f"{sensor_type} is below minimum threshold",
                        'severity': 'warning',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                if value > thresholds['max']:
                    alerts.append({
                        'type': 'high_threshold',
                        'sensor_type': sensor_type,
                        'value': value,
                        'threshold': thresholds['max'],
                        'message': f"{sensor_type} is above maximum threshold",
                        'severity': 'critical',
                        'timestamp': datetime.utcnow().isoformat()
                    })
        
        return alerts
    
    def update_thresholds(self, sensor_type: str, min_val: float, max_val: float):
        """Update alert thresholds for a sensor type"""
        if sensor_type in self.alert_thresholds:
            self.alert_thresholds[sensor_type] = {'min': min_val, 'max': max_val}
            logger.info(f"Updated thresholds for {sensor_type}: min={min_val}, max={max_val}")
        else:
            logger.warning(f"Unknown sensor type: {sensor_type}")


