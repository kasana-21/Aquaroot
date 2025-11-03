# Farm IoT Monitoring Service

A comprehensive FastAPI-based IoT farm monitoring service that processes real-time sensor data, performs ML predictions, generates AI-powered insights, and integrates weather data for intelligent farm management.

## 🌱 Features

- **Real-time Sensor Data Processing**: Receive and validate data from DHT sensors (temperature, humidity) and soil sensors (moisture, temperature)
- **Machine Learning Predictions**: Pre-trained models for irrigation needs, crop health assessment, and yield forecasting
- **AI-Powered Insights**: LLM integration (OpenAI/Gemini) for generating intelligent farm recommendations
- **Weather Integration**: Third-party weather API integration for contextual analysis
- **Feedback Collection**: User feedback system for continuous model improvement and retraining
- **Comprehensive API**: RESTful API with automatic documentation and testing interface

## 🏗️ Architecture

```
farmie/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── sensors.py          # Sensor data endpoints
│   │   ├── weather.py          # Weather data endpoints
│   │   └── feedback.py         # Feedback collection endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   ├── train.py            # ML model training
│   │   └── saved/              # Pre-trained models (.pkl files)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm.py              # LLM service integration
│   │   └── third_party.py      # Third-party API integration
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── models.py            # Pydantic data models
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Utility functions
├── data/                       # Data storage directory
├── tests/                      # Test files
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Quick Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd farmie
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Start the service**
   ```bash
   python app/main.py
   ```

The service will be available at `http://localhost:8000`

### Manual Installation

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install lightweight dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate mock ML models**
   ```bash
   python app/models/train.py
   ```

4. **Generate sample data**
   ```bash
   python data/generate_sample_data.py
   ```

5. **Start the service**
   ```bash
   python app/main.py
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# API Keys (replace with your actual keys)
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Application Settings
APP_NAME=Farm IoT Monitoring Service
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Model Settings
MODEL_RETRAIN_THRESHOLD=100
PREDICTION_CONFIDENCE_THRESHOLD=0.7

# Weather API Settings
WEATHER_API_URL=https://api.openweathermap.org/data/2.5
DEFAULT_LATITUDE=40.7128
DEFAULT_LONGITUDE=-74.0060
```

### API Keys Setup

1. **OpenWeatherMap API**:
   - Sign up at [OpenWeatherMap](https://openweathermap.org/api)
   - Get your API key from the dashboard
   - Add to `OPENWEATHER_API_KEY` in `.env`

2. **OpenAI API** (optional):
   - Sign up at [OpenAI](https://platform.openai.com/)
   - Generate an API key
   - Add to `OPENAI_API_KEY` in `.env`

3. **Google Gemini API** (optional):
   - Get API key from [Google AI Studio](https://makersuite.google.com/)
   - Add to `GOOGLE_API_KEY` in `.env`

## 📡 API Endpoints

### Sensor Data Endpoints

- `POST /api/sensors/data` - Receive single sensor reading
- `POST /api/sensors/batch` - Receive batch sensor data
- `GET /api/sensors/status/{farm_id}` - Get farm status
- `GET /api/sensors/predictions/{sensor_id}` - Get sensor predictions
- `GET /api/sensors/alerts` - Get active alerts

### Weather Endpoints

- `GET /api/weather/current` - Get current weather
- `GET /api/weather/forecast` - Get weather forecast
- `GET /api/weather/historical` - Get historical weather
- `GET /api/weather/air-quality` - Get air quality data
- `GET /api/weather/summary` - Get comprehensive weather summary
- `GET /api/weather/farm-recommendations` - Get farm-specific recommendations

### Feedback Endpoints

- `POST /api/feedback/submit` - Submit user feedback
- `GET /api/feedback/{feedback_id}` - Get specific feedback
- `GET /api/feedback` - Get all feedback with filtering
- `GET /api/feedback/analytics` - Get feedback analytics
- `POST /api/feedback/retrain` - Trigger model retraining
- `GET /api/feedback/retraining-status` - Get retraining status

### System Endpoints

- `GET /` - Service information
- `GET /health` - Health check
- `GET /metrics` - Service metrics
- `GET /config` - Configuration info
- `GET /docs` - Interactive API documentation

## 🔧 Usage Examples

### 1. Send Sensor Data

```python
import requests
import json

# Single sensor reading
sensor_data = {
    "sensor_id": "temp_001",
    "sensor_type": "dht_temperature",
    "value": 25.5,
    "timestamp": "2024-01-15T10:30:00Z",
    "location": "field_a"
}

response = requests.post(
    "http://localhost:8000/api/sensors/data",
    json=sensor_data
)
print(response.json())
```

### 2. Batch Sensor Data

```python
batch_data = {
    "farm_id": "farm_001",
    "sensors": [
        {
            "sensor_id": "temp_001",
            "sensor_type": "dht_temperature", 
            "value": 25.5,
            "timestamp": "2024-01-15T10:30:00Z",
            "location": "field_a"
        },
        {
            "sensor_id": "humid_001",
            "sensor_type": "dht_humidity",
            "value": 65.2,
            "timestamp": "2024-01-15T10:30:00Z", 
            "location": "field_a"
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/sensors/batch",
    json=batch_data
)
print(response.json())
```

### 3. Get Weather Data

```python
# Current weather
response = requests.get("http://localhost:8000/api/weather/current")
weather = response.json()
print(f"Temperature: {weather['temperature']}°C")
print(f"Humidity: {weather['humidity']}%")

# Weather forecast
response = requests.get("http://localhost:8000/api/weather/forecast?days=5")
forecast = response.json()
print(f"5-day forecast: {len(forecast)} entries")
```

### 4. Submit Feedback

```python
feedback_data = {
    "feedback_id": "feedback_001",
    "sensor_data_id": "sensor_001",
    "prediction_id": "pred_001", 
    "user_rating": 4,
    "feedback_text": "Prediction was accurate and helpful",
    "is_correct": True
}

response = requests.post(
    "http://localhost:8000/api/feedback/submit",
    json=feedback_data
)
print(response.json())
```

## 🤖 Machine Learning Models

The service includes three ML models that work with mock implementations for immediate testing:

### 1. Irrigation Need Prediction
- **Type**: Binary Classification (Mock)
- **Input**: Temperature, humidity, soil moisture, soil temperature, weather data
- **Output**: Irrigation needed (0/1) with confidence score
- **Model**: Mock Random Forest Classifier

### 2. Crop Health Assessment  
- **Type**: Regression (Mock)
- **Input**: Environmental and soil conditions
- **Output**: Health score (0-100) with confidence
- **Model**: Mock Random Forest Regressor

### 3. Yield Prediction
- **Type**: Regression (Mock)
- **Input**: Historical and current conditions
- **Output**: Predicted yield (kg/hectare) with confidence
- **Model**: Mock Random Forest Regressor

### Using Real Models

For production use, replace the mock models with real trained models:

1. **Train models in online notebooks** (Google Colab, Kaggle, etc.)
2. **Save models as .pkl files**:
   - `irrigation_model.pkl`
   - `crop_health_model.pkl`
   - `yield_model.pkl`
   - `irrigation_scaler.pkl`
   - `crop_health_scaler.pkl`
   - `yield_scaler.pkl`
   - `model_metadata.pkl`
3. **Place files in** `app/models/saved/`
4. **Update metadata** with real performance metrics

### Mock Model Training

Generate mock models for testing:

```bash
python app/models/train.py
```

This creates mock models that simulate real ML behavior for demonstration purposes.

## 🧪 Testing

### Generate Sample Data

```bash
python data/generate_sample_data.py
```

This creates sample sensor data, batch data, and feedback data for testing.

### Test API Endpoints

1. **Interactive Documentation**: Visit `http://localhost:8000/docs`
2. **Health Check**: `curl http://localhost:8000/health`
3. **Sample Data**: Use the generated sample data files

### Example Test Script

```python
import requests
import json

# Load sample data
with open('data/sample_sensor_data.json', 'r') as f:
    sensor_data = json.load(f)

# Test single sensor endpoint
response = requests.post(
    "http://localhost:8000/api/sensors/data",
    json=sensor_data[0]
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## 🔍 Monitoring and Logging

### Health Monitoring

- **Health Check**: `GET /health` - Service health status
- **Metrics**: `GET /metrics` - Performance metrics
- **Configuration**: `GET /config` - Current configuration

### Logging

The service logs to console with structured logging:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Critical errors

### Model Performance

Monitor model performance through:
- Prediction confidence scores
- User feedback ratings
- Retraining queue status

## 🚨 Error Handling

The service includes comprehensive error handling:

- **Validation Errors**: Invalid sensor data format
- **API Errors**: Third-party service failures
- **Model Errors**: ML prediction failures
- **System Errors**: Internal service errors

All errors return structured JSON responses with error codes and messages.

## 🔒 Security Considerations

### Production Deployment

1. **API Keys**: Store securely, never commit to version control
2. **CORS**: Configure appropriate origins for production
3. **Rate Limiting**: Implement rate limiting for production use
4. **Authentication**: Add authentication/authorization as needed
5. **HTTPS**: Use HTTPS in production
6. **Input Validation**: All inputs are validated using Pydantic schemas

### Environment Security

```bash
# Never commit .env files
echo ".env" >> .gitignore
echo "*.pkl" >> .gitignore
echo "data/" >> .gitignore
```

## 📊 Performance Optimization

### Scaling Considerations

1. **Database**: Replace file storage with database (PostgreSQL, MongoDB)
2. **Caching**: Add Redis for caching predictions and weather data
3. **Load Balancing**: Use multiple service instances
4. **Background Tasks**: Implement proper task queue (Celery)
5. **Model Serving**: Use dedicated ML model serving (MLflow, TensorFlow Serving)

### Performance Tips

- Use batch endpoints for multiple sensors
- Cache weather data (5-10 minute TTL)
- Implement connection pooling for external APIs
- Use async/await for I/O operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

1. **Models not loading**: Run `python app/models/train.py` to train models
2. **API key errors**: Check `.env` file configuration
3. **Port conflicts**: Change `PORT` in `.env` file
4. **Import errors**: Ensure virtual environment is activated

### Getting Help

- Check the API documentation at `/docs`
- Review the logs for error messages
- Test with sample data first
- Check environment variable configuration

## 🔮 Future Enhancements

- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Real-time WebSocket connections
- [ ] Mobile app integration
- [ ] Advanced ML models (Deep Learning)
- [ ] Multi-farm support
- [ ] Advanced analytics dashboard
- [ ] Integration with farm management systems
- [ ] Automated irrigation control
- [ ] Pest and disease detection
- [ ] Satellite imagery integration

---

**Farm IoT Monitoring Service** - Intelligent farming through IoT and AI

For more information, visit the API documentation at `http://localhost:8000/docs` when the service is running.
