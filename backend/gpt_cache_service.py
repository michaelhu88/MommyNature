import json
import os
from typing import Dict, List, Any
from datetime import datetime

class GPTCacheService:
    def __init__(self, cache_file_path: str = None):
        if cache_file_path is None:
            cache_file_path = os.path.join(os.path.dirname(__file__), 'gpt_cache', 'gpt_locations_database.json')
        self.cache_file_path = cache_file_path
        self.cache_data = self.load_cache()
    
    def load_cache(self) -> Dict[str, Any]:
        """Load cache data from JSON file"""
        try:
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "cache_metadata": {
                        "version": "2.0",
                        "description": "GPT-powered location cache for verified Reddit locations with place_id support",
                        "created": datetime.now().isoformat(),
                        "format": "city -> city_metadata + categories -> locations array"
                    },
                    "place_id_index": {},
                    "locations": {}
                }
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {"cache_metadata": {}, "locations": {}}
    
    def save_cache(self) -> bool:
        """Save cache data to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving cache: {e}")
            return False
    
    def add_locations(self, city: str, category: str, verified_locations: List[Dict[str, Any]], 
                     source_url: str = None, city_place_id: str = None, city_metadata: Dict[str, Any] = None) -> bool:
        """Add verified locations to cache with metadata"""
        try:
            # Initialize city if it doesn't exist
            if city not in self.cache_data["locations"]:
                self.cache_data["locations"][city] = {}
                
                # Add city metadata if provided
                if city_metadata:
                    self.cache_data["locations"][city]["city_metadata"] = city_metadata
                    
                    # Update place_id index
                    if "place_id_index" not in self.cache_data:
                        self.cache_data["place_id_index"] = {}
                    if city_place_id:
                        self.cache_data["place_id_index"][city_place_id] = city
            
            # Initialize category if it doesn't exist
            if category not in self.cache_data["locations"][city]:
                self.cache_data["locations"][city][category] = {
                    "locations": [],
                    "metadata": {
                        "last_updated": datetime.now().isoformat(),
                        "source_type": "gpt_extraction",
                        "total_locations": 0
                    }
                }
            
            # Add new locations
            category_data = self.cache_data["locations"][city][category]
            
            for location in verified_locations:
                # Create cache entry from verified location
                cache_entry = {
                    "name": location["name"],
                    "verified": location["verified"],
                    "city": city,
                    "category": category,
                    "cached_at": datetime.now().isoformat(),
                    "source_url": source_url
                }
                
                # Add Google Places data if available
                if location.get("google_data"):
                    google_data = location["google_data"]
                    cache_entry.update({
                        "canonical_name": google_data.get("canonical_name"),
                        "google_rating": google_data.get("rating"),
                        "google_reviews": google_data.get("review_count"),
                        "address": google_data.get("address"),
                        "place_id": google_data.get("place_id"),
                        "google_types": google_data.get("types", [])
                    })
                
                category_data["locations"].append(cache_entry)
            
            # Update metadata
            category_data["metadata"]["last_updated"] = datetime.now().isoformat()
            category_data["metadata"]["total_locations"] = len(category_data["locations"])
            if source_url:
                category_data["metadata"]["source_url"] = source_url
            
            # Save to file
            return self.save_cache()
            
        except Exception as e:
            print(f"Error adding locations to cache: {e}")
            return False
    
    def get_locations(self, city: str = None, category: str = None) -> List[Dict[str, Any]]:
        """Get cached locations by city and/or category"""
        try:
            if not city and not category:
                # Return all locations
                all_locations = []
                for city_data in self.cache_data["locations"].values():
                    for category_data in city_data.values():
                        all_locations.extend(category_data["locations"])
                return all_locations
            
            if city and city in self.cache_data["locations"]:
                if category and category in self.cache_data["locations"][city]:
                    return self.cache_data["locations"][city][category]["locations"]
                elif not category:
                    # Return all locations for the city
                    city_locations = []
                    for category_data in self.cache_data["locations"][city].values():
                        city_locations.extend(category_data["locations"])
                    return city_locations
            
            return []
            
        except Exception as e:
            print(f"Error getting locations from cache: {e}")
            return []
    
    def get_locations_by_place_id(self, place_id: str, category: str = None) -> List[Dict[str, Any]]:
        """Get cached locations by Google place_id"""
        try:
            # Look up city from place_id index
            place_id_index = self.cache_data.get("place_id_index", {})
            city = place_id_index.get(place_id)
            
            if not city:
                return []
            
            # Use existing get_locations method
            return self.get_locations(city=city, category=category)
            
        except Exception as e:
            print(f"Error getting locations by place_id: {e}")
            return []
    
    def get_city_by_place_id(self, place_id: str) -> Dict[str, Any]:
        """Get city metadata by Google place_id"""
        try:
            # Look up city from place_id index
            place_id_index = self.cache_data.get("place_id_index", {})
            city = place_id_index.get(place_id)
            
            if not city or city not in self.cache_data["locations"]:
                return {}
            
            city_data = self.cache_data["locations"][city]
            return city_data.get("city_metadata", {})
            
        except Exception as e:
            print(f"Error getting city by place_id: {e}")
            return {}
    
    def get_all_cities_with_metadata(self) -> List[Dict[str, Any]]:
        """Get all cached cities with their metadata"""
        try:
            cities = []
            for city_name, city_data in self.cache_data["locations"].items():
                city_metadata = city_data.get("city_metadata", {})
                if city_metadata:
                    cities.append({
                        "city_name": city_name,
                        **city_metadata
                    })
            return cities
        except Exception as e:
            print(f"Error getting cities with metadata: {e}")
            return []
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get summary of cache contents"""
        try:
            summary = {
                "total_cities": len(self.cache_data["locations"]),
                "cities": {}
            }
            
            for city, city_data in self.cache_data["locations"].items():
                summary["cities"][city] = {
                    "categories": list(city_data.keys()),
                    "total_locations": sum(len(cat_data["locations"]) for cat_data in city_data.values())
                }
            
            return summary
            
        except Exception as e:
            print(f"Error getting cache summary: {e}")
            return {}

    def clear_cache(self) -> bool:
        """Clear all cached data and reset to empty state"""
        try:
            self.cache_data = {
                "cache_metadata": {
                    "version": "2.0",
                    "description": "GPT-powered location cache for verified Reddit locations with place_id support",
                    "created": datetime.now().isoformat(),
                    "format": "city -> city_metadata + categories -> locations array"
                },
                "place_id_index": {},
                "locations": {}
            }
            return self.save_cache()
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False

    def get_detailed_summary(self) -> Dict[str, Any]:
        """Get detailed summary of cache contents with timestamps and stats"""
        try:
            total_locations = 0
            total_verified = 0
            
            detailed_summary = {
                "cache_info": {
                    "version": self.cache_data.get("cache_metadata", {}).get("version", "unknown"),
                    "created": self.cache_data.get("cache_metadata", {}).get("created", "unknown"),
                    "cache_file": self.cache_file_path
                },
                "overview": {
                    "total_cities": len(self.cache_data["locations"]),
                    "total_locations": 0,
                    "total_verified": 0,
                    "total_categories": 0
                },
                "cities": {}
            }
            
            all_categories = set()
            
            for city, city_data in self.cache_data["locations"].items():
                city_info = {
                    "total_locations": 0,
                    "categories": {}
                }
                
                for category, category_data in city_data.items():
                    all_categories.add(category)
                    locations = category_data.get("locations", [])
                    metadata = category_data.get("metadata", {})
                    
                    verified_count = sum(1 for loc in locations if loc.get("verified", False))
                    
                    city_info["categories"][category] = {
                        "location_count": len(locations),
                        "verified_count": verified_count,
                        "last_updated": metadata.get("last_updated", "unknown"),
                        "source_type": metadata.get("source_type", "unknown")
                    }
                    
                    city_info["total_locations"] += len(locations)
                    total_locations += len(locations)
                    total_verified += verified_count
                
                detailed_summary["cities"][city] = city_info
            
            # Update overview
            detailed_summary["overview"]["total_locations"] = total_locations
            detailed_summary["overview"]["total_verified"] = total_verified
            detailed_summary["overview"]["total_categories"] = len(all_categories)
            
            return detailed_summary
            
        except Exception as e:
            print(f"Error getting detailed cache summary: {e}")
            return {}

def main():
    """Simple test/demo of the cache service"""
    cache = GPTCacheService()
    summary = cache.get_cache_summary()
    print("GPT Cache Summary:")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()