import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from upstash_redis import Redis

class VercelKVCacheService:
    def __init__(self):
        """Initialize connection to Vercel KV using Upstash Redis"""
        self.kv_url = os.getenv('KV_REST_API_URL')
        self.kv_token = os.getenv('KV_REST_API_TOKEN')
        
        if not self.kv_url or not self.kv_token:
            raise ValueError("KV_REST_API_URL and KV_REST_API_TOKEN must be set as environment variables")
        
        self.redis = Redis(url=self.kv_url, token=self.kv_token)
        self._ensure_cache_structure()
    
    def _ensure_cache_structure(self):
        """Ensure the cache has the required structure"""
        try:
            # Check if cache metadata exists
            metadata = self.redis.get("cache_metadata")
            if not metadata:
                # Initialize cache structure
                initial_metadata = {
                    "version": "2.0",
                    "description": "GPT-powered location cache for verified Reddit locations with place_id support",
                    "created": datetime.now().isoformat(),
                    "format": "Redis-based KV store for MommyNature location data"
                }
                self.redis.set("cache_metadata", json.dumps(initial_metadata))
                
            # Ensure place_id_index exists
            if not self.redis.exists("place_id_index"):
                self.redis.set("place_id_index", json.dumps({}))
                
        except Exception as e:
            print(f"Error initializing cache structure: {e}")
    
    def add_locations(self, city: str, category: str, verified_locations: List[Dict[str, Any]], 
                     source_url: str = None, city_place_id: str = None, city_metadata: Dict[str, Any] = None) -> bool:
        """Add verified locations to KV cache"""
        try:
            # Update place_id index if city_place_id is provided
            if city_place_id:
                place_id_index = json.loads(self.redis.get("place_id_index") or "{}")
                place_id_index[city_place_id] = city
                self.redis.set("place_id_index", json.dumps(place_id_index))
            
            # Store city metadata
            if city_metadata:
                city_metadata_key = f"city_metadata:{city}"
                self.redis.set(city_metadata_key, json.dumps(city_metadata))
            
            # Process and store locations
            locations_key = f"locations:{city}:{category}"
            existing_locations = json.loads(self.redis.get(locations_key) or "[]")
            
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
                        "google_types": google_data.get("types", []),
                        "photo_urls": google_data.get("photo_urls", [])
                    })
                
                existing_locations.append(cache_entry)
            
            # Store updated locations
            self.redis.set(locations_key, json.dumps(existing_locations))
            
            # Update category metadata
            metadata_key = f"metadata:{city}:{category}"
            metadata = {
                "last_updated": datetime.now().isoformat(),
                "source_type": "gpt_extraction",
                "total_locations": len(existing_locations),
                "source_url": source_url
            }
            self.redis.set(metadata_key, json.dumps(metadata))
            
            return True
            
        except Exception as e:
            print(f"Error adding locations to KV cache: {e}")
            return False
    
    def get_locations(self, city: str = None, category: str = None) -> List[Dict[str, Any]]:
        """Get cached locations by city and/or category"""
        try:
            if not city and not category:
                # Return all locations - scan all location keys
                all_locations = []
                keys = self.redis.keys("locations:*")
                for key in keys:
                    locations_data = json.loads(self.redis.get(key) or "[]")
                    all_locations.extend(locations_data)
                return all_locations
            
            if city and category:
                # Get specific city/category combination
                locations_key = f"locations:{city}:{category}"
                return json.loads(self.redis.get(locations_key) or "[]")
            
            if city and not category:
                # Get all locations for a city
                city_locations = []
                keys = self.redis.keys(f"locations:{city}:*")
                for key in keys:
                    locations_data = json.loads(self.redis.get(key) or "[]")
                    city_locations.extend(locations_data)
                return city_locations
            
            return []
            
        except Exception as e:
            print(f"Error getting locations from KV cache: {e}")
            return []
    
    def get_locations_by_place_id(self, place_id: str, category: str = None) -> List[Dict[str, Any]]:
        """Get cached locations by Google place_id"""
        try:
            # Look up city from place_id index
            place_id_index = json.loads(self.redis.get("place_id_index") or "{}")
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
            place_id_index = json.loads(self.redis.get("place_id_index") or "{}")
            city = place_id_index.get(place_id)
            
            if not city:
                return {}
            
            # Get city metadata
            city_metadata_key = f"city_metadata:{city}"
            metadata = self.redis.get(city_metadata_key)
            return json.loads(metadata) if metadata else {}
            
        except Exception as e:
            print(f"Error getting city by place_id: {e}")
            return {}
    
    def get_all_cities_with_metadata(self) -> List[Dict[str, Any]]:
        """Get all cached cities with their metadata"""
        try:
            cities = []
            keys = self.redis.keys("city_metadata:*")
            
            for key in keys:
                city_name = key.replace("city_metadata:", "")
                metadata = json.loads(self.redis.get(key) or "{}")
                if metadata:
                    cities.append({
                        "city_name": city_name,
                        **metadata
                    })
            
            return cities
            
        except Exception as e:
            print(f"Error getting cities with metadata: {e}")
            return []
    
    def update_location_summary(self, place_id: str, category: str, location_name: str, mama_summary: str) -> bool:
        """Update a location's mama summary in the cache"""
        try:
            # Look up city from place_id index
            place_id_index = json.loads(self.redis.get("place_id_index") or "{}")
            city = place_id_index.get(place_id)
            
            if not city:
                print(f"City not found for place_id: {place_id}")
                return False
            
            # Get existing locations
            locations_key = f"locations:{city}:{category}"
            locations = json.loads(self.redis.get(locations_key) or "[]")
            
            # Find and update the location
            for location in locations:
                if location.get("name", "").lower() == location_name.lower():
                    location["mama_summary"] = mama_summary
                    location["summary_updated"] = datetime.now().isoformat()
                    
                    # Save updated locations
                    self.redis.set(locations_key, json.dumps(locations))
                    return True
            
            print(f"Location '{location_name}' not found in {city}/{category}")
            return False
            
        except Exception as e:
            print(f"Error updating location summary: {e}")
            return False
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get summary of cache contents"""
        try:
            # Get all location keys to count cities and locations
            location_keys = self.redis.keys("locations:*")
            cities = set()
            total_locations = 0
            
            for key in location_keys:
                # Extract city from key: "locations:city:category"
                parts = key.split(":")
                if len(parts) >= 2:
                    city = parts[1]
                    cities.add(city)
                    
                    # Count locations in this key
                    locations = json.loads(self.redis.get(key) or "[]")
                    total_locations += len(locations)
            
            summary = {
                "total_cities": len(cities),
                "total_locations": total_locations,
                "cities": {}
            }
            
            # Get detailed info for each city
            for city in cities:
                city_keys = self.redis.keys(f"locations:{city}:*")
                categories = []
                city_total_locations = 0
                
                for city_key in city_keys:
                    # Extract category from key
                    parts = city_key.split(":")
                    if len(parts) >= 3:
                        category = parts[2]
                        categories.append(category)
                        
                        locations = json.loads(self.redis.get(city_key) or "[]")
                        city_total_locations += len(locations)
                
                summary["cities"][city] = {
                    "categories": categories,
                    "total_locations": city_total_locations
                }
            
            return summary
            
        except Exception as e:
            print(f"Error getting cache summary: {e}")
            return {}
    
    def clear_cache(self) -> bool:
        """Clear all cached data"""
        try:
            # Delete all cache-related keys
            keys_to_delete = []
            keys_to_delete.extend(self.redis.keys("locations:*"))
            keys_to_delete.extend(self.redis.keys("city_metadata:*"))
            keys_to_delete.extend(self.redis.keys("metadata:*"))
            keys_to_delete.append("place_id_index")
            keys_to_delete.append("cache_metadata")
            
            for key in keys_to_delete:
                self.redis.delete(key)
            
            # Reinitialize cache structure
            self._ensure_cache_structure()
            return True
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def get_detailed_summary(self) -> Dict[str, Any]:
        """Get detailed summary of cache contents with timestamps and stats"""
        try:
            # Get cache metadata
            cache_metadata = json.loads(self.redis.get("cache_metadata") or "{}")
            
            # Get basic summary
            basic_summary = self.get_cache_summary()
            
            detailed_summary = {
                "cache_info": {
                    "version": cache_metadata.get("version", "unknown"),
                    "created": cache_metadata.get("created", "unknown"),
                    "description": cache_metadata.get("description", ""),
                    "storage_type": "Vercel KV (Upstash Redis)"
                },
                "overview": {
                    "total_cities": basic_summary.get("total_cities", 0),
                    "total_locations": basic_summary.get("total_locations", 0),
                    "total_verified": 0,
                    "total_categories": 0
                },
                "cities": {}
            }
            
            # Get detailed info for each city
            all_categories = set()
            total_verified = 0
            
            for city, city_info in basic_summary.get("cities", {}).items():
                detailed_city_info = {
                    "total_locations": city_info["total_locations"],
                    "categories": {}
                }
                
                for category in city_info["categories"]:
                    all_categories.add(category)
                    
                    # Get locations for this city/category
                    locations_key = f"locations:{city}:{category}"
                    locations = json.loads(self.redis.get(locations_key) or "[]")
                    
                    # Get metadata for this city/category
                    metadata_key = f"metadata:{city}:{category}"
                    metadata = json.loads(self.redis.get(metadata_key) or "{}")
                    
                    verified_count = sum(1 for loc in locations if loc.get("verified", False))
                    total_verified += verified_count
                    
                    detailed_city_info["categories"][category] = {
                        "location_count": len(locations),
                        "verified_count": verified_count,
                        "last_updated": metadata.get("last_updated", "unknown"),
                        "source_type": metadata.get("source_type", "unknown")
                    }
                
                detailed_summary["cities"][city] = detailed_city_info
            
            # Update overview
            detailed_summary["overview"]["total_verified"] = total_verified
            detailed_summary["overview"]["total_categories"] = len(all_categories)
            
            return detailed_summary
            
        except Exception as e:
            print(f"Error getting detailed cache summary: {e}")
            return {}

def main():
    """Test the KV cache service"""
    try:
        cache = VercelKVCacheService()
        summary = cache.get_cache_summary()
        print("Vercel KV Cache Summary:")
        print(json.dumps(summary, indent=2))
    except Exception as e:
        print(f"Error testing KV cache: {e}")

if __name__ == "__main__":
    main()