#!/usr/bin/env python3
"""
Test script for Farm IoT Monitoring Service
Run this script to test the API endpoints with sample data
"""

import requests
import json
import time
from datetime import datetime
import os

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['data']['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data['message']}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_sensor_data():
    """Test sensor data endpoint"""
    print("🔍 Testing sensor data endpoint...")
    
    # Sample sensor data
    sensor_data = {
        "sensor_id": "test_temp_001",
        "sensor_type": "dht_temperature",
        "value": 25.5,
        "timestamp": datetime.utcnow().isoformat(),
        "location": "test_field",
        "metadata": {
            "battery_level": 95.0,
            "signal_strength": 85.0
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/sensors/data",
            json=sensor_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sensor data processed: {data['message']}")
            print(f"   Predictions: {len(data['data']['predictions'])} models")
            print(f"   Insights: {len(data['data']['insights'])} generated")
            return True
        else:
            print(f"❌ Sensor data failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Sensor data error: {e}")
        return False

def test_batch_sensor_data():
    """Test batch sensor data endpoint"""
    print("🔍 Testing batch sensor data endpoint...")
    
    batch_data = {
        "farm_id": "test_farm_001",
        "sensors": [
            {
                "sensor_id": "test_temp_001",
                "sensor_type": "dht_temperature",
                "value": 25.5,
                "timestamp": datetime.utcnow().isoformat(),
                "location": "test_field_a"
            },
            {
                "sensor_id": "test_humid_001", 
                "sensor_type": "dht_humidity",
                "value": 65.2,
                "timestamp": datetime.utcnow().isoformat(),
                "location": "test_field_a"
            },
            {
                "sensor_id": "test_moist_001",
                "sensor_type": "soil_moisture", 
                "value": 45.8,
                "timestamp": datetime.utcnow().isoformat(),
                "location": "test_field_a"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/sensors/batch",
            json=batch_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Batch data processed: {data['message']}")
            print(f"   Processed sensors: {data['data']['processed_count']}")
            return True
        else:
            print(f"❌ Batch data failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Batch data error: {e}")
        return False

def test_weather_endpoints():
    """Test weather endpoints"""
    print("🔍 Testing weather endpoints...")
    
    endpoints = [
        ("/api/weather/current", "Current weather"),
        ("/api/weather/forecast?days=3", "Weather forecast"),
        ("/api/weather/summary", "Weather summary"),
        ("/api/weather/air-quality", "Air quality")
    ]
    
    success_count = 0
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                success_count += 1
            else:
                print(f"❌ {description}: Failed ({response.status_code})")
        except Exception as e:
            print(f"❌ {description}: Error ({e})")
    
    return success_count == len(endpoints)

def test_feedback_endpoints():
    """Test feedback endpoints"""
    print("🔍 Testing feedback endpoints...")
    
    # Test feedback submission
    feedback_data = {
        "feedback_id": "test_feedback_001",
        "sensor_data_id": "test_sensor_001",
        "prediction_id": "test_pred_001",
        "user_rating": 4,
        "feedback_text": "Test feedback - prediction was helpful",
        "is_correct": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/feedback/submit",
            json=feedback_data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Feedback submitted: {data['message']}")
            
            # Test feedback retrieval
            response = requests.get(f"{BASE_URL}/api/feedback/analytics", timeout=TIMEOUT)
            if response.status_code == 200:
                print("✅ Feedback analytics: OK")
                return True
            else:
                print("❌ Feedback analytics: Failed")
                return False
        else:
            print(f"❌ Feedback submission failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return False

def test_configuration():
    """Test configuration endpoint"""
    print("🔍 Testing configuration endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/config", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Configuration retrieved: {data['data']['app_name']}")
            print(f"   Debug mode: {data['data']['debug']}")
            print(f"   Weather API configured: {data['data']['weather_api_configured']}")
            return True
        else:
            print(f"❌ Configuration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Farm IoT Monitoring Service Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("Sensor Data", test_sensor_data),
        ("Batch Sensor Data", test_batch_sensor_data),
        ("Weather Endpoints", test_weather_endpoints),
        ("Feedback Endpoints", test_feedback_endpoints),
        ("Configuration", test_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        
        time.sleep(0.5)  # Small delay between tests
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Service is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the service logs for details.")
    
    return passed == total

if __name__ == "__main__":
    print("Farm IoT Monitoring Service - Test Suite")
    print("Make sure the service is running on http://localhost:8000")
    print("Start the service with: python app/main.py")
    print()
    
    input("Press Enter to start tests...")
    
    success = run_all_tests()
    
    if success:
        print("\n🔗 Next steps:")
        print("1. Visit http://localhost:8000/docs for interactive API documentation")
        print("2. Try the sample data: python data/generate_sample_data.py")
        print("3. Check the data/ directory for saved sensor data")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the service is running: python app/main.py")
        print("2. Check the service logs for errors")
        print("3. Verify all dependencies are installed: pip install -r requirements.txt")
        print("4. Check .env file configuration")
    
    exit(0 if success else 1)
