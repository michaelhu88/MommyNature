#!/usr/bin/env python3
"""
Migration script to transfer data from JSON cache to Vercel KV
"""
import json
import os
from datetime import datetime
from gpt_cache_service import GPTCacheService
from vercel_kv_cache_service import VercelKVCacheService

def migrate_json_to_kv():
    """Migrate all data from JSON cache to Vercel KV"""
    print("🔄 Starting migration from JSON to Vercel KV...")
    
    try:
        # Initialize both services
        json_cache = GPTCacheService()
        kv_cache = VercelKVCacheService()
        
        # Get summary of JSON cache
        json_summary = json_cache.get_detailed_summary()
        print(f"\n📊 JSON Cache Summary:")
        print(f"   Total cities: {json_summary['overview']['total_cities']}")
        print(f"   Total locations: {json_summary['overview']['total_locations']}")
        print(f"   Total verified: {json_summary['overview']['total_verified']}")
        
        # Clear KV cache to start fresh
        print("\n🧹 Clearing existing KV cache...")
        kv_cache.clear_cache()
        
        # Migrate place_id index
        print("\n🗂️ Migrating place_id index...")
        if hasattr(json_cache, 'cache_data') and 'place_id_index' in json_cache.cache_data:
            place_id_index = json_cache.cache_data['place_id_index']
            # Set the place_id index directly in KV
            kv_cache.redis.set("place_id_index", json.dumps(place_id_index))
            print(f"   Migrated {len(place_id_index)} place_id mappings")
        
        # Migrate cache metadata
        print("\n📋 Migrating cache metadata...")
        if hasattr(json_cache, 'cache_data') and 'cache_metadata' in json_cache.cache_data:
            metadata = json_cache.cache_data['cache_metadata'].copy()
            metadata['migrated_to_kv'] = datetime.now().isoformat()
            metadata['original_storage'] = 'JSON file'
            metadata['new_storage'] = 'Vercel KV (Upstash Redis)'
            kv_cache.redis.set("cache_metadata", json.dumps(metadata))
            print("   Cache metadata migrated")
        
        # Migrate cities and locations
        migrated_cities = 0
        migrated_locations = 0
        
        for city_name, city_info in json_summary['cities'].items():
            print(f"\n🏙️ Migrating city: {city_name}")
            
            # Get city metadata from JSON cache
            if hasattr(json_cache, 'cache_data') and city_name in json_cache.cache_data.get('locations', {}):
                city_data = json_cache.cache_data['locations'][city_name]
                
                # Migrate city metadata
                if 'city_metadata' in city_data:
                    city_metadata = city_data['city_metadata']
                    kv_cache.redis.set(f"city_metadata:{city_name}", json.dumps(city_metadata))
                    print(f"   City metadata: ✅")
                
                # Migrate each category
                for category in city_info['categories']:
                    if category == 'city_metadata':  # Skip metadata, already handled
                        continue
                        
                    print(f"   Category: {category}")
                    
                    if category in city_data:
                        category_data = city_data[category]
                        locations = category_data.get('locations', [])
                        
                        if locations:
                            # Store locations in KV
                            locations_key = f"locations:{city_name}:{category}"
                            kv_cache.redis.set(locations_key, json.dumps(locations))
                            
                            # Store category metadata
                            if 'metadata' in category_data:
                                metadata_key = f"metadata:{city_name}:{category}"
                                kv_cache.redis.set(metadata_key, json.dumps(category_data['metadata']))
                            
                            migrated_locations += len(locations)
                            print(f"     ✅ {len(locations)} locations migrated")
                        else:
                            print(f"     ⚠️ No locations found")
            
            migrated_cities += 1
        
        # Verify migration
        print(f"\n✅ Migration completed!")
        print(f"   Cities migrated: {migrated_cities}")
        print(f"   Locations migrated: {migrated_locations}")
        
        # Get KV cache summary to verify
        print(f"\n📊 Verifying KV Cache...")
        kv_summary = kv_cache.get_detailed_summary()
        print(f"   KV Total cities: {kv_summary['overview']['total_cities']}")
        print(f"   KV Total locations: {kv_summary['overview']['total_locations']}")
        print(f"   KV Total verified: {kv_summary['overview']['total_verified']}")
        
        # Compare counts
        json_total = json_summary['overview']['total_locations']
        kv_total = kv_summary['overview']['total_locations']
        
        if json_total == kv_total:
            print(f"\n🎉 SUCCESS: All {json_total} locations migrated successfully!")
        else:
            print(f"\n⚠️ WARNING: Location count mismatch!")
            print(f"   JSON cache had: {json_total} locations")
            print(f"   KV cache has: {kv_total} locations")
            
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_kv_connection():
    """Test the KV connection before migration"""
    print("🔍 Testing KV connection...")
    try:
        kv_cache = VercelKVCacheService()
        # Try to get cache metadata
        metadata = kv_cache.redis.get("cache_metadata")
        print("✅ KV connection successful")
        return True
    except Exception as e:
        print(f"❌ KV connection failed: {e}")
        return False

def main():
    print("🚀 MommyNature JSON to Vercel KV Migration")
    print("=" * 50)
    
    # Check environment variables
    kv_url = os.getenv('KV_REST_API_URL')
    kv_token = os.getenv('KV_REST_API_TOKEN')
    
    if not kv_url or not kv_token:
        print("❌ Missing required environment variables:")
        print("   KV_REST_API_URL and KV_REST_API_TOKEN must be set")
        print("\nPlease set these environment variables and try again.")
        return
    
    print(f"KV URL: {kv_url}")
    print(f"KV Token: {kv_token[:20]}...")
    
    # Test connection
    if not test_kv_connection():
        print("❌ Cannot connect to Vercel KV. Please check your credentials.")
        return
    
    # Run migration
    if migrate_json_to_kv():
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update your main.py to use VercelKVCacheService")
        print("2. Deploy to Railway with the KV environment variables")
        print("3. Test your application")
    else:
        print("\n❌ Migration failed. Please check the errors above.")

if __name__ == "__main__":
    main()