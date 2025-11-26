import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from dotenv import load_dotenv

# Optional imports for LLM services
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available - LLM insights will use fallback")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini not available - LLM insights will use fallback")

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating insights using LLM APIs"""
    
    def __init__(self):
        self.openai_client = None
        self.gemini_model = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients"""
        # Initialize OpenAI
        if OPENAI_AVAILABLE:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key and openai_api_key != 'your_openai_api_key_here':
                openai.api_key = openai_api_key
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not found or not configured")
        else:
            logger.warning("OpenAI library not available")
        
        # Initialize Gemini
        if GEMINI_AVAILABLE:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if google_api_key and google_api_key != 'your_google_api_key_here':
                genai.configure(api_key=google_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                logger.info("Gemini client initialized")
            else:
                logger.warning("Google API key not found or not configured")
        else:
            logger.warning("Google Gemini library not available")
    
    def generate_irrigation_insight(
        self,
        sensor_data: Dict[str, Any],
        prediction: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]] = None,
        forecast_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate irrigation insights using LLM"""
        try:
            # Prepare context
            context = self._prepare_irrigation_context(
                sensor_data, prediction, weather_data, forecast_data
            )
            
            # Try OpenAI first, fallback to Gemini
            if self.openai_client:
                return self._generate_with_openai(context, "irrigation")
            elif self.gemini_model:
                return self._generate_with_gemini(context, "irrigation")
            else:
                return self._generate_fallback_insight(context, "irrigation")
                
        except Exception as e:
            logger.error(f"Error generating irrigation insight: {e}")
            return self._generate_fallback_insight(sensor_data, "irrigation")
    
    def generate_crop_health_insight(
        self,
        sensor_data: Dict[str, Any],
        prediction: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]] = None,
        forecast_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate crop health insights using LLM"""
        try:
            context = self._prepare_crop_health_context(
                sensor_data, prediction, weather_data, forecast_data
            )
            
            if self.openai_client:
                return self._generate_with_openai(context, "crop_health")
            elif self.gemini_model:
                return self._generate_with_gemini(context, "crop_health")
            else:
                return self._generate_fallback_insight(context, "crop_health")
                
        except Exception as e:
            logger.error(f"Error generating crop health insight: {e}")
            return self._generate_fallback_insight(sensor_data, "crop_health")
    
    def generate_yield_insight(
        self,
        sensor_data: Dict[str, Any],
        prediction: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]] = None,
        forecast_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate yield prediction insights using LLM"""
        try:
            context = self._prepare_yield_context(
                sensor_data, prediction, weather_data, forecast_data
            )
            
            if self.openai_client:
                return self._generate_with_openai(context, "yield")
            elif self.gemini_model:
                return self._generate_with_gemini(context, "yield")
            else:
                return self._generate_fallback_insight(context, "yield")
                
        except Exception as e:
            logger.error(f"Error generating yield insight: {e}")
            return self._generate_fallback_insight(sensor_data, "yield")
    
    def _prepare_irrigation_context(
        self,
        sensor_data: Dict,
        prediction: Dict,
        weather_data: Optional[Dict],
        forecast_data: Optional[List[Dict[str, Any]]],
    ) -> str:
        """Prepare context for irrigation insights, including forecast if available"""
        context = f"""
        Farm Sensor Data:
        - Temperature: {sensor_data.get('temperature', 'N/A')}°C
        - Humidity: {sensor_data.get('humidity', 'N/A')}%
        - Soil Moisture: {sensor_data.get('soil_moisture', 'N/A')}%
        - Soil Temperature: {sensor_data.get('soil_temperature', 'N/A')}°C
        
        ML Prediction:
        - Irrigation Needed: {prediction.get('predicted_value', 'N/A')}
        - Confidence: {prediction.get('confidence', 'N/A')}
        """
        
        if weather_data:
            context += f"""
            Current Weather Data:
            - Temperature: {weather_data.get('temperature', 'N/A')}°C
            - Humidity: {weather_data.get('humidity', 'N/A')}%
            - Precipitation (last hour): {weather_data.get('precipitation', 'N/A')}mm
            - Wind Speed: {weather_data.get('wind_speed', 'N/A')}m/s
            - Pressure: {weather_data.get('pressure', 'N/A')}hPa
            """

        if forecast_data:
            # Summarize next 24h from forecast
            next_window = forecast_data[:8]
            if next_window:
                temps = [d.get('temperature') for d in next_window if d.get('temperature') is not None]
                precip = [d.get('precipitation', 0) for d in next_window]
                avg_temp = sum(temps) / len(temps) if temps else 'N/A'
                total_precip = sum(precip) if precip else 'N/A'
                context += f"""
                Short-term Forecast (next 24h):
                - Average Temperature: {avg_temp}°C
                - Total Precipitation: {total_precip}mm
                - Example Conditions: {next_window[0].get('description', 'N/A')}
                """
        
        return context
    
    def _prepare_crop_health_context(
        self,
        sensor_data: Dict,
        prediction: Dict,
        weather_data: Optional[Dict],
        forecast_data: Optional[List[Dict[str, Any]]],
    ) -> str:
        """Prepare context for crop health insights, including forecast if available"""
        context = f"""
        Farm Sensor Data:
        - Temperature: {sensor_data.get('temperature', 'N/A')}°C
        - Humidity: {sensor_data.get('humidity', 'N/A')}%
        - Soil Moisture: {sensor_data.get('soil_moisture', 'N/A')}%
        - Soil Temperature: {sensor_data.get('soil_temperature', 'N/A')}°C
        
        ML Prediction:
        - Crop Health Score: {prediction.get('predicted_value', 'N/A')}/100
        - Confidence: {prediction.get('confidence', 'N/A')}
        """
        
        if weather_data:
            context += f"""
            Current Weather Data:
            - Temperature: {weather_data.get('temperature', 'N/A')}°C
            - Humidity: {weather_data.get('humidity', 'N/A')}%
            - UV Index: {weather_data.get('uv_index', 'N/A')}
            """

        if forecast_data:
            next_window = forecast_data[:8]
            if next_window:
                temps = [d.get('temperature') for d in next_window if d.get('temperature') is not None]
                humid = [d.get('humidity') for d in next_window if d.get('humidity') is not None]
                avg_temp = sum(temps) / len(temps) if temps else 'N/A'
                avg_hum = sum(humid) / len(humid) if humid else 'N/A'
                context += f"""
                Short-term Forecast (next 24h):
                - Average Temperature: {avg_temp}°C
                - Average Humidity: {avg_hum}%
                - Example Conditions: {next_window[0].get('description', 'N/A')}
                """
        
        return context
    
    def _prepare_yield_context(
        self,
        sensor_data: Dict,
        prediction: Dict,
        weather_data: Optional[Dict],
        forecast_data: Optional[List[Dict[str, Any]]],
    ) -> str:
        """Prepare context for yield insights, including forecast if available"""
        context = f"""
        Farm Sensor Data:
        - Temperature: {sensor_data.get('temperature', 'N/A')}°C
        - Humidity: {sensor_data.get('humidity', 'N/A')}%
        - Soil Moisture: {sensor_data.get('soil_moisture', 'N/A')}%
        - Soil Temperature: {sensor_data.get('soil_temperature', 'N/A')}°C
        
        ML Prediction:
        - Predicted Yield: {prediction.get('predicted_value', 'N/A')} kg/hectare
        - Confidence: {prediction.get('confidence', 'N/A')}
        """
        
        if weather_data:
            context += f"""
            Current Weather Data:
            - Temperature: {weather_data.get('temperature', 'N/A')}°C
            - Humidity: {weather_data.get('humidity', 'N/A')}%
            - Precipitation: {weather_data.get('precipitation', 'N/A')}mm
            - Wind Speed: {weather_data.get('wind_speed', 'N/A')}m/s
            """

        if forecast_data:
            window = forecast_data[:8]
            if window:
                temps = [d.get('temperature') for d in window if d.get('temperature') is not None]
                precip = [d.get('precipitation', 0) for d in window]
                avg_temp = sum(temps) / len(temps) if temps else 'N/A'
                total_precip = sum(precip) if precip else 'N/A'
                context += f"""
                Short-term Forecast (next 24h):
                - Average Temperature: {avg_temp}°C
                - Total Precipitation: {total_precip}mm
                - Example Conditions: {window[0].get('description', 'N/A')}
                """
        
        return context
    
    def _generate_with_openai(self, context: str, insight_type: str) -> Dict[str, Any]:
        """Generate insight using OpenAI"""
        prompt = self._get_prompt_template(insight_type)
        full_prompt = f"{prompt}\n\n{context}"
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert agricultural consultant providing insights based on farm sensor data and ML predictions."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        return self._parse_llm_response(content, insight_type)
    
    def _generate_with_gemini(self, context: str, insight_type: str) -> Dict[str, Any]:
        """Generate insight using Gemini"""
        prompt = self._get_prompt_template(insight_type)
        full_prompt = f"{prompt}\n\n{context}"
        
        response = self.gemini_model.generate_content(full_prompt)
        content = response.text
        
        return self._parse_llm_response(content, insight_type)
    
    def _get_prompt_template(self, insight_type: str) -> str:
        """Get prompt template for different insight types"""
        templates = {
            "irrigation": """
            Based on the farm sensor data and ML prediction, provide irrigation recommendations.
            Include:
            1. Whether irrigation is needed and why
            2. Specific recommendations for irrigation timing and amount
            3. Any warnings about over/under irrigation
            4. Weather considerations
            
            Format your response as JSON with keys: insight_type, content, recommendations, warnings, confidence
            """,
            "crop_health": """
            Based on the farm sensor data and ML prediction, provide crop health insights.
            Include:
            1. Assessment of current crop health
            2. Factors affecting crop health
            3. Recommendations for improvement
            4. Potential issues to watch for
            
            Format your response as JSON with keys: insight_type, content, recommendations, warnings, confidence
            """,
            "yield": """
            Based on the farm sensor data and ML prediction, provide yield insights.
            Include:
            1. Yield prediction analysis
            2. Factors influencing yield
            3. Recommendations to optimize yield
            4. Risk factors affecting yield
            
            Format your response as JSON with keys: insight_type, content, recommendations, warnings, confidence
            """
        }
        
        return templates.get(insight_type, templates["irrigation"])
    
    def _parse_llm_response(self, content: str, insight_type: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Try to extract JSON from response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            parsed = json.loads(json_str)

            # Normalize into a friendly structure expected by LLMInsight
            # Ensure we always have a human-readable content string
            raw_content = parsed.get("content")
            if isinstance(raw_content, dict):
              # Flatten dict-like content into a readable sentence
              flat_parts = []
              for k, v in raw_content.items():
                  flat_parts.append(f"{k.replace('_', ' ')}: {v}")
              parsed["content"] = "; ".join(flat_parts)
            elif not isinstance(raw_content, str) or not raw_content.strip():
              # Build a generic summary from other keys if content is missing
              summary_parts = []
              if "current_crop_health" in parsed:
                  summary_parts.append(
                      f"Current crop health score is {parsed['current_crop_health']}."
                  )
              if "yield_prediction_analysis" in parsed:
                  summary_parts.append(str(parsed["yield_prediction_analysis"]))
              if not summary_parts:
                  summary_parts.append(str(parsed))
              parsed["content"] = " ".join(summary_parts)

            # Normalize recommendations and warnings to lists of strings
            for key in ["recommendations", "warnings"]:
                value = parsed.get(key, [])
                if isinstance(value, str):
                    parsed[key] = [value]
                elif isinstance(value, list):
                    parsed[key] = [str(v) for v in value]
                else:
                    parsed[key] = [str(value)] if value else []

            parsed['timestamp'] = datetime.utcnow().isoformat()
            return parsed
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return self._generate_fallback_insight(content, insight_type)
    
    def _generate_fallback_insight(self, context: Any, insight_type: str) -> Dict[str, Any]:
        """Generate fallback insight when LLM is not available"""
        fallback_insights = {
            "irrigation": {
                "insight_type": "irrigation_recommendation",
                "content": "Based on sensor data analysis, irrigation recommendations are generated using rule-based logic.",
                "recommendations": [
                    "Monitor soil moisture levels regularly",
                    "Consider weather conditions before irrigation",
                    "Avoid over-irrigation to prevent waterlogging"
                ],
                "warnings": ["LLM service unavailable - using fallback recommendations"],
                "confidence": 0.6,
                "timestamp": datetime.utcnow().isoformat()
            },
            "crop_health": {
                "insight_type": "crop_health_assessment",
                "content": "Crop health assessment based on sensor data patterns and historical trends.",
                "recommendations": [
                    "Maintain optimal soil moisture levels",
                    "Monitor temperature and humidity conditions",
                    "Regular soil testing recommended"
                ],
                "warnings": ["LLM service unavailable - using fallback assessment"],
                "confidence": 0.6,
                "timestamp": datetime.utcnow().isoformat()
            },
            "yield": {
                "insight_type": "yield_prediction",
                "content": "Yield prediction based on current sensor data and environmental conditions.",
                "recommendations": [
                    "Optimize irrigation schedule",
                    "Monitor crop development stages",
                    "Consider weather patterns for yield optimization"
                ],
                "warnings": ["LLM service unavailable - using fallback prediction"],
                "confidence": 0.6,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        return fallback_insights.get(insight_type, fallback_insights["irrigation"])


class WeatherService:
    """Service for fetching weather data from third-party APIs"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = os.getenv('WEATHER_API_URL', 'https://api.openweathermap.org/data/2.5')
        self.default_lat = float(os.getenv('DEFAULT_LATITUDE', '40.7128'))
        self.default_lon = float(os.getenv('DEFAULT_LONGITUDE', '-74.0060'))
    
    def get_current_weather(self, latitude: Optional[float] = None, 
                          longitude: Optional[float] = None) -> Dict[str, Any]:
        """Get current weather data"""
        if not self.api_key or self.api_key == 'your_openweather_api_key_here':
            logger.warning("OpenWeather API key not configured, returning mock data")
            return self._get_mock_weather_data()
        
        lat = latitude or self.default_lat
        lon = longitude or self.default_lon
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'precipitation': data.get('rain', {}).get('1h', 0),
                'wind_speed': data['wind']['speed'],
                'wind_direction': data['wind'].get('deg', 0),
                'pressure': data['main']['pressure'],
                'visibility': data.get('visibility', 0) / 1000,  # Convert to km
                'uv_index': 0,  # Not available in current weather API
                'timestamp': datetime.utcnow().isoformat(),
                'location': data['name']
            }
            
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return self._get_mock_weather_data()
    
    def get_weather_forecast(self, latitude: Optional[float] = None, 
                           longitude: Optional[float] = None, 
                           days: int = 5) -> List[Dict[str, Any]]:
        """Get weather forecast data"""
        if not self.api_key or self.api_key == 'your_openweather_api_key_here':
            logger.warning("OpenWeather API key not configured, returning mock forecast")
            return self._get_mock_forecast_data(days)
        
        lat = latitude or self.default_lat
        lon = longitude or self.default_lon
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            forecasts = []
            
            for item in data['list'][:days * 8]:  # 8 forecasts per day (3-hour intervals)
                forecasts.append({
                    'temperature': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'precipitation': item.get('rain', {}).get('3h', 0),
                    'wind_speed': item['wind']['speed'],
                    'wind_direction': item['wind'].get('deg', 0),
                    'pressure': item['main']['pressure'],
                    'timestamp': item['dt_txt'],
                    'description': item['weather'][0]['description']
                })
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return self._get_mock_forecast_data(days)
    
    def _get_mock_weather_data(self) -> Dict[str, Any]:
        """Generate mock weather data for testing"""
        import random
        
        return {
            'temperature': round(random.uniform(15, 30), 1),
            'humidity': round(random.uniform(40, 80), 1),
            'precipitation': round(random.uniform(0, 5), 1),
            'wind_speed': round(random.uniform(1, 10), 1),
            'wind_direction': round(random.uniform(0, 360), 1),
            'pressure': round(random.uniform(1000, 1020), 1),
            'visibility': round(random.uniform(5, 15), 1),
            'uv_index': round(random.uniform(0, 10), 1),
            'timestamp': datetime.utcnow().isoformat(),
            'location': 'Mock Location'
        }
    
    def _get_mock_forecast_data(self, days: int) -> List[Dict[str, Any]]:
        """Generate mock forecast data for testing"""
        import random
        from datetime import datetime, timedelta
        
        forecasts = []
        base_time = datetime.utcnow()
        
        for i in range(days * 8):
            forecast_time = base_time + timedelta(hours=i * 3)
            forecasts.append({
                'temperature': round(random.uniform(15, 30), 1),
                'humidity': round(random.uniform(40, 80), 1),
                'precipitation': round(random.uniform(0, 5), 1),
                'wind_speed': round(random.uniform(1, 10), 1),
                'wind_direction': round(random.uniform(0, 360), 1),
                'pressure': round(random.uniform(1000, 1020), 1),
                'timestamp': forecast_time.isoformat(),
                'description': random.choice(['clear sky', 'few clouds', 'scattered clouds', 'broken clouds', 'shower rain'])
            })
        
        return forecasts
