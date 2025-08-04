#!/usr/bin/env python3
"""
Cache Viewer - View cached Reddit scraping results
Usage: python3 view_cache.py [summary|details|locations|search <term>]
"""

import os
import json
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

class CacheViewer:
    def __init__(self, cache_dir="reddit_cache"):
        self.cache_dir = cache_dir
    
    def list_cache_files(self) -> List[str]:
        """List all cache files"""
        if not os.path.exists(self.cache_dir):
            print(f"❌ Cache directory '{self.cache_dir}' doesn't exist")
            return []
        
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
        return sorted(cache_files)
    
    def load_cache_file(self, filename: str) -> Dict[str, Any]:
        """Load a specific cache file"""
        filepath = os.path.join(self.cache_dir, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
            return {}
    
    def format_timestamp(self, timestamp: float) -> str:
        """Format timestamp to readable date"""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def show_cache_summary(self):
        """Show summary of all cached queries"""
        cache_files = self.list_cache_files()
        
        if not cache_files:
            print("📭 No cache files found")
            return
        
        print(f"📦 Cache Summary ({len(cache_files)} files)")
        print("=" * 60)
        
        total_locations = 0
        total_posts = 0
        
        for i, filename in enumerate(cache_files, 1):
            data = self.load_cache_file(filename)
            if not data:
                continue
            
            # Extract info
            query = data.get('query', 'Unknown')
            results = data.get('results', [])
            cached_at = data.get('cached_at', 0)
            
            # Count locations
            locations_count = sum(len(result.get('locations', [])) for result in results)
            total_locations += locations_count
            total_posts += len(results)
            
            print(f"{i}. Query: '{query}'")
            print(f"   Posts: {len(results)}, Locations: {locations_count}")
            print(f"   Cached: {self.format_timestamp(cached_at)}")
            print()
        
        print(f"🎯 Total: {total_posts} posts, {total_locations} locations")
    
    def show_cache_details(self, cache_index: int = 0):
        """Show detailed view of a specific cache entry"""
        cache_files = self.list_cache_files()
        
        if not cache_files:
            print("📭 No cache files found")
            return
        
        if cache_index >= len(cache_files):
            print(f"❌ Cache index {cache_index} out of range (0-{len(cache_files)-1})")
            return
        
        filename = cache_files[cache_index]
        data = self.load_cache_file(filename)
        
        if not data:
            return
        
        # Header
        query = data.get('query', 'Unknown')
        cached_at = data.get('cached_at', 0)
        results = data.get('results', [])
        
        print(f"🔍 Cache Details: '{query}'")
        print(f"📅 Cached: {self.format_timestamp(cached_at)}")
        print(f"📋 Results: {len(results)} posts")
        print("=" * 60)
        
        # Show each post
        for i, result in enumerate(results, 1):
            print(f"\n📝 Post {i}: {result.get('title', 'No title')}")
            print(f"   Score: {result.get('score', 0)}")
            print(f"   URL: {result.get('reddit_url', 'No URL')}")
            print(f"   Locations: {', '.join(result.get('locations', []))}")
            
            # Show top comments
            comments = result.get('top_comments', [])
            if comments:
                print(f"   💬 Top Comments:")
                for j, comment in enumerate(comments[:2], 1):  # Show top 2
                    body = comment.get('body', '')[:100] + '...' if len(comment.get('body', '')) > 100 else comment.get('body', '')
                    print(f"      {j}. (+{comment.get('score', 0)}) {body}")
    
    def show_all_locations(self):
        """Show all unique locations found across all cache files"""
        cache_files = self.list_cache_files()
        
        if not cache_files:
            print("📭 No cache files found")
            return
        
        location_mentions = {}
        
        # Collect all locations
        for filename in cache_files:
            data = self.load_cache_file(filename)
            if not data:
                continue
            
            query = data.get('query', 'Unknown')
            results = data.get('results', [])
            
            for result in results:
                locations = result.get('locations', [])
                for location in locations:
                    if location not in location_mentions:
                        location_mentions[location] = {
                            'count': 0,
                            'queries': set(),
                            'sources': []
                        }
                    
                    location_mentions[location]['count'] += 1
                    location_mentions[location]['queries'].add(query)
                    location_mentions[location]['sources'].append(result.get('title', 'Unknown'))
        
        # Sort by mention count
        sorted_locations = sorted(location_mentions.items(), key=lambda x: x[1]['count'], reverse=True)
        
        print(f"🏔️  All Locations ({len(sorted_locations)} unique)")
        print("=" * 60)
        
        for location, data in sorted_locations:
            queries = list(data['queries'])
            sources = data['sources'][:3]  # Show top 3 sources
            
            print(f"📍 {location}")
            print(f"   Mentions: {data['count']}")
            print(f"   Queries: {', '.join(queries)}")
            print(f"   Sources: {', '.join(sources)}")
            print()
    
    def search_locations(self, search_term: str):
        """Search for locations containing a specific term"""
        cache_files = self.list_cache_files()
        
        if not cache_files:
            print("📭 No cache files found")
            return
        
        matches = []
        
        for filename in cache_files:
            data = self.load_cache_file(filename)
            if not data:
                continue
            
            query = data.get('query', 'Unknown')
            results = data.get('results', [])
            
            for result in results:
                locations = result.get('locations', [])
                for location in locations:
                    if search_term.lower() in location.lower():
                        matches.append({
                            'location': location,
                            'query': query,
                            'post_title': result.get('title', 'Unknown'),
                            'url': result.get('reddit_url', '')
                        })
        
        if matches:
            print(f"🔍 Found {len(matches)} matches for '{search_term}'")
            print("=" * 60)
            
            for match in matches:
                print(f"📍 {match['location']}")
                print(f"   Query: {match['query']}")
                print(f"   Post: {match['post_title']}")
                print(f"   URL: {match['url']}")
                print()
        else:
            print(f"❌ No locations found matching '{search_term}'")

def main():
    viewer = CacheViewer()
    
    if len(sys.argv) < 2:
        print("Usage: python3 view_cache.py [summary|details|locations|search <term>]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'summary':
        viewer.show_cache_summary()
    elif command == 'details':
        index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        viewer.show_cache_details(index)
    elif command == 'locations':
        viewer.show_all_locations()
    elif command == 'search':
        if len(sys.argv) < 3:
            print("Usage: python3 view_cache.py search <term>")
            sys.exit(1)
        search_term = sys.argv[2]
        viewer.search_locations(search_term)
    else:
        print("Invalid command. Use: summary, details, locations, or search")

if __name__ == "__main__":
    main()