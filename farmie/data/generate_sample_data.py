import json
import random
from datetime import datetime, timedelta
import os

# Create sample sensor data for testing
def generate_sample_sensor_data():
    """Generate sample sensor data for testing the API"""
    
    # Sample sensor configurations
    sensors = [
        {"id": "dht_temp_001", "type": "dht_temperature", "location": "field_a"},
        {"id": "dht_humid_001", "type": "dht_humidity", "location": "field_a"},
        {"id": "soil_moist_001", "type": "soil_moisture", "location": "field_a"},
        {"id": "soil_temp_001", "type": "soil_temperature", "location": "field_a"},
        {"id": "dht_temp_002", "type": "dht_temperature", "location": "field_b"},
        {"id": "dht_humid_002", "type": "dht_humidity", "location": "field_b"},
        {"id": "soil_moist_002", "type": "soil_moisture", "location": "field_b"},
        {"id": "soil_temp_002", "type": "soil_temperature", "location": "field_b"},
    ]
    
    # Generate sample data for each sensor
    sample_data = []
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(48):  # 48 readings (every 30 minutes for 24 hours)
        timestamp = base_time + timedelta(minutes=i * 30)
        
        for sensor in sensors:
            # Generate realistic values based on sensor type
            if sensor["type"] == "dht_temperature":
                value = round(random.uniform(15, 35), 1)
            elif sensor["type"] == "dht_humidity":
                value = round(random.uniform(30, 80), 1)
            elif sensor["type"] == "soil_moisture":
                value = round(random.uniform(20, 70), 1)
            elif sensor["type"] == "soil_temperature":
                value = round(random.uniform(10, 30), 1)
            
            sensor_data = {
                "sensor_id": sensor["id"],
                "sensor_type": sensor["type"],
                "value": value,
                "timestamp": timestamp.isoformat(),
                "location": sensor["location"],
                "metadata": {
                    "battery_level": round(random.uniform(80, 100), 1),
                    "signal_strength": round(random.uniform(70, 100), 1)
                }
            }
            
            sample_data.append(sensor_data)
    
    return sample_data

def generate_batch_sensor_data():
    """Generate batch sensor data for testing"""
    sensors_data = generate_sample_sensor_data()
    
    # Group by timestamp for batch requests
    batch_data = []
    timestamps = sorted(set(data["timestamp"] for data in sensors_data))
    
    for timestamp in timestamps[:10]:  # First 10 timestamps
        sensors_at_time = [data for data in sensors_data if data["timestamp"] == timestamp]
        
        batch_request = {
            "farm_id": "farm_001",
            "sensors": sensors_at_time
        }
        
        batch_data.append(batch_request)
    
    return batch_data

def generate_feedback_data():
    """Generate sample feedback data"""
    feedback_samples = [
        {
            "feedback_id": "feedback_001",
            "sensor_data_id": "sensor_001",
            "prediction_id": "pred_001",
            "user_rating": 4,
            "feedback_text": "Temperature prediction was accurate, helped optimize irrigation timing",
            "is_correct": True,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "feedback_id": "feedback_002", 
            "sensor_data_id": "sensor_002",
            "prediction_id": "pred_002",
            "user_rating": 2,
            "feedback_text": "Soil moisture prediction was too low, caused over-irrigation",
            "is_correct": False,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "feedback_id": "feedback_003",
            "sensor_data_id": "sensor_003", 
            "prediction_id": "pred_003",
            "user_rating": 5,
            "feedback_text": "Excellent crop health assessment, recommendations were spot on",
            "is_correct": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    ]
    
    return feedback_samples

def save_sample_data():
    """Save all sample data to files"""
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Generate and save sensor data
    sensor_data = generate_sample_sensor_data()
    with open("data/sample_sensor_data.json", "w") as f:
        json.dump(sensor_data, f, indent=2)
    
    # Generate and save batch data
    batch_data = generate_batch_sensor_data()
    with open("data/sample_batch_data.json", "w") as f:
        json.dump(batch_data, f, indent=2)
    
    # Generate and save feedback data
    feedback_data = generate_feedback_data()
    with open("data/sample_feedback_data.json", "w") as f:
        json.dump(feedback_data, f, indent=2)
    
    print("Sample data generated and saved to data/ directory:")
    print("- sample_sensor_data.json")
    print("- sample_batch_data.json") 
    print("- sample_feedback_data.json")

if __name__ == "__main__":
    save_sample_data()
