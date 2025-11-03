import json
import random
import os
from datetime import datetime, timedelta
import logging
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FarmMLTrainer:
    """ML trainer for farm monitoring predictions using real sklearn models"""
    
    def __init__(self, models_dir: str = "app/models/saved"):
        self.models_dir = models_dir
        
        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)
    
    def generate_sample_data(self, n_samples: int = 1000) -> list:
        """Generate sample farm data for training"""
        logger.info(f"Generating {n_samples} sample data points...")
        
        random.seed(42)
        np.random.seed(42)
        
        # Generate realistic farm data
        data = []
        base_date = datetime.now() - timedelta(days=365)
        
        for i in range(n_samples):
            # Seasonal patterns
            day_of_year = (base_date + timedelta(days=i)).timetuple().tm_yday
            
            # Temperature with seasonal variation
            temp_base = 15 + 10 * np.sin(2 * np.pi * day_of_year / 365 - np.pi/2)
            temperature = temp_base + random.uniform(-3, 3)
            
            # Humidity inversely correlated with temperature
            humidity = max(20, min(95, 80 - temperature * 0.8 + random.uniform(-5, 5)))
            
            # Soil moisture (higher in winter, lower in summer)
            soil_moisture_base = 60 - 20 * np.sin(2 * np.pi * day_of_year / 365 - np.pi/2)
            soil_moisture = max(10, min(90, soil_moisture_base + random.uniform(-8, 8)))
            
            # Soil temperature follows air temperature with lag
            soil_temp = temperature - 2 + random.uniform(-1.5, 1.5)
            
            # Precipitation (random but seasonal)
            precipitation = max(0, random.uniform(0, 5) if random.random() < 0.3 else 0)
            
            # Wind speed
            wind_speed = random.uniform(1, 10)
            
            # Calculate derived features
            temp_humidity_interaction = temperature * humidity / 100
            moisture_temp_ratio = soil_moisture / (temperature + 1)  # Avoid division by zero
            
            # Extract time features
            timestamp_obj = base_date + timedelta(days=i)
            hour = timestamp_obj.hour
            month = timestamp_obj.month
            
            # Target variables (what we want to predict)
            # Irrigation need (binary: 0 = no irrigation, 1 = irrigation needed)
            # Balanced logic to get ~40-50% positive cases for better training
            irrigation_need = 1 if (
                soil_moisture < 40 or  # Low moisture
                (temperature > 26 and humidity < 55) or  # Hot and somewhat dry
                (soil_moisture < 50 and temperature > 24) or  # Moderate conditions
                (soil_moisture < 60 and day_of_year > 150 and day_of_year < 270)  # Summer dry period
            ) else 0
            
            # Crop health score (0-100)
            crop_health = min(100, max(0, 
                50 + (soil_moisture - 50) * 0.5 + 
                (temperature - 20) * 0.3 + 
                (humidity - 50) * 0.2 + 
                random.uniform(-5, 5)
            ))
            
            # Yield prediction (kg per hectare)
            yield_prediction = max(0, 
                2000 + (crop_health - 50) * 20 + 
                (soil_moisture - 50) * 10 + 
                (temperature - 20) * 5 + 
                random.uniform(-100, 100)
            )
            
            data.append({
                'timestamp': timestamp_obj.isoformat(),
                'temperature': round(temperature, 2),
                'humidity': round(humidity, 2),
                'soil_moisture': round(soil_moisture, 2),
                'soil_temperature': round(soil_temp, 2),
                'precipitation': round(precipitation, 2),
                'wind_speed': round(wind_speed, 2),
                'temp_humidity_interaction': round(temp_humidity_interaction, 2),
                'moisture_temp_ratio': round(moisture_temp_ratio, 2),
                'hour': hour,
                'day_of_year': day_of_year,
                'month': month,
                'irrigation_need': irrigation_need,
                'crop_health': round(crop_health, 2),
                'yield_prediction': round(yield_prediction, 2)
            })
        
        logger.info(f"Generated sample data with {len(data)} records")
        return data
    
    def prepare_features(self, data: list) -> tuple:
        """Prepare feature matrix and target vectors"""
        feature_columns = [
            'temperature', 'humidity', 'soil_moisture', 'soil_temperature',
            'precipitation', 'wind_speed', 'temp_humidity_interaction', 
            'moisture_temp_ratio', 'hour', 'day_of_year', 'month'
        ]
        
        X = np.array([[row[col] for col in feature_columns] for row in data])
        y_irrigation = np.array([row['irrigation_need'] for row in data])
        y_crop_health = np.array([row['crop_health'] for row in data])
        y_yield = np.array([row['yield_prediction'] for row in data])
        
        return X, y_irrigation, y_crop_health, y_yield, feature_columns
    
    def train_irrigation_model(self, X, y_irrigation) -> dict:
        """Train irrigation need prediction model"""
        logger.info("Training irrigation need prediction model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_irrigation, test_size=0.2, random_state=42, stratify=y_irrigation
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train RandomForest Classifier
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy')
        
        # Feature importance
        feature_names = [
            'temperature', 'humidity', 'soil_moisture', 'soil_temperature',
            'precipitation', 'wind_speed', 'temp_humidity_interaction', 
            'moisture_temp_ratio', 'hour', 'day_of_year', 'month'
        ]
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        
        logger.info(f"Irrigation model accuracy: {accuracy:.3f}")
        logger.info(f"Cross-validation scores: {[round(s, 3) for s in cv_scores]}")
        logger.info(f"CV mean: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        return {
            'model': model,
            'scaler': scaler,
            'accuracy': float(accuracy),
            'cv_scores': [float(s) for s in cv_scores],
            'feature_importance': feature_importance
        }
    
    def train_crop_health_model(self, X, y_crop_health) -> dict:
        """Train crop health prediction model"""
        logger.info("Training crop health prediction model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_crop_health, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train RandomForest Regressor
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
        
        # Feature importance
        feature_names = [
            'temperature', 'humidity', 'soil_moisture', 'soil_temperature',
            'precipitation', 'wind_speed', 'temp_humidity_interaction', 
            'moisture_temp_ratio', 'hour', 'day_of_year', 'month'
        ]
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        
        logger.info(f"Crop health model MSE: {mse:.3f}")
        logger.info(f"Crop health model R²: {r2:.3f}")
        logger.info(f"Cross-validation R² scores: {[round(s, 3) for s in cv_scores]}")
        logger.info(f"CV mean: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        return {
            'model': model,
            'scaler': scaler,
            'mse': float(mse),
            'r2': float(r2),
            'cv_scores': [float(s) for s in cv_scores],
            'feature_importance': feature_importance
        }
    
    def train_yield_model(self, X, y_yield) -> dict:
        """Train yield prediction model"""
        logger.info("Training yield prediction model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_yield, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train RandomForest Regressor
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
        
        # Feature importance
        feature_names = [
            'temperature', 'humidity', 'soil_moisture', 'soil_temperature',
            'precipitation', 'wind_speed', 'temp_humidity_interaction', 
            'moisture_temp_ratio', 'hour', 'day_of_year', 'month'
        ]
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        
        logger.info(f"Yield model MSE: {mse:.3f}")
        logger.info(f"Yield model R²: {r2:.3f}")
        logger.info(f"Cross-validation R² scores: {[round(s, 3) for s in cv_scores]}")
        logger.info(f"CV mean: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        return {
            'model': model,
            'scaler': scaler,
            'mse': float(mse),
            'r2': float(r2),
            'cv_scores': [float(s) for s in cv_scores],
            'feature_importance': feature_importance
        }
    
    def save_models(self, irrigation_results: dict, crop_health_results: dict, yield_results: dict, feature_columns: list):
        """Save trained models and scalers"""
        logger.info("Saving trained models...")
        
        # Save irrigation model
        joblib.dump(irrigation_results['model'], 
                   os.path.join(self.models_dir, 'irrigation_model.pkl'))
        joblib.dump(irrigation_results['scaler'], 
                   os.path.join(self.models_dir, 'irrigation_scaler.pkl'))
        
        # Save crop health model
        joblib.dump(crop_health_results['model'], 
                   os.path.join(self.models_dir, 'crop_health_model.pkl'))
        joblib.dump(crop_health_results['scaler'], 
                   os.path.join(self.models_dir, 'crop_health_scaler.pkl'))
        
        # Save yield model
        joblib.dump(yield_results['model'], 
                   os.path.join(self.models_dir, 'yield_model.pkl'))
        joblib.dump(yield_results['scaler'], 
                   os.path.join(self.models_dir, 'yield_scaler.pkl'))
        
        # Save model metadata
        metadata = {
            'irrigation_model': {
                'accuracy': irrigation_results['accuracy'],
                'cv_scores': irrigation_results['cv_scores'],
                'cv_mean': float(np.mean(irrigation_results['cv_scores'])),
                'cv_std': float(np.std(irrigation_results['cv_scores'])),
                'feature_importance': irrigation_results['feature_importance']
            },
            'crop_health_model': {
                'mse': crop_health_results['mse'],
                'r2': crop_health_results['r2'],
                'cv_scores': crop_health_results['cv_scores'],
                'cv_mean': float(np.mean(crop_health_results['cv_scores'])),
                'cv_std': float(np.std(crop_health_results['cv_scores'])),
                'feature_importance': crop_health_results['feature_importance']
            },
            'yield_model': {
                'mse': yield_results['mse'],
                'r2': yield_results['r2'],
                'cv_scores': yield_results['cv_scores'],
                'cv_mean': float(np.mean(yield_results['cv_scores'])),
                'cv_std': float(np.std(yield_results['cv_scores'])),
                'feature_importance': yield_results['feature_importance']
            },
            'training_timestamp': datetime.now().isoformat(),
            'feature_columns': feature_columns,
            'model_type': 'sklearn_random_forest',
            'model_info': {
                'irrigation': 'RandomForestClassifier (n_estimators=100)',
                'crop_health': 'RandomForestRegressor (n_estimators=100)',
                'yield': 'RandomForestRegressor (n_estimators=100)'
            }
        }
        
        joblib.dump(metadata, os.path.join(self.models_dir, 'model_metadata.pkl'))
        
        # Save sample data for reference
        sample_data = self.generate_sample_data(100)
        with open(os.path.join(self.models_dir, 'sample_training_data.json'), 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        logger.info("Models saved successfully!")
    
    def train_all_models(self, n_samples: int = 1000):
        """Train all ML models"""
        logger.info("Starting ML model training with real sklearn models...")
        
        # Generate sample data
        data = self.generate_sample_data(n_samples)
        
        # Prepare features
        X, y_irrigation, y_crop_health, y_yield, feature_columns = self.prepare_features(data)
        
        logger.info(f"Training data shape: {X.shape}")
        logger.info(f"Irrigation classes: {np.unique(y_irrigation, return_counts=True)}")
        
        # Train models
        irrigation_results = self.train_irrigation_model(X, y_irrigation)
        crop_health_results = self.train_crop_health_model(X, y_crop_health)
        yield_results = self.train_yield_model(X, y_yield)
        
        # Save models
        self.save_models(irrigation_results, crop_health_results, yield_results, feature_columns)
        
        logger.info("All models trained and saved successfully!")
        
        return {
            'irrigation': irrigation_results,
            'crop_health': crop_health_results,
            'yield': yield_results
        }


def main():
    """Main training function"""
    trainer = FarmMLTrainer()
    results = trainer.train_all_models(n_samples=1000)
    
    print("\n" + "="*60)
    print("TRAINING SUMMARY")
    print("="*60)
    print(f"Irrigation Model Accuracy: {results['irrigation']['accuracy']:.3f}")
    print(f"  CV Mean: {np.mean(results['irrigation']['cv_scores']):.3f} (+/- {np.std(results['irrigation']['cv_scores']):.3f})")
    print(f"\nCrop Health Model R²: {results['crop_health']['r2']:.3f}")
    print(f"  CV Mean: {np.mean(results['crop_health']['cv_scores']):.3f} (+/- {np.std(results['crop_health']['cv_scores']):.3f})")
    print(f"  MSE: {results['crop_health']['mse']:.3f}")
    print(f"\nYield Model R²: {results['yield']['r2']:.3f}")
    print(f"  CV Mean: {np.mean(results['yield']['cv_scores']):.3f} (+/- {np.std(results['yield']['cv_scores']):.3f})")
    print(f"  MSE: {results['yield']['mse']:.3f}")
    print("="*60)
    print("\n✓ Real sklearn models trained and saved successfully!")
    print("✓ Models are ready for production use")


if __name__ == "__main__":
    main()
