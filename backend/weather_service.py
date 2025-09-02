import requests
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

load_dotenv()

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        if not self.api_key:
            print("Warning: OPENWEATHER_API_KEY not found in .env file")
            self.api_key = None
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_coordinates_from_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Get latitude and longitude from address using OpenWeatherMap Geocoding API"""
        if not self.api_key:
            return None
        
        try:
            geocode_url = "http://api.openweathermap.org/geo/1.0/direct"
            params = {
                'q': address,
                'limit': 1,
                'appid': self.api_key
            }
            
            response = requests.get(geocode_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return (data[0]['lat'], data[0]['lon'])
            else:
                print(f"Geocoding error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting coordinates: {e}")
            return None
    
    def get_current_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """Get current weather for given coordinates"""
        if not self.api_key:
            return None
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'  # Fahrenheit for US users
            }
            
            response = requests.get(f"{self.base_url}/weather", params=params)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': round(data['main']['temp']),
                    'feels_like': round(data['main']['feels_like']),
                    'humidity': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'main': data['weather'][0]['main'],
                    'wind_speed': data['wind']['speed'],
                    'visibility': data.get('visibility', 0) / 1000,  # Convert to miles
                    'timestamp': datetime.now().isoformat()
                }
            else:
                print(f"Weather API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting current weather: {e}")
            return None
    
    def get_forecast(self, lat: float, lon: float, days: int = 5) -> Optional[List[Dict]]:
        """Get weather forecast for given coordinates (up to 5 days)"""
        if not self.api_key:
            return None
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'  # Fahrenheit for US users
            }
            
            response = requests.get(f"{self.base_url}/forecast", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Group forecasts by day
                daily_forecasts = {}
                
                for forecast in data['list'][:days*8]:  # 8 forecasts per day (every 3 hours)
                    date = datetime.fromtimestamp(forecast['dt']).date()
                    
                    if date not in daily_forecasts:
                        daily_forecasts[date] = {
                            'date': date.isoformat(),
                            'temps': [],
                            'descriptions': [],
                            'humidity': [],
                            'wind_speed': [],
                            'main_conditions': []
                        }
                    
                    daily_forecasts[date]['temps'].append(forecast['main']['temp'])
                    daily_forecasts[date]['descriptions'].append(forecast['weather'][0]['description'])
                    daily_forecasts[date]['humidity'].append(forecast['main']['humidity'])
                    daily_forecasts[date]['wind_speed'].append(forecast['wind']['speed'])
                    daily_forecasts[date]['main_conditions'].append(forecast['weather'][0]['main'])
                
                # Process daily summaries
                processed_forecasts = []
                for date, day_data in daily_forecasts.items():
                    processed_forecasts.append({
                        'date': day_data['date'],
                        'high_temp': round(max(day_data['temps'])),
                        'low_temp': round(min(day_data['temps'])),
                        'avg_temp': round(sum(day_data['temps']) / len(day_data['temps'])),
                        'description': max(set(day_data['descriptions']), key=day_data['descriptions'].count),
                        'main': max(set(day_data['main_conditions']), key=day_data['main_conditions'].count),
                        'avg_humidity': round(sum(day_data['humidity']) / len(day_data['humidity'])),
                        'avg_wind_speed': round(sum(day_data['wind_speed']) / len(day_data['wind_speed']), 1)
                    })
                
                return processed_forecasts[:days]
            else:
                print(f"Forecast API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting forecast: {e}")
            return None
    
    def get_weather_for_date(self, lat: float, lon: float, target_date: str) -> Optional[Dict]:
        """Get weather for a specific date (within 5 days)"""
        try:
            target = datetime.fromisoformat(target_date).date()
            today = datetime.now().date()
            days_from_now = (target - today).days
            
            if days_from_now < 0:
                return {
                    'error': 'past_date',
                    'message': 'Cannot get weather for past dates'
                }
            elif days_from_now > 5:
                return {
                    'error': 'too_far_future',
                    'message': 'Weather forecast only available for next 5 days'
                }
            
            # Get current weather for today
            if days_from_now == 0:
                return self.get_current_weather(lat, lon)
            
            # Get forecast for future dates
            forecasts = self.get_forecast(lat, lon, days=6)
            
            if forecasts:
                for forecast in forecasts:
                    if forecast['date'] == target_date:
                        return forecast
                        
            return None
            
        except Exception as e:
            print(f"Error getting weather for specific date: {e}")
            return None
    
    def get_weather_for_location_and_date(self, address: str, target_date: str) -> Optional[Dict]:
        """Complete workflow: get weather for location address and specific date"""
        # Get coordinates
        coords = self.get_coordinates_from_address(address)
        if not coords:
            return {
                'error': 'location_not_found',
                'message': f'Could not find coordinates for location: {address}'
            }
        
        lat, lon = coords
        
        # Get weather for the date
        weather = self.get_weather_for_date(lat, lon, target_date)
        
        if weather:
            weather['location'] = address
            weather['coordinates'] = {'lat': lat, 'lon': lon}
            
        return weather

# Example usage and testing
if __name__ == "__main__":
    weather_service = WeatherService()
    
    # Test location
    test_address = "Mount Umunhum, California"
    test_date = (datetime.now() + timedelta(days=2)).date().isoformat()
    
    print("Testing Weather Service...")
    print("=" * 50)
    
    if weather_service.api_key:
        result = weather_service.get_weather_for_location_and_date(test_address, test_date)
        if result:
            print(f"Location: {test_address}")
            print(f"Date: {test_date}")
            print(f"Weather: {json.dumps(result, indent=2)}")
        else:
            print("Failed to get weather data")
    else:
        print("OpenWeatherMap API key not available")