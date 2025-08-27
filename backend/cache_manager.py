#!/usr/bin/env python3
"""
Cache Manager - Interactive CLI tool for managing GPT location cache

Usage:
    python3 cache_manager.py

Features:
- View detailed cache summary
- Clear entire cache
- Interactive menu system
"""

import sys
import os
from datetime import datetime
from gpt_cache_service import GPTCacheService


class CacheManager:
    def __init__(self):
        """Initialize cache manager with service"""
        self.cache_service = GPTCacheService()
        self.running = True

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Print application header"""
        print("=" * 50)
        print("  MOMMY NATURE - CACHE MANAGER")
        print("=" * 50)
        print()

    def print_menu(self):
        """Print main menu options"""
        print("📋 CACHE MANAGEMENT OPTIONS:")
        print()
        print("  1. View cache summary")
        print("  2. Clear entire cache")  
        print("  3. Exit")
        print()

    def view_cache_summary(self):
        """Display detailed cache summary"""
        print("📊 CACHE SUMMARY")
        print("-" * 30)
        
        try:
            summary = self.cache_service.get_detailed_summary()
            
            if not summary or not summary.get("cities"):
                print("🔍 Cache is empty - no locations found.")
                print()
                return
            
            # Overview
            overview = summary.get("overview", {})
            print(f"🏙️  Cities: {overview.get('total_cities', 0)}")
            print(f"📍 Total Locations: {overview.get('total_locations', 0)}")
            print(f"✅ Verified: {overview.get('total_verified', 0)}")
            print(f"📂 Categories: {overview.get('total_categories', 0)}")
            print()
            
            # Cache info
            cache_info = summary.get("cache_info", {})
            print(f"📄 Cache File: {os.path.basename(cache_info.get('cache_file', 'unknown'))}")
            print(f"🕐 Created: {self._format_timestamp(cache_info.get('created', 'unknown'))}")
            print()
            
            # Per-city breakdown
            cities = summary.get("cities", {})
            for city, city_data in cities.items():
                print(f"🌆 {city} ({city_data['total_locations']} locations)")
                
                categories = city_data.get("categories", {})
                for category, cat_data in categories.items():
                    verified = cat_data.get("verified_count", 0)
                    total = cat_data.get("location_count", 0)
                    last_updated = self._format_timestamp(cat_data.get("last_updated", "unknown"))
                    
                    print(f"  └── {category}: {total} locations ({verified} verified)")
                    print(f"      Last updated: {last_updated}")
                print()
                
        except Exception as e:
            print(f"❌ Error retrieving cache summary: {e}")
        
        print()

    def clear_cache_with_confirmation(self):
        """Clear cache with user confirmation"""
        print("🗑️  CLEAR CACHE")
        print("-" * 20)
        print()
        print("⚠️  WARNING: This will permanently delete ALL cached locations!")
        print("   This action cannot be undone.")
        print()
        
        # Get confirmation
        confirm = input("Are you sure you want to clear the cache? (yes/no): ").lower().strip()
        
        if confirm in ['yes', 'y']:
            print()
            print("🧹 Clearing cache...")
            
            try:
                success = self.cache_service.clear_cache()
                
                if success:
                    print("✅ Cache cleared successfully!")
                    print("📝 Cache reset to empty state.")
                else:
                    print("❌ Failed to clear cache.")
                    
            except Exception as e:
                print(f"❌ Error clearing cache: {e}")
        else:
            print("🔒 Cache clear operation cancelled.")
        
        print()

    def _format_timestamp(self, timestamp_str: str) -> str:
        """Format timestamp string for display"""
        if timestamp_str == "unknown":
            return "Unknown"
        
        try:
            # Parse ISO timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return timestamp_str

    def get_user_choice(self) -> str:
        """Get user menu choice"""
        try:
            choice = input("Enter your choice (1-3): ").strip()
            return choice
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return "3"

    def run(self):
        """Main application loop"""
        self.clear_screen()
        
        while self.running:
            self.print_header()
            self.print_menu()
            
            choice = self.get_user_choice()
            print()
            
            if choice == "1":
                self.view_cache_summary()
            elif choice == "2":
                self.clear_cache_with_confirmation()
            elif choice == "3":
                print("👋 Goodbye!")
                self.running = False
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                print()
            
            if self.running:
                input("Press Enter to continue...")
                self.clear_screen()


def main():
    """Entry point for cache manager"""
    try:
        manager = CacheManager()
        manager.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()