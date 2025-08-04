#!/usr/bin/env python3
"""
Locations Database Viewer - View cached nature recommendations from Reddit
Usage: python3 view_cache.py [summary|details <city>|locations [city] [category]|search <term>]
"""

import os
import json
import sys
from datetime import datetime
from typing import Optional

class LocationsViewer:
    def __init__(self, database_file="reddit_cache/locations_database.json"):
        self.database_file = database_file
        self.data = {}
        self.load_database()
    
    def load_database(self) -> bool:
        """Load the locations database"""
        if not os.path.exists(self.database_file):
            print(f"❌ Database file '{self.database_file}' doesn't exist")
            return False
        
        try:
            with open(self.database_file, 'r') as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            return False
    
    def format_timestamp(self, timestamp: float) -> str:
        """Format timestamp to readable date"""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def show_summary(self):
        """Show summary of all cities and categories"""
        if not self.data:
            print("📭 No data found in database")
            return
        
        total_locations = 0
        total_categories = 0
        
        print(f"🏔️  Locations Database Summary ({len(self.data)} cities)")
        print("=" * 70)
        
        for city, categories in self.data.items():
            city_locations = 0
            print(f"\n📍 {city}")
            
            for category, category_data in categories.items():
                location_count = category_data.get('count', len(category_data.get('locations', [])))
                updated_at = category_data.get('updated_at', 0)
                city_locations += location_count
                total_categories += 1
                
                print(f"   🏷️  {category}: {location_count} locations (updated: {self.format_timestamp(updated_at)})")
            
            print(f"   📊 Total: {city_locations} locations")
            total_locations += city_locations
        
        print(f"\n🎯 Grand Total: {total_locations} locations across {total_categories} categories in {len(self.data)} cities")
    
    def show_city_details(self, city: str):
        """Show detailed view of all categories for a specific city"""
        # Find city (case insensitive)
        city_key = None
        for key in self.data.keys():
            if key.lower() == city.lower():
                city_key = key
                break
        
        if not city_key:
            print(f"❌ City '{city}' not found in database")
            print(f"Available cities: {', '.join(self.data.keys())}")
            return
        
        city_data = self.data[city_key]
        
        print(f"🏙️  Details for {city_key}")
        print("=" * 70)
        
        total_locations = 0
        
        for category, category_data in city_data.items():
            locations = category_data.get('locations', [])
            updated_at = category_data.get('updated_at', 0)
            
            print(f"\n🏷️  {category.upper()} ({len(locations)} locations)")
            print(f"📅 Last updated: {self.format_timestamp(updated_at)}")
            print("-" * 50)
            
            # Sort locations by score (descending)
            sorted_locations = sorted(locations, key=lambda x: x.get('score', 0), reverse=True)
            
            for i, location in enumerate(sorted_locations, 1):
                name = location.get('name', 'Unknown')
                score = location.get('score', 0)
                reddit_score = location.get('reddit_score', 0)
                google_score = location.get('google_score', 0)
                mentions = location.get('mentions', 0)
                google_rating = location.get('google_rating')
                google_reviews = location.get('google_reviews', 0)
                address = location.get('address', 'No address')
                validated = location.get('validated', False)
                
                validation_icon = "✅" if validated else "❓"
                
                print(f"{i:2d}. {validation_icon} {name}")
                print(f"     📊 Score: {score:.1f} (Reddit: {reddit_score:.1f}, Google: {google_score:.1f})")
                print(f"     💬 Mentions: {mentions}")
                
                if google_rating:
                    print(f"     ⭐ Google: {google_rating}/5.0 ({google_reviews} reviews)")
                
                print(f"     📍 {address}")
                
                # Show sources
                sources = location.get('sources', [])
                if sources:
                    source_preview = sources[0][:80] + "..." if len(sources[0]) > 80 else sources[0]
                    print(f"     💭 Source: {source_preview}")
                
                print()
            
            total_locations += len(locations)
        
        print(f"🎯 Total locations in {city_key}: {total_locations}")
    
    def show_locations(self, city_filter: Optional[str] = None, category_filter: Optional[str] = None):
        """Show all locations, optionally filtered by city and/or category"""
        if not self.data:
            print("📭 No data found in database")
            return
        
        all_locations = []
        
        # Collect all locations
        for city, categories in self.data.items():
            # Apply city filter
            if city_filter and city_filter.lower() not in city.lower():
                continue
            
            for category, category_data in categories.items():
                # Apply category filter
                if category_filter and category_filter.lower() not in category.lower():
                    continue
                
                locations = category_data.get('locations', [])
                for location in locations:
                    location_info = {
                        'city': city,
                        'category': category,
                        **location
                    }
                    all_locations.append(location_info)
        
        if not all_locations:
            filter_desc = ""
            if city_filter and category_filter:
                filter_desc = f" matching city '{city_filter}' and category '{category_filter}'"
            elif city_filter:
                filter_desc = f" in city '{city_filter}'"
            elif category_filter:
                filter_desc = f" in category '{category_filter}'"
            
            print(f"❌ No locations found{filter_desc}")
            return
        
        # Sort by score (descending)
        sorted_locations = sorted(all_locations, key=lambda x: x.get('score', 0), reverse=True)
        
        filter_desc = ""
        if city_filter and category_filter:
            filter_desc = f" ({city_filter} - {category_filter})"
        elif city_filter:
            filter_desc = f" ({city_filter})"
        elif category_filter:
            filter_desc = f" ({category_filter})"
        
        print(f"🏔️  All Locations{filter_desc} ({len(sorted_locations)} found)")
        print("=" * 70)
        
        current_city = None
        current_category = None
        
        for location in sorted_locations:
            city = location['city']
            category = location['category']
            name = location.get('name', 'Unknown')
            score = location.get('score', 0)
            mentions = location.get('mentions', 0)
            google_rating = location.get('google_rating')
            validated = location.get('validated', False)
            
            # Show city header if changed
            if city != current_city:
                print(f"\n📍 {city}")
                current_city = city
                current_category = None
            
            # Show category header if changed
            if category != current_category:
                print(f"  🏷️  {category}")
                current_category = category
            
            validation_icon = "✅" if validated else "❓"
            rating_text = f" (⭐{google_rating}/5)" if google_rating else ""
            
            print(f"    {validation_icon} {name} - Score: {score:.1f}, Mentions: {mentions}{rating_text}")
    
    def search_locations(self, search_term: str):
        """Search for locations by name, address, or source content"""
        if not self.data:
            print("📭 No data found in database")
            return
        
        matches = []
        search_lower = search_term.lower()
        
        for city, categories in self.data.items():
            for category, category_data in categories.items():
                locations = category_data.get('locations', [])
                
                for location in locations:
                    name = location.get('name', '').lower()
                    address = location.get('address', '').lower()
                    sources = location.get('sources', [])
                    google_types = location.get('google_types', [])
                    
                    # Check if search term matches name, address, sources, or types
                    match_found = False
                    match_type = ""
                    
                    if search_lower in name:
                        match_found = True
                        match_type = "name"
                    elif search_lower in address:
                        match_found = True
                        match_type = "address"
                    elif any(search_lower in source.lower() for source in sources):
                        match_found = True
                        match_type = "source"
                    elif any(search_lower in gtype.lower() for gtype in google_types):
                        match_found = True
                        match_type = "type"
                    
                    if match_found:
                        matches.append({
                            'city': city,
                            'category': category,
                            'match_type': match_type,
                            **location
                        })
        
        if not matches:
            print(f"❌ No locations found matching '{search_term}'")
            return
        
        # Sort matches by score
        sorted_matches = sorted(matches, key=lambda x: x.get('score', 0), reverse=True)
        
        print(f"🔍 Found {len(sorted_matches)} matches for '{search_term}'")
        print("=" * 70)
        
        for match in sorted_matches:
            city = match['city']
            category = match['category']
            name = match.get('name', 'Unknown')
            score = match.get('score', 0)
            address = match.get('address', 'No address')
            source_url = match.get('source_url', '')
            match_type = match['match_type']
            validated = match.get('validated', False)
            google_rating = match.get('google_rating')
            
            validation_icon = "✅" if validated else "❓"
            rating_text = f" (⭐{google_rating}/5)" if google_rating else ""
            
            print(f"{validation_icon} {name}{rating_text}")
            print(f"   📍 {city} - {category} (Score: {score:.1f})")
            print(f"   🎯 Match: {match_type}")
            print(f"   📍 {address}")
            if source_url:
                print(f"   🔗 {source_url}")
            print()

    def show_stats(self):
        """Show detailed statistics about the database"""
        if not self.data:
            print("📭 No data found in database")
            return
        
        print("📊 Database Statistics")
        print("=" * 50)
        
        total_locations = 0
        validated_locations = 0
        categories_stats = {}
        cities_stats = {}
        
        for city, categories in self.data.items():
            city_count = 0
            
            for category, category_data in categories.items():
                locations = category_data.get('locations', [])
                city_count += len(locations)
                
                # Category stats
                if category not in categories_stats:
                    categories_stats[category] = 0
                categories_stats[category] += len(locations)
                
                # Validation stats
                for location in locations:
                    if location.get('validated', False):
                        validated_locations += 1
            
            cities_stats[city] = city_count
            total_locations += city_count
        
        print(f"🏙️  Cities: {len(self.data)}")
        print(f"🏷️  Categories: {len(categories_stats)}")
        print(f"🏔️  Total Locations: {total_locations}")
        print(f"✅ Validated: {validated_locations} ({validated_locations/total_locations*100:.1f}%)")
        
        print(f"\n📊 By Category:")
        for category, count in sorted(categories_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count}")
        
        print(f"\n📍 By City:")
        for city, count in sorted(cities_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"   {city}: {count}")

def main():
    viewer = LocationsViewer()
    
    if len(sys.argv) < 2:
        print("Usage: python3 view_cache.py [summary|details <city>|locations [city] [category]|search <term>|stats]")
        print("\nCommands:")
        print("  summary                    - Show overview of all cities and categories")
        print("  details <city>             - Show detailed view of all categories for a city")
        print("  locations [city] [category] - Show all locations, optionally filtered")
        print("  search <term>              - Search locations by name, address, or content")
        print("  stats                      - Show database statistics")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'summary':
        viewer.show_summary()
    elif command == 'details':
        if len(sys.argv) < 3:
            print("Usage: python3 view_cache.py details <city>")
            print(f"Available cities: {', '.join(viewer.data.keys())}")
            sys.exit(1)
        city = sys.argv[2]
        viewer.show_city_details(city)
    elif command == 'locations':
        city_filter = sys.argv[2] if len(sys.argv) > 2 else None
        category_filter = sys.argv[3] if len(sys.argv) > 3 else None
        viewer.show_locations(city_filter, category_filter)
    elif command == 'search':
        if len(sys.argv) < 3:
            print("Usage: python3 view_cache.py search <term>")
            sys.exit(1)
        search_term = sys.argv[2]
        viewer.search_locations(search_term)
    elif command == 'stats':
        viewer.show_stats()
    else:
        print("Invalid command. Use: summary, details, locations, search, or stats")

if __name__ == "__main__":
    main()