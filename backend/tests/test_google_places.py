#!/usr/bin/env python3
"""
Simple test for Google Places API to debug the 403 errors
"""

import os
from dotenv import load_dotenv
from google_places import GooglePlacesService

def test_google_places_api():
    # Load environment variables
    load_dotenv()
    
    # Check if API key is loaded
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        print("❌ No GOOGLE_PLACES_API_KEY found in environment")
        return
    
    print(f"✅ API key loaded: {api_key[:20]}...")
    
    # Initialize Google Places service
    places_service = GooglePlacesService()
    
    # Test locations - some that should definitely exist
    test_locations = [
        "Communications Hill San Jose",
        "Mount Hamilton San Jose",
        "Mission Peak Fremont",
        "Rancho San Antonio County Park",
        "Lick Observatory"
    ]
    
    print("\n🔍 Testing Google Places API with known locations:")
    print("=" * 60)
    
    for location in test_locations:
        print(f"\n📍 Testing: {location}")
        
        try:
            result = places_service.search_place(location)
            
            if result:
                print(f"  ✅ Found: {result['name']}")
                print(f"  📍 Address: {result.get('address', 'N/A')}")
                print(f"  ⭐ Rating: {result.get('rating', 'N/A')}")
                print(f"  📝 Reviews: {result.get('review_count', 'N/A')}")
                print(f"  🏷️  Types: {result.get('types', [])}")
                print(f"  🆔 Place ID: {result.get('place_id', 'N/A')}")
            else:
                print(f"  ❌ No results found")
                
        except Exception as e:
            print(f"  💥 Error: {e}")

if __name__ == "__main__":
    test_google_places_api()