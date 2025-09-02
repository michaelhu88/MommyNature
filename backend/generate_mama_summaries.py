#!/usr/bin/env python3
"""
Generate Mama Summaries for Existing Cached Locations

This utility script generates nurturing "Mama Knows Best" summaries for all existing
locations in the cache that don't already have summaries.

Usage:
    python3 generate_mama_summaries.py [--dry-run] [--city CITY] [--category CATEGORY]

Options:
    --dry-run: Show what would be generated without actually saving summaries
    --city: Generate summaries only for a specific city  
    --category: Generate summaries only for a specific category
"""

import argparse
import asyncio
from typing import Dict, List, Any
from vercel_kv_cache_service import VercelKVCacheService
from gpt_summary import GPTSummaryService

class MamaSummaryGenerator:
    def __init__(self):
        self.cache_service = VercelKVCacheService()
        self.summary_service = GPTSummaryService()
        self.generated_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def get_locations_without_summaries(self, city_filter: str = None, category_filter: str = None) -> List[Dict[str, Any]]:
        """Get all cached locations that don't have mama summaries"""
        locations_to_process = []
        
        for city, city_data in self.cache_service.cache_data.get("locations", {}).items():
            if city_filter and city != city_filter:
                continue
            
            # Skip city_metadata entries
            if city == "city_metadata":
                continue
                
            for category, category_data in city_data.items():
                if category == "city_metadata":
                    continue
                    
                if category_filter and category != category_filter:
                    continue
                
                locations = category_data.get("locations", [])
                for location in locations:
                    if not location.get("mama_summary"):  # No summary yet
                        locations_to_process.append({
                            "city": city,
                            "category": category,
                            "location": location,
                            "place_id": city_data.get("city_metadata", {}).get("place_id")
                        })
        
        return locations_to_process
    
    def generate_summary_for_location(self, location_info: Dict[str, Any]) -> str:
        """Generate mama summary for a single location"""
        location = location_info["location"]
        
        try:
            if not self.summary_service.client:
                raise Exception("OpenAI API not available")
            
            # Generate summary using existing GPT service
            summary = self.summary_service.generate_location_summary(location)
            
            if summary:
                self.generated_count += 1
                return summary
            else:
                raise Exception("Summary generation returned None")
                
        except Exception as e:
            print(f"❌ Error generating summary for {location.get('name', 'Unknown')}: {e}")
            self.error_count += 1
            return None
    
    def update_location_with_summary(self, location_info: Dict[str, Any], summary: str) -> bool:
        """Update the location in cache with the generated summary"""
        try:
            place_id = location_info.get("place_id")
            category = location_info["category"]
            location_name = location_info["location"].get("name")
            
            if place_id:
                return self.cache_service.update_location_summary(
                    place_id, category, location_name, summary
                )
            else:
                print(f"⚠️  No place_id for {location_name}, cannot update cache")
                return False
                
        except Exception as e:
            print(f"❌ Error updating cache for {location_info['location'].get('name')}: {e}")
            return False
    
    def run_generation(self, dry_run: bool = False, city_filter: str = None, category_filter: str = None):
        """Main generation process"""
        print("🌸 Mama Knows Best Summary Generator")
        print("=" * 50)
        
        # Get locations that need summaries
        locations_to_process = self.get_locations_without_summaries(city_filter, category_filter)
        
        if not locations_to_process:
            print("✅ All cached locations already have mama summaries!")
            return
        
        print(f"📋 Found {len(locations_to_process)} locations without summaries")
        
        if city_filter:
            print(f"🏙️  Filtering by city: {city_filter}")
        if category_filter:
            print(f"📍 Filtering by category: {category_filter}")
            
        print(f"🔄 Mode: {'DRY RUN' if dry_run else 'LIVE GENERATION'}")
        print()
        
        # Process each location
        for i, location_info in enumerate(locations_to_process, 1):
            city = location_info["city"]
            category = location_info["category"]
            location = location_info["location"]
            location_name = location.get("name", "Unknown")
            
            print(f"[{i}/{len(locations_to_process)}] Processing: {location_name} ({city}, {category})")
            
            if dry_run:
                print(f"   💭 Would generate summary for this location")
                self.skipped_count += 1
                continue
            
            # Generate summary
            summary = self.generate_summary_for_location(location_info)
            
            if summary:
                print(f"   ✅ Generated: {summary[:60]}...")
                
                # Update cache
                if self.update_location_with_summary(location_info, summary):
                    print(f"   💾 Updated cache successfully")
                else:
                    print(f"   ⚠️  Failed to update cache")
            else:
                print(f"   ❌ Failed to generate summary")
        
        print()
        print("📊 Summary Generation Report:")
        print(f"   ✅ Generated: {self.generated_count}")
        print(f"   ⏭️  Skipped: {self.skipped_count}")
        print(f"   ❌ Errors: {self.error_count}")
        
        if not dry_run and self.generated_count > 0:
            print("💾 Cache has been updated with new mama summaries!")

def main():
    parser = argparse.ArgumentParser(description="Generate mama summaries for cached locations")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be generated without saving")
    parser.add_argument("--city", type=str, 
                       help="Generate summaries only for specific city")
    parser.add_argument("--category", type=str,
                       help="Generate summaries only for specific category")
    
    args = parser.parse_args()
    
    generator = MamaSummaryGenerator()
    generator.run_generation(
        dry_run=args.dry_run,
        city_filter=args.city,
        category_filter=args.category
    )

if __name__ == "__main__":
    main()