#!/usr/bin/env python3
"""
Migration script to add photo_urls to existing locations in cache.

This script:
1. Reads the existing gpt_locations_database.json
2. For each location that has a place_id but no photo_urls
3. Fetches fresh photo data from Google Places API
4. Adds photo_urls to the location entry
5. Saves the updated cache
"""

import json
import os
from google_places import GooglePlacesService
from dotenv import load_dotenv

load_dotenv()

def migrate_photos():
    """Add photo_urls to existing cache locations"""
    
    # Initialize Google Places service
    places_service = GooglePlacesService()
    if not places_service.api_key:
        print("❌ Error: GOOGLE_PLACES_API_KEY not found in .env file")
        return False
    
    # Load existing cache
    cache_file_path = os.path.join(os.path.dirname(__file__), 'gpt_cache', 'gpt_locations_database.json')
    
    if not os.path.exists(cache_file_path):
        print(f"❌ Error: Cache file not found at {cache_file_path}")
        return False
    
    print(f"📖 Loading cache from {cache_file_path}")
    
    with open(cache_file_path, 'r', encoding='utf-8') as f:
        cache_data = json.load(f)
    
    # Track progress
    total_locations = 0
    updated_locations = 0
    skipped_locations = 0
    error_locations = 0
    
    # Iterate through all cities and categories
    for city_name, city_data in cache_data.get("locations", {}).items():
        print(f"\n🏙️ Processing city: {city_name}")
        
        for category, category_data in city_data.items():
            if category == "city_metadata":
                continue
                
            print(f"  📂 Category: {category}")
            locations = category_data.get("locations", [])
            
            for i, location in enumerate(locations):
                total_locations += 1
                location_name = location.get("name", "Unknown")
                place_id = location.get("place_id")
                
                # Skip if no place_id or already has photos
                if not place_id:
                    print(f"    ⏭️ {location_name}: No place_id, skipping")
                    skipped_locations += 1
                    continue
                
                if location.get("photo_urls"):
                    print(f"    ✅ {location_name}: Already has photos ({len(location['photo_urls'])} photos)")
                    skipped_locations += 1
                    continue
                
                # Fetch fresh photos from Google Places
                print(f"    🔍 {location_name}: Fetching photos...")
                
                try:
                    # Use place_id as search query for more accurate results
                    google_data = places_service.search_place(location_name)
                    
                    if google_data and google_data.get('photo_names'):
                        photo_names = google_data.get('photo_names', [])
                        photo_urls = places_service.get_photo_urls(photo_names)
                        
                        # Add photo_urls to location
                        location['photo_urls'] = photo_urls
                        
                        print(f"    ✅ {location_name}: Added {len(photo_urls)} photos")
                        updated_locations += 1
                        
                    else:
                        # No photos found, add empty array
                        location['photo_urls'] = []
                        print(f"    📷 {location_name}: No photos found, added empty array")
                        updated_locations += 1
                        
                except Exception as e:
                    print(f"    ❌ {location_name}: Error fetching photos - {str(e)}")
                    location['photo_urls'] = []  # Add empty array on error
                    error_locations += 1
    
    # Save updated cache
    print(f"\n💾 Saving updated cache...")
    
    # Create backup first
    backup_path = cache_file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    print(f"📋 Backup created at {backup_path}")
    
    # Save updated cache
    with open(cache_file_path, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    # Summary
    print(f"\n✅ Migration completed!")
    print(f"   Total locations processed: {total_locations}")
    print(f"   Updated with photos: {updated_locations}")
    print(f"   Skipped (already had photos/no place_id): {skipped_locations}")
    print(f"   Errors: {error_locations}")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting photo migration...")
    success = migrate_photos()
    
    if success:
        print("\n🎉 Photo migration completed successfully!")
        print("   New locations will automatically include photos.")
        print("   Existing locations now have photo_urls field.")
    else:
        print("\n❌ Photo migration failed!")