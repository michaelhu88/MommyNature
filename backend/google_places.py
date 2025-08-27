import requests
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import time

load_dotenv()

class GooglePlacesService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.api_key:
            print("Warning: GOOGLE_PLACES_API_KEY not found in .env file")
            self.api_key = None
        self.base_url = "https://places.googleapis.com/v1/places"
    
    def search_place(self, location_name: str, location_type: str = None) -> Optional[Dict]:
        """Search for a place using Google Places API (New)"""
        if not self.api_key:
            return None
        
        try:
            # Rate limiting: 1 request per second to avoid 429 errors
            time.sleep(1)
            
            # Enhance query with location type for better results
            query = location_name
            if location_type:
                query += f" {location_type}"
            
            # Use the new Places API (New) search endpoint
            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'places.displayName,places.rating,places.userRatingCount,places.types,places.formattedAddress,places.shortFormattedAddress,places.id,places.photos'
            }
            
            data = {
                "textQuery": query,
                "maxResultCount": 1
            }
            
            response = requests.post(
                f"{self.base_url}:searchText",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'places' in result and result['places']:
                    place = result['places'][0]
                    
                    # Debug: Print the full place response to understand structure
                    print(f"🔍 DEBUG: Place data for '{location_name}':")
                    print(f"  Photos field present: {'photos' in place}")
                    if 'photos' in place:
                        print(f"  Number of photos: {len(place['photos'])}")
                        print(f"  Sample photo data: {place['photos'][:1] if place['photos'] else 'None'}")
                    
                    # Extract photo names
                    photo_names = []
                    if 'photos' in place and place['photos']:
                        for photo in place['photos'][:3]:  # Get up to 3 photos
                            if 'name' in photo:
                                photo_names.append(photo['name'])
                                print(f"  📸 Found photo: {photo['name']}")
                    
                    print(f"  Total photos extracted: {len(photo_names)}")
                    
                    return {
                        'name': place.get('displayName', {}).get('text', location_name),
                        'rating': place.get('rating'),
                        'review_count': place.get('userRatingCount', 0),
                        'types': place.get('types', []),
                        'address': place.get('formattedAddress', ''),
                        'vicinity': place.get('shortFormattedAddress', ''),
                        'place_id': place.get('id', ''),
                        'photo_names': photo_names
                    }
            elif response.status_code == 429:
                print(f"Rate limit hit for '{location_name}' - waiting 2 seconds...")
                time.sleep(2)
                return None
            else:
                print(f"Places API error for '{location_name}': {response.status_code}")
                print(f"Response: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"Error searching for place '{location_name}': {e}")
            return None
    
    def get_photo_url(self, photo_name: str, max_width: int = 800) -> str:
        """Convert photo name to actual photo URL"""
        if not self.api_key or not photo_name:
            return ""
        
        # For the new Places API, photo names are in format "places/{place_id}/photos/{photo_id}"
        # Construct the correct URL for the Places Photo API
        return f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx={max_width}&key={self.api_key}"
    
    def get_photo_urls(self, photo_names: List[str], max_width: int = 800) -> List[str]:
        """Convert list of photo names to photo URLs"""
        print(f"🔗 BACKEND DEBUG: Converting {len(photo_names)} photo names to URLs")
        print(f"  Input photo_names: {photo_names}")
        
        urls = []
        for i, name in enumerate(photo_names):
            if name:
                url = self.get_photo_url(name, max_width)
                urls.append(url)
                print(f"  Photo {i+1}: {url}")
            else:
                print(f"  Photo {i+1}: SKIPPED (empty name)")
        
        print(f"  Total URLs generated: {len(urls)}")
        return urls
    
    def calculate_google_score(self, rating: float, review_count: int) -> float:
        """
        Calculate a normalized Google Places score (0-10)
        
        Scoring logic:
        - High rating + many reviews = best score
        - High rating + few reviews = good score  
        - Medium rating + many reviews = decent score
        - Low rating or few reviews = lower score
        """
        if not rating or review_count == 0:
            return 0.0
        
        # Normalize rating (Google uses 1-5, we want 0-10)
        rating_score = (rating - 1) * 2.5  # Convert 1-5 to 0-10
        
        # Review count confidence factor
        # More reviews = higher confidence in the rating
        if review_count >= 500:
            confidence = 1.0      # Very confident
        elif review_count >= 100:
            confidence = 0.9      # High confidence  
        elif review_count >= 50:
            confidence = 0.8      # Good confidence
        elif review_count >= 20:
            confidence = 0.7      # Moderate confidence
        elif review_count >= 10:
            confidence = 0.6      # Some confidence
        else:
            confidence = 0.4      # Low confidence
        
        # Final score combines rating quality with review confidence
        google_score = rating_score * confidence
        
        return round(google_score, 1)
    
    def enhance_locations_with_google_data(self, locations: List[Dict]) -> List[Dict]:
        """Enhance location data with Google Places information"""
        enhanced_locations = []
        
        for location in locations:
            # Add delay to respect API rate limits
            time.sleep(0.1)
            
            location_name = location['name']
            
            # Try to determine location type from name
            location_type = self._guess_location_type(location_name)
            
            # Search Google Places
            google_data = self.search_place(location_name, location_type)
            
            # Calculate enhanced score
            enhanced_location = location.copy()
            
            if google_data:
                google_score = self.calculate_google_score(
                    google_data.get('rating', 0),
                    google_data.get('review_count', 0)
                )
                
                # Combine Reddit score with Google score
                reddit_score = location['score']
                
                # Weighted combination: 40% Reddit + 60% Google
                # Google gets higher weight since it's more reliable
                combined_score = (reddit_score * 0.4) + (google_score * 0.6)
                
                enhanced_location.update({
                    'score': round(combined_score, 1),
                    'reddit_score': reddit_score,
                    'google_score': google_score,
                    'google_rating': google_data.get('rating'),
                    'google_reviews': google_data.get('review_count', 0),
                    'google_types': google_data.get('types', []),
                    'address': google_data.get('address', ''),
                    'place_id': google_data.get('place_id', ''),
                    'photo_names': google_data.get('photo_names', []),
                    'photo_urls': self.get_photo_urls(google_data.get('photo_names', []))
                })
            else:
                # No Google data found, keep original Reddit score but mark it
                enhanced_location.update({
                    'score': location['score'] * 0.7,  # Penalize slightly for no Google data
                    'reddit_score': location['score'],
                    'google_score': 0.0,
                    'google_rating': None,
                    'google_reviews': 0,
                    'google_types': [],
                    'address': '',
                    'place_id': '',
                    'photo_names': [],
                    'photo_urls': []
                })
            
            enhanced_locations.append(enhanced_location)
        
        # Re-sort by new combined score
        enhanced_locations.sort(key=lambda x: x['score'], reverse=True)
        
        return enhanced_locations
    
    def _guess_location_type(self, location_name: str) -> Optional[str]:
        """Guess the type of location based on name keywords"""
        name_lower = location_name.lower()
        
        if any(word in name_lower for word in ['park', 'preserve', 'reserve']):
            return 'park'
        elif any(word in name_lower for word in ['trail', 'hike', 'hiking']):
            return 'hiking trail'
        elif any(word in name_lower for word in ['beach', 'shore', 'coast']):
            return 'beach'
        elif any(word in name_lower for word in ['mountain', 'mount', 'mt', 'peak']):
            return 'mountain'
        elif any(word in name_lower for word in ['lake', 'pond', 'reservoir']):
            return 'lake'
        elif any(word in name_lower for word in ['waterfall', 'falls']):
            return 'waterfall'
        elif any(word in name_lower for word in ['viewpoint', 'overlook', 'vista']):
            return 'scenic viewpoint'
        else:
            return 'tourist attraction'

# Example usage and testing
if __name__ == "__main__":
    places_service = GooglePlacesService()
    
    # Test locations
    test_locations = [
        {'name': 'Sierra Vista Open Space', 'score': 12.7, 'mentions': 4, 'sources': ['test']},
        {'name': 'Communications Hill', 'score': 8.6, 'mentions': 4, 'sources': ['test']},
        {'name': 'Mt. Hamilton', 'score': 9.3, 'mentions': 2, 'sources': ['test']}
    ]
    
    print("Testing Google Places integration...")
    enhanced = places_service.enhance_locations_with_google_data(test_locations)
    
    for location in enhanced:
        print(f"\n{location['name']}:")
        print(f"  Combined Score: {location['score']}")
        print(f"  Reddit Score: {location['reddit_score']}")
        print(f"  Google Score: {location['google_score']}")
        if location['google_rating']:
            print(f"  Google Rating: {location['google_rating']}/5 ({location['google_reviews']} reviews)")
        print(f"  Address: {location.get('address', 'Not found')}")