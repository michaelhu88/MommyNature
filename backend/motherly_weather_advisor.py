import openai
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class MotherlyWeatherAdvisor:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found in .env file")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_motherly_weather_advice(self, location_data: Dict, weather_data: Dict, visit_date: str) -> Optional[str]:
        """
        Generate warm, motherly weather advice and clothing recommendations
        
        Args:
            location_data: Dict with location name, type, etc.
            weather_data: Dict with temperature, conditions, etc.
            visit_date: ISO date string for the visit
        """
        if not self.client:
            return self._create_fallback_advice(location_data, weather_data, visit_date)
        
        # Extract key information
        location_name = location_data.get('name', 'this beautiful spot')
        location_type = self._infer_location_type(location_data)
        
        # Handle weather data errors
        if weather_data.get('error'):
            return self._handle_weather_error(weather_data, location_name, visit_date)
        
        # Extract weather information
        temp = weather_data.get('temperature') or weather_data.get('avg_temp', 70)
        high_temp = weather_data.get('high_temp', temp)
        low_temp = weather_data.get('low_temp', temp)
        description = weather_data.get('description', 'partly cloudy')
        main_condition = weather_data.get('main', 'Clear')
        humidity = weather_data.get('humidity') or weather_data.get('avg_humidity', 50)
        wind_speed = weather_data.get('wind_speed') or weather_data.get('avg_wind_speed', 5)
        
        # Format the date for natural language
        try:
            date_obj = datetime.fromisoformat(visit_date)
            formatted_date = date_obj.strftime("%A, %B %d")
        except:
            formatted_date = visit_date
        
        # Build context for the AI prompt
        weather_context = f"""
Location: {location_name} ({location_type})
Visit Date: {formatted_date}
Temperature: {temp}°F (High: {high_temp}°F, Low: {low_temp}°F)
Conditions: {description}
Main Weather: {main_condition}
Humidity: {humidity}%
Wind Speed: {wind_speed} mph
"""
        
        # Create the motherly advice prompt
        prompt = f"""You are a caring, experienced mom giving weather and clothing advice to someone visiting a nature location. 

Write a warm, practical, and nurturing 2-3 sentence weather advisory. Your tone should be:
- Motherly and caring (like talking to your own child)
- Practical with specific clothing recommendations
- Consider the outdoor activity type
- Include gentle reminders about safety/comfort
- Enthusiastic but realistic about conditions

Weather Information:
{weather_context}

Write advice that sounds like a loving mom who wants her child to be comfortable and safe on their outdoor adventure. Start with something like "Oh honey," or "Sweetie," and include specific clothing suggestions based on the weather."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a caring, nurturing mom who gives excellent outdoor weather advice."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            advice = response.choices[0].message.content.strip()
            return advice
            
        except Exception as e:
            print(f"Error generating weather advice for {location_name}: {e}")
            return self._create_fallback_advice(location_data, weather_data, visit_date)
    
    def _infer_location_type(self, location_data: Dict) -> str:
        """Infer the type of outdoor activity from location data"""
        location_name = location_data.get('name', '').lower()
        google_types = location_data.get('google_types', [])
        category = location_data.get('category', '')
        
        if 'park' in location_name or 'park' in google_types:
            return 'park'
        elif 'mount' in location_name or 'peak' in location_name or 'mountain' in location_name:
            return 'mountain/hiking area'
        elif 'trail' in location_name or 'hiking' in category:
            return 'hiking trail'
        elif 'beach' in location_name or 'coast' in location_name:
            return 'beach/coastal area'
        elif 'viewpoint' in category:
            return 'scenic viewpoint'
        elif 'dog' in category:
            return 'dog park'
        else:
            return 'outdoor recreation area'
    
    def _handle_weather_error(self, weather_data: Dict, location_name: str, visit_date: str) -> str:
        """Handle weather API errors with motherly advice"""
        error_type = weather_data.get('error', 'unknown')
        
        if error_type == 'past_date':
            return f"Oh sweetie, I can't check the weather for dates that have already passed! But I hope you had a wonderful time at {location_name}. For your next adventure, try checking the weather a few days ahead so I can give you my best advice! 💕"
        
        elif error_type == 'too_far_future':
            try:
                date_obj = datetime.fromisoformat(visit_date)
                month = date_obj.strftime("%B")
                return f"Honey, that's quite a ways out - I can only see the weather about 5 days ahead! But for {month} visits to {location_name}, I'd generally recommend dressing in layers and checking the weather again closer to your trip. Nature can be unpredictable, so it's always good to be prepared! 🌤️"
            except:
                return f"That's quite far in the future, sweetie! I can only check weather about 5 days ahead. For {location_name}, I'd recommend checking back closer to your visit date so I can give you the most accurate advice! 💝"
        
        else:
            return f"Oh dear, I'm having trouble getting the weather forecast right now. But don't worry! For any outdoor adventure to {location_name}, I always recommend dressing in layers, bringing a water bottle, and checking the weather again before you head out. Stay safe and have fun! 🌈"
    
    def _create_fallback_advice(self, location_data: Dict, weather_data: Dict, visit_date: str) -> str:
        """Create basic motherly advice when GPT is not available"""
        location_name = location_data.get('name', 'your outdoor destination')
        temp = weather_data.get('temperature') or weather_data.get('avg_temp')
        
        if temp:
            if temp >= 75:
                return f"Oh honey, it looks like it'll be a warm {temp}°F for your visit to {location_name}! I'd recommend light, breathable clothing, a sun hat, and plenty of water. Don't forget the sunscreen - mama's orders! ☀️"
            elif temp >= 60:
                return f"Perfect weather at {temp}°F for {location_name}, sweetie! I'd pack a light jacket just in case, comfortable walking shoes, and maybe a small backpack with snacks and water. You're going to have such a lovely time! 🌤️"
            else:
                return f"It'll be a bit chilly at {temp}°F, honey! Bundle up with layers you can adjust, a warm jacket, and don't forget gloves and a cozy hat. {location_name} will be beautiful, just stay warm out there! 🧥"
        else:
            return f"I can't get the exact weather right now, but for any trip to {location_name}, I always say: dress in layers, bring water, wear good shoes, and check the forecast before you go. Have a wonderful and safe adventure, sweetie! 💕"

# Example usage and testing
if __name__ == "__main__":
    advisor = MotherlyWeatherAdvisor()
    
    # Test location data
    test_location = {
        'name': 'Mount Umunhum',
        'category': 'viewpoints',
        'google_types': ['natural_feature', 'establishment']
    }
    
    # Test weather data
    test_weather = {
        'temperature': 68,
        'high_temp': 72,
        'low_temp': 55,
        'description': 'partly cloudy',
        'main': 'Clouds',
        'humidity': 65,
        'wind_speed': 8
    }
    
    test_date = "2025-08-30"
    
    print("Testing Motherly Weather Advisor...")
    print("=" * 50)
    
    if advisor.client:
        advice = advisor.generate_motherly_weather_advice(test_location, test_weather, test_date)
        print(f"Location: {test_location['name']}")
        print(f"Weather: {test_weather['temperature']}°F, {test_weather['description']}")
        print(f"Mama's Advice: {advice}")
    else:
        print("OpenAI API key not available - using fallback advice")
        fallback = advisor._create_fallback_advice(test_location, test_weather, test_date)
        print(f"Fallback Advice: {fallback}")