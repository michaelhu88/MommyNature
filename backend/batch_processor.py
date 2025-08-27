#!/usr/bin/env python3
"""
Batch Processor - Process multiple Reddit URLs to populate location cache

Usage:
    python3 batch_processor.py

Features:
- Process multiple (reddit_url, city, category) tuples
- Send requests to /api/locations endpoint
- Progress tracking with detailed output  
- Error handling and retry logic
- Final summary report
"""

import requests
import time
import sys
from typing import List, Tuple, Dict, Any
from datetime import datetime


class BatchProcessor:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """Initialize batch processor"""
        self.api_base_url = api_base_url
        self.locations_endpoint = f"{api_base_url}/api/locations"
        self.health_endpoint = f"{api_base_url}/health"
        
        # Processing stats
        self.total_processed = 0
        self.total_successful = 0
        self.total_failed = 0
        self.results = []

    def check_api_health(self) -> bool:
        """Check if the API server is running"""
        try:
            response = requests.get(self.health_endpoint, timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API server is healthy")
                print(f"   Endpoints: {health_data.get('endpoints', [])}")
                return True
            else:
                print(f"❌ API server responded with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to API server: {e}")
            print(f"   Make sure the server is running at {self.api_base_url}")
            return False

    def validate_tuple(self, data_tuple: Tuple[str, str, str]) -> Tuple[bool, str]:
        """Validate a single data tuple"""
        if len(data_tuple) != 3:
            return False, f"Tuple must have exactly 3 elements, got {len(data_tuple)}"
        
        reddit_url, city, category = data_tuple
        
        # Validate URL
        if not reddit_url or not reddit_url.startswith("http"):
            return False, f"Invalid Reddit URL: {reddit_url}"
        
        if "reddit.com" not in reddit_url:
            return False, f"URL must be from reddit.com: {reddit_url}"
        
        # Validate city
        if not city or not city.strip():
            return False, "City cannot be empty"
        
        # Validate category
        valid_categories = ["viewpoints", "dog_parks", "hiking_spots"]
        if category not in valid_categories:
            return False, f"Category must be one of {valid_categories}, got '{category}'"
        
        return True, "Valid"

    def process_single_request(self, reddit_url: str, city: str, category: str, index: int, total: int) -> Dict[str, Any]:
        """Process a single location request"""
        print(f"\n[{index}/{total}] Processing: {city} {category}")
        print(f"   URL: {reddit_url}")
        
        start_time = time.time()
        
        # Prepare request data
        request_data = {
            "reddit_url": reddit_url,
            "city": city,
            "category": category
        }
        
        try:
            # Send POST request
            response = requests.post(
                self.locations_endpoint,
                json=request_data,
                timeout=120  # 2 minute timeout for processing
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                
                # Extract key metrics
                verified_count = len(result_data.get('verified_locations', []))
                total_extracted = len(result_data.get('raw_locations', []))
                cached = result_data.get('cached', False)
                
                print(f"   ✅ SUCCESS ({processing_time:.1f}s)")
                print(f"   📍 Extracted: {total_extracted} locations")
                print(f"   ✅ Verified: {verified_count} locations") 
                print(f"   💾 Cached: {'Yes' if cached else 'No'}")
                
                return {
                    "status": "success",
                    "reddit_url": reddit_url,
                    "city": city,
                    "category": category,
                    "verified_count": verified_count,
                    "total_extracted": total_extracted,
                    "cached": cached,
                    "processing_time": processing_time,
                    "response_data": result_data
                }
            else:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', str(error_data))
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                
                print(f"   ❌ FAILED ({processing_time:.1f}s)")
                print(f"   Error: {error_detail}")
                
                return {
                    "status": "failed",
                    "reddit_url": reddit_url,
                    "city": city,
                    "category": category,
                    "error": error_detail,
                    "processing_time": processing_time,
                    "http_status": response.status_code
                }
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT (>{120}s)")
            return {
                "status": "failed",
                "reddit_url": reddit_url,
                "city": city,
                "category": category,
                "error": "Request timeout",
                "processing_time": time.time() - start_time
            }
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ CONNECTION ERROR: {e}")
            return {
                "status": "failed",
                "reddit_url": reddit_url,
                "city": city,
                "category": category,
                "error": f"Connection error: {e}",
                "processing_time": time.time() - start_time
            }

    def process_batch(self, batch_data: List[Tuple[str, str, str]]) -> Dict[str, Any]:
        """Process a batch of location requests"""
        print("🚀 BATCH LOCATION PROCESSOR")
        print("=" * 50)
        
        if not batch_data:
            print("❌ No data to process")
            return {"success": False, "error": "Empty batch data"}
        
        # Check API health first
        if not self.check_api_health():
            return {"success": False, "error": "API server not available"}
        
        print(f"\n📋 Processing {len(batch_data)} location requests...")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Validate all tuples first
        print(f"\n🔍 Validating input data...")
        for i, data_tuple in enumerate(batch_data, 1):
            is_valid, message = self.validate_tuple(data_tuple)
            if not is_valid:
                print(f"❌ Invalid tuple #{i}: {message}")
                return {"success": False, "error": f"Invalid input data: {message}"}
        
        print(f"✅ All {len(batch_data)} tuples validated successfully")
        
        # Process each request
        self.results = []
        start_time = time.time()
        
        for i, (reddit_url, city, category) in enumerate(batch_data, 1):
            result = self.process_single_request(reddit_url, city, category, i, len(batch_data))
            self.results.append(result)
            
            if result["status"] == "success":
                self.total_successful += 1
            else:
                self.total_failed += 1
            
            self.total_processed += 1
            
            # Small delay between requests to be nice to the API
            if i < len(batch_data):
                time.sleep(1)
        
        # Generate summary report
        total_time = time.time() - start_time
        summary = self.generate_summary_report(total_time)
        
        return {
            "success": True,
            "summary": summary,
            "detailed_results": self.results
        }

    def generate_summary_report(self, total_time: float) -> Dict[str, Any]:
        """Generate final summary report"""
        print(f"\n" + "=" * 50)
        print("📊 BATCH PROCESSING SUMMARY")
        print("=" * 50)
        
        # Overall stats
        print(f"⏰ Total processing time: {total_time:.1f}s")
        print(f"📊 Total requests: {self.total_processed}")
        print(f"✅ Successful: {self.total_successful}")
        print(f"❌ Failed: {self.total_failed}")
        
        if self.total_processed > 0:
            success_rate = (self.total_successful / self.total_processed) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        # Location stats
        total_locations = sum(r.get('verified_count', 0) for r in self.results if r['status'] == 'success')
        print(f"📍 Total locations cached: {total_locations}")
        
        # City/category breakdown
        city_stats = {}
        for result in self.results:
            if result['status'] == 'success':
                city = result['city']
                category = result['category']
                count = result.get('verified_count', 0)
                
                if city not in city_stats:
                    city_stats[city] = {}
                if category not in city_stats[city]:
                    city_stats[city][category] = 0
                
                city_stats[city][category] += count
        
        if city_stats:
            print(f"\n🏙️ Locations by city:")
            for city, categories in city_stats.items():
                total_city_locations = sum(categories.values())
                print(f"   {city}: {total_city_locations} locations")
                for category, count in categories.items():
                    print(f"     └── {category}: {count}")
        
        # Error summary
        if self.total_failed > 0:
            print(f"\n❌ Failed requests:")
            for result in self.results:
                if result['status'] == 'failed':
                    print(f"   • {result['city']} {result['category']}: {result.get('error', 'Unknown error')}")
        
        return {
            "total_processed": self.total_processed,
            "successful": self.total_successful,
            "failed": self.total_failed,
            "success_rate": (self.total_successful / self.total_processed * 100) if self.total_processed > 0 else 0,
            "total_locations": total_locations,
            "processing_time": total_time,
            "city_stats": city_stats
        }


def main():
    """Main function with sample data"""
    
    # SAMPLE BATCH DATA - Modify this list with your Reddit URLs
    batch_data = [
        # Format: (reddit_url, city, category)
        ("https://www.reddit.com/r/SanJose/comments/1fj1txc/fun_dog_friendly_parks_for_a_day_off_in_ssj/", 
         "San Jose", "dog_parks"),
    ]
    
    print(f"🎯 Ready to process {len(batch_data)} location requests")
    print("📝 Batch data:")
    for i, (url, city, category) in enumerate(batch_data, 1):
        print(f"   {i}. {city} {category} - {url}")
    
    # Confirm before processing
    try:
        confirm = input(f"\nProceed with batch processing? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("❌ Batch processing cancelled")
            return
    except KeyboardInterrupt:
        print("\n❌ Batch processing cancelled")
        return
    
    # Create processor and run batch
    processor = BatchProcessor()
    
    try:
        result = processor.process_batch(batch_data)
        
        if result["success"]:
            print(f"\n🎉 Batch processing completed successfully!")
            summary = result["summary"]
            if summary["total_locations"] > 0:
                print(f"💾 Added {summary['total_locations']} verified locations to cache")
        else:
            print(f"\n❌ Batch processing failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Batch processing interrupted by user")
        if processor.total_processed > 0:
            print(f"📊 Partial results: {processor.total_successful}/{processor.total_processed} successful")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during batch processing: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())