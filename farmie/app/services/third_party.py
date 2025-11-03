import os
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThirdPartyService:
    """Service for integrating with third-party APIs"""
    
    def __init__(self):
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.openweather_base_url = os.getenv('WEATHER_API_URL', 'https://api.openweathermap.org/data/2.5')
        self.default_lat = float(os.getenv('DEFAULT_LATITUDE', '40.7128'))
        self.default_lon = float(os.getenv('DEFAULT_LONGITUDE', '-74.0060'))
    
    def get_weather_data(self, latitude: Optional[float] = None, 
                        longitude: Optional[float] = None) -> Dict[str, Any]:
        """Get current weather data from OpenWeatherMap API"""
        if not self.openweather_api_key or self.openweather_api_key == 'your_openweather_api_key_here':
            logger.warning("OpenWeather API key not configured, returning mock data")
            return self._get_mock_weather_data()
        
        lat = latitude or self.default_lat
        lon = longitude or self.default_lon
        
        try:
            # Get current weather
            current_url = f"{self.openweather_base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(current_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get UV index (requires separate API call)
            uv_index = self._get_uv_index(lat, lon)
            
            weather_data = {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'precipitation': data.get('rain', {}).get('1h', 0),
                'wind_speed': data['wind']['speed'],
                'wind_direction': data['wind'].get('deg', 0),
                'pressure': data['main']['pressure'],
                'visibility': data.get('visibility', 0) / 1000,  # Convert to km
                'uv_index': uv_index,
                'timestamp': datetime.utcnow().isoformat(),
                'location': data['name'],
                'country': data['sys']['country'],
                'weather_description': data['weather'][0]['description'],
                'weather_icon': data['weather'][0]['icon']
            }
            
            logger.info(f"Weather data fetched for {data['name']}, {data['sys']['country']}")
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return self._get_mock_weather_data()
        except Exception as e:
            logger.error(f"Unexpected error fetching weather data: {e}")
            return self._get_mock_weather_data()
    
    def get_weather_forecast(self, latitude: Optional[float] = None, 
                           longitude: Optional[float] = None, 
                           days: int = 5) -> List[Dict[str, Any]]:
        """Get weather forecast from OpenWeatherMap API"""
        if not self.openweather_api_key or self.openweather_api_key == 'your_openweather_api_key_here':
            logger.warning("OpenWeather API key not configured, returning mock forecast")
            return self._get_mock_forecast_data(days)
        
        lat = latitude or self.default_lat
        lon = longitude or self.default_lon
        
        try:
            url = f"{self.openweather_base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            forecasts = []
            
            # Process forecast data (3-hour intervals)
            for item in data['list'][:days * 8]:  # 8 forecasts per day
                forecast = {
                    'temperature': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'precipitation': item.get('rain', {}).get('3h', 0),
                    'wind_speed': item['wind']['speed'],
                    'wind_direction': item['wind'].get('deg', 0),
                    'pressure': item['main']['pressure'],
                    'timestamp': item['dt_txt'],
                    'description': item['weather'][0]['description'],
                    'icon': item['weather'][0]['icon'],
                    'temperature_min': item['main']['temp_min'],
                    'temperature_max': item['main']['temp_max']
                }
                forecasts.append(forecast)
            
            logger.info(f"Weather forecast fetched for {days} days")
            return forecasts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return self._get_mock_forecast_data(days)
        except Exception as e:
            logger.error(f"Unexpected error fetching weather forecast: {e}")
            return self._get_mock_forecast_data(days)
    
    def get_historical_weather(self, latitude: Optional[float] = None, 
                             longitude: Optional[float] = None, 
                             days_back: int = 7) -> List[Dict[str, Any]]:
        """Get historical weather data (requires One Call API 3.0)"""
        if not self.openweather_api_key or self.openweather_api_key == 'your_openweather_api_key_here':
            logger.warning("OpenWeather API key not configured, returning mock historical data")
            return self._get_mock_historical_data(days_back)
        
        lat = latitude or self.default_lat
        lon = longitude or self.default_lon
        
        try:
            # Note: Historical data requires One Call API 3.0 subscription
            # For demo purposes, we'll return mock data
            logger.info("Historical weather data requires One Call API 3.0 subscription")
            return self._get_mock_historical_data(days_back)
            
        except Exception as e:
            logger.error(f"Error fetching historical weather data: {e}")
            return self._get_mock_historical_data(days_back)
    
    def _get_uv_index(self, latitude: float, longitude: float) -> float:
        """Get UV index data (requires separate API call)"""
        try:
            url = f"{self.openweather_base_url}/uvi"
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.openweather_api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return data.get('value', 0)
            
        except Exception as e:
            logger.warning(f"Could not fetch UV index: {e}")
            return 0
    
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
            'location': 'Mock Location',
            'country': 'US',
            'weather_description': 'clear sky',
            'weather_icon': '01d'
        }
    
    def _get_mock_forecast_data(self, days: int) -> List[Dict[str, Any]]:
        """Generate mock forecast data for testing"""
        import random
        
        forecasts = []
        base_time = datetime.utcnow()
        
        for i in range(days * 8):  # 8 forecasts per day (3-hour intervals)
            forecast_time = base_time + timedelta(hours=i * 3)
            temp = round(random.uniform(15, 30), 1)
            
            forecasts.append({
                'temperature': temp,
                'humidity': round(random.uniform(40, 80), 1),
                'precipitation': round(random.uniform(0, 5), 1),
                'wind_speed': round(random.uniform(1, 10), 1),
                'wind_direction': round(random.uniform(0, 360), 1),
                'pressure': round(random.uniform(1000, 1020), 1),
                'timestamp': forecast_time.isoformat(),
                'description': random.choice(['clear sky', 'few clouds', 'scattered clouds', 'broken clouds', 'shower rain']),
                'icon': random.choice(['01d', '02d', '03d', '04d', '09d']),
                'temperature_min': round(temp - random.uniform(2, 5), 1),
                'temperature_max': round(temp + random.uniform(2, 5), 1)
            })
        
        return forecasts
    
    def _get_mock_historical_data(self, days_back: int) -> List[Dict[str, Any]]:
        """Generate mock historical weather data"""
        import random
        
        historical_data = []
        base_time = datetime.utcnow() - timedelta(days=days_back)
        
        for i in range(days_back):
            day_time = base_time + timedelta(days=i)
            
            historical_data.append({
                'date': day_time.strftime('%Y-%m-%d'),
                'temperature_avg': round(random.uniform(15, 30), 1),
                'temperature_min': round(random.uniform(10, 20), 1),
                'temperature_max': round(random.uniform(25, 35), 1),
                'humidity': round(random.uniform(40, 80), 1),
                'precipitation': round(random.uniform(0, 10), 1),
                'wind_speed': round(random.uniform(1, 10), 1),
                'pressure': round(random.uniform(1000, 1020), 1)
            })
        
        return historical_data
    
    def get_air_quality(self, latitude: Optional[float] = None, 
                       longitude: Optional[float] = None) -> Dict[str, Any]:
        """Get air quality data (requires Air Pollution API)"""
        if not self.openweather_api_key or self.openweather_api_key == 'your_openweather_api_key_here':
            logger.warning("OpenWeather API key not configured, returning mock air quality data")
            return self._get_mock_air_quality_data()
        
        lat = latitude or self.default_lat
        lon = longitude or self.default_lon
        
        try:
            url = f"{self.openweather_base_url}/air_pollution"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.openweather_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Air quality index mapping
            aqi_levels = {
                1: "Good",
                2: "Fair", 
                3: "Moderate",
                4: "Poor",
                5: "Very Poor"
            }
            
            air_quality = {
                'aqi': data['list'][0]['main']['aqi'],
                'aqi_level': aqi_levels.get(data['list'][0]['main']['aqi'], "Unknown"),
                'co': data['list'][0]['components']['co'],
                'no': data['list'][0]['components']['no'],
                'no2': data['list'][0]['components']['no2'],
                'o3': data['list'][0]['components']['o3'],
                'pm2_5': data['list'][0]['components']['pm2_5'],
                'pm10': data['list'][0]['components']['pm10'],
                'so2': data['list'][0]['components']['so2'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Air quality data fetched - AQI: {air_quality['aqi']} ({air_quality['aqi_level']})")
            return air_quality
            
        except Exception as e:
            logger.error(f"Error fetching air quality data: {e}")
            return self._get_mock_air_quality_data()
    
    def _get_mock_air_quality_data(self) -> Dict[str, Any]:
        """Generate mock air quality data"""
        import random
        
        aqi = random.randint(1, 5)
        aqi_levels = {
            1: "Good",
            2: "Fair", 
            3: "Moderate",
            4: "Poor",
            5: "Very Poor"
        }
        
        return {
            'aqi': aqi,
            'aqi_level': aqi_levels[aqi],
            'co': round(random.uniform(0, 1000), 1),
            'no': round(random.uniform(0, 50), 1),
            'no2': round(random.uniform(0, 100), 1),
            'o3': round(random.uniform(0, 200), 1),
            'pm2_5': round(random.uniform(0, 50), 1),
            'pm10': round(random.uniform(0, 100), 1),
            'so2': round(random.uniform(0, 50), 1),
            'timestamp': datetime.utcnow().isoformat()
        }


