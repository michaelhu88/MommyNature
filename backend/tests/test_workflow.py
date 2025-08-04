#!/usr/bin/env python3
"""
Test script for the structured DuckDuckGo + Reddit + Google Places workflow
Flow: location_type + city → DuckDuckGo finds Reddit posts → Reddit scraper extracts locations → Google Places validates with city context
"""

import os
import sys
sys.path.append('..')
from dotenv import load_dotenv
from reddit_scraper import RedditScraper

def test_workflow():
    # Load environment variables
    load_dotenv('../.env')
    
    # Test with structured parameters
    location_type = "viewpoints"
    city = "San Jose, CA"
    print(f"🔍 Testing structured workflow: {location_type} in {city}")
    print("=" * 60)
    
    # Initialize scraper in debug mode
    scraper = RedditScraper(debug_mode=True)
    
    # Step 1: Search Reddit with structured parameters
    print(f"\n📡 Step 1: Searching Reddit for {location_type} in {city}...")
    results = scraper.scrape_for_locations(location_type, city, max_results=3)
    
    if not results:
        print("❌ No Reddit posts found")
        return
    
    print(f"✅ Found {len(results)} Reddit posts")
    
    # Step 2: Show what was found
    print("\n📋 Step 2: Reddit posts discovered:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['title']}")
        print(f"     Score: {result['score']}, Comments: {len(result['top_comments'])}")
        print(f"     URL: {result['reddit_url']}")
        print(f"     Locations found: {result['locations']}")
        print(f"     Location type: {result.get('location_type', 'N/A')}")
        print(f"     City context: {result.get('city_context', 'N/A')}")
        print()
    
    # Step 3: Extract and validate top locations with Google Places
    print("\n🏔️  Step 3: Extracting and validating locations with city context...")
    top_locations = scraper.get_top_locations_by_score(results, top_n=10)
    
    if top_locations:
        print(f"✅ Found {len(top_locations)} validated locations:")
        for i, location in enumerate(top_locations, 1):
            print(f"  {i}. {location['name']}")
            print(f"     Combined Score: {location['score']}")
            print(f"     Reddit Score: {location['reddit_score']}, Google Score: {location['google_score']}")
            print(f"     Mentions: {location['mentions']}")
            if location.get('google_rating'):
                print(f"     Google Rating: {location['google_rating']}/5 ({location['google_reviews']} reviews)")
            if location.get('address'):
                print(f"     Address: {location['address']}")
            print(f"     Sources: {location['sources'][0] if location['sources'] else 'N/A'}")
            print()
    else:
        print("❌ No locations extracted")
    
    print("=" * 60)
    print(f"🎯 Workflow complete! Found {len(top_locations)} locations from {len(results)} Reddit posts")

if __name__ == "__main__":
    test_workflow()