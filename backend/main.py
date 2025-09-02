from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
from reddit_transcript import RedditTranscriptService
from gpt_extraction import GPTLocationExtractor
from gpt_cache_service import GPTCacheService
from gpt_summary import GPTSummaryService
from weather_service import WeatherService
from motherly_weather_advisor import MotherlyWeatherAdvisor
import uvicorn

app = FastAPI(
    title="MommyNature API",
    description="Discover scenic nature spots from Reddit discussions",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
transcript_service = RedditTranscriptService()
gpt_extractor = GPTLocationExtractor()
cache_service = GPTCacheService()
summary_service = GPTSummaryService()
weather_service = WeatherService()
weather_advisor = MotherlyWeatherAdvisor()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MommyNature API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Reddit connection
        subreddit = transcript_service.reddit.subreddit("hiking")
        test_post = next(subreddit.hot(limit=1))
        reddit_status = "connected"
    except Exception as e:
        reddit_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "reddit_api": reddit_status,
        "endpoints": ["/api/transcript", "/api/locations", "/api/places/cities", "/api/places/lookup", "/api/places/{place_id}/locations", "/health"]
    }

class TranscriptRequest(BaseModel):
    reddit_url: str

class LocationRequest(BaseModel):
    reddit_url: str
    city: str
    category: str  # viewpoints, dog_parks, hiking_spots

class WeatherRequest(BaseModel):
    location_name: str
    visit_date: str  # ISO date format (YYYY-MM-DD)
    place_id: Optional[str] = None
    category: Optional[str] = None

@app.post("/api/transcript")
async def get_reddit_transcript(request: TranscriptRequest):
    """
    Extract complete transcript from a Reddit URL
    
    - **reddit_url**: Reddit post URL to extract transcript from
    """
    try:
        # Extract transcript from the URL
        transcript = await asyncio.get_event_loop().run_in_executor(
            None,
            transcript_service.get_transcript,
            request.reddit_url
        )
        
        if not transcript:
            raise HTTPException(status_code=400, detail="Could not extract submission ID from URL")
        
        if not transcript.get('success'):
            raise HTTPException(status_code=500, detail=f"Transcript extraction failed: {transcript.get('error')}")
        
        return transcript
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcript extraction failed: {str(e)}")

@app.post("/api/locations")
async def extract_locations(request: LocationRequest):
    """
    Extract and verify locations from Reddit URL with city and category context
    
    - **reddit_url**: Reddit post URL to extract locations from
    - **city**: City context (required) - e.g. "San Jose", "San Francisco"
    - **category**: Location category (required) - "viewpoints", "dog_parks", or "hiking_spots"
    """
    try:
        # Validate category
        valid_categories = ["viewpoints", "dog_parks", "hiking_spots"]
        if request.category not in valid_categories:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )
        
        # Step 1: Get transcript using existing service (reuse logic)
        transcript = await asyncio.get_event_loop().run_in_executor(
            None,
            transcript_service.get_transcript,
            request.reddit_url
        )
        
        if not transcript:
            raise HTTPException(status_code=400, detail="Could not extract submission ID from URL")
        
        if not transcript.get('success'):
            raise HTTPException(status_code=500, detail=f"Transcript extraction failed: {transcript.get('error')}")
        
        # Step 2: Extract locations with GPT + Google verification
        if not gpt_extractor.client:
            raise HTTPException(status_code=500, detail="OpenAI API not available - check OPENAI_API_KEY")
        
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            gpt_extractor.extract_locations,
            transcript,
            request.city,
            request.category
        )
        
        # Step 3: Cache verified locations if any exist
        if result['verified_locations']:
            # TODO: Update to pass city_place_id and city_metadata when Google Places integration is complete
            cache_success = await asyncio.get_event_loop().run_in_executor(
                None,
                cache_service.add_locations,
                request.city,
                request.category,
                result['verified_locations'],
                request.reddit_url
            )
            result['cached'] = cache_success
        else:
            result['cached'] = False
        
        # Add request info to response
        result['request_info'] = {
            'reddit_url': request.reddit_url,
            'city': request.city,
            'category': request.category,
            'post_title': transcript['post']['title'],
            'total_comments': transcript['total_comments']
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Location extraction failed: {str(e)}")

@app.get("/api/places/cities")
async def get_all_cities():
    """
    Get all cached cities with their metadata including place_ids
    
    Returns list of cities with place_id, name, state, etc.
    """
    try:
        cities = cache_service.get_all_cities_with_metadata()
        return {
            "cities": cities,
            "count": len(cities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cities: {str(e)}")

@app.get("/api/places/lookup/{place_id}")
async def get_city_by_place_id(place_id: str):
    """
    Get city metadata by Google place_id
    
    - **place_id**: Google Places place_id for the city
    """
    try:
        city_metadata = cache_service.get_city_by_place_id(place_id)
        
        if not city_metadata:
            raise HTTPException(status_code=404, detail=f"City with place_id '{place_id}' not found in cache")
        
        return {
            "city_metadata": city_metadata,
            "place_id": place_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to lookup city by place_id: {str(e)}")

@app.get("/api/places/{place_id}/locations/{category}")
async def get_locations_by_place_id(place_id: str, category: str):
    """
    Get cached locations by Google place_id and category
    
    - **place_id**: Google Places place_id for the city
    - **category**: Location category (e.g., "viewpoints", "dog_parks")
    """
    try:
        # Get locations using place_id
        locations = cache_service.get_locations_by_place_id(place_id, category)
        
        # Get city metadata for response
        city_metadata = cache_service.get_city_by_place_id(place_id)
        
        if not locations:
            return {
                "city_metadata": city_metadata,
                "place_id": place_id,
                "category": category,
                "count": 0,
                "locations": [],
                "message": f"No {category} found for this city. Try a different category."
            }
        
        # Transform cache data to match frontend expectations
        frontend_locations = []
        for location in locations:
            frontend_location = {
                "name": location.get("name"),
                "address": location.get("address"),
                "google_rating": location.get("google_rating"),
                "google_reviews": location.get("google_reviews", 0),
                "place_id": location.get("place_id"),
                "validated": location.get("verified", False),
                "score": location.get("google_rating") or 7.0,
                "mentions": 1
            }
            frontend_locations.append(frontend_location)
        
        return {
            "city_metadata": city_metadata,
            "place_id": place_id,
            "category": category,
            "count": len(frontend_locations),
            "locations": frontend_locations,
            "source": "cache"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get locations by place_id: {str(e)}")

@app.get("/locations/{city}/{category}")
async def get_cached_locations(city: str, category: str):
    """
    Get cached locations by city and category
    
    - **city**: City name (e.g., "San Jose", "San Francisco")  
    - **category**: Location category (e.g., "viewpoints", "dog_parks")
    """
    try:
        # Normalize city name (handle URL encoding)
        city = city.replace("%20", " ").replace("+", " ").strip()
        
        # Get cached locations
        locations = cache_service.get_locations(city=city, category=category)
        
        if not locations:
            return {
                "city": city,
                "category": category,
                "count": 0,
                "locations": [],
                "message": f"No {category} found in {city}. Try a different city or category."
            }
        
        # Transform cache data to match frontend expectations
        frontend_locations = []
        for location in locations:
            frontend_location = {
                "name": location.get("name"),
                "address": location.get("address"),
                "google_rating": location.get("google_rating"),
                "google_reviews": location.get("google_reviews", 0),
                "place_id": location.get("place_id"),
                "validated": location.get("verified", False),
                "score": location.get("google_rating") or 7.0,  # Use Google rating or default
                "mentions": 1  # Default since cache doesn't track mentions
            }
            frontend_locations.append(frontend_location)
        
        return {
            "city": city,
            "category": category,
            "count": len(frontend_locations),
            "locations": frontend_locations,
            "source": "cache"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cached locations: {str(e)}")

@app.get("/location/{location_name}/details")
async def get_location_details(location_name: str, place_id: Optional[str] = None, category: Optional[str] = None):
    """
    Get detailed information about a specific location
    
    - **location_name**: Name of the location to get details for
    - **place_id**: Google place_id for the city to lookup locations
    - **category**: Optional category context to narrow search
    """
    try:
        # Normalize location name (handle URL encoding)
        location_name = location_name.replace("%20", " ").replace("+", " ").strip()
        
        # Search for the location in cache using place_id
        if place_id:
            all_locations = cache_service.get_locations_by_place_id(place_id, category)
        else:
            # Fallback to getting all locations if no place_id provided
            all_locations = cache_service.get_locations(category=category)
        
        if not all_locations:
            raise HTTPException(status_code=404, detail=f"No locations found in cache")
        
        # Find location by name (case-insensitive)
        found_location = None
        for location in all_locations:
            if location.get("name", "").lower() == location_name.lower():
                found_location = location
                break
        
        if not found_location:
            # Try partial match if exact match not found
            for location in all_locations:
                if location_name.lower() in location.get("name", "").lower():
                    found_location = location
                    break
        
        if not found_location:
            raise HTTPException(status_code=404, detail=f"Location '{location_name}' not found in cache")
        
        # Generate mama summary if not cached
        mama_summary = found_location.get("mama_summary")
        if not mama_summary and summary_service.client:
            try:
                # Generate new summary using GPT
                mama_summary = await asyncio.get_event_loop().run_in_executor(
                    None,
                    summary_service.generate_location_summary,
                    found_location
                )
                # Update cache with generated summary (if we have a place_id)
                if mama_summary and place_id:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        cache_service.update_location_summary,
                        place_id,
                        category or "unknown",
                        found_location.get("name"),
                        mama_summary
                    )
            except Exception as e:
                print(f"Error generating mama summary for {found_location.get('name')}: {e}")
                mama_summary = None
        
        # Transform cache data to match frontend expectations
        location_details = {
            "name": found_location.get("name"),
            "address": found_location.get("address"),
            "google_rating": found_location.get("google_rating"),
            "google_reviews": found_location.get("google_reviews", 0),
            "place_id": found_location.get("place_id"),
            "validated": found_location.get("verified", False),
            "score": found_location.get("google_rating") or 7.0,
            "mentions": 1,  # Default since cache doesn't track mentions
            "tags": [],  # Could be derived from google_types if needed
            "awesome_points": [f"Highly rated location with {found_location.get('google_reviews', 0)} reviews"],
            "photo_urls": found_location.get("photo_urls", []),
            "mama_summary": mama_summary
        }
        
        return {
            "location": location_details,
            "source": "cache"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get location details: {str(e)}")

@app.post("/location/{location_name}/weather-advice")
async def get_weather_advice(location_name: str, request: WeatherRequest):
    """
    Get motherly weather advice for a specific location and date
    
    - **location_name**: Name of the location to get weather advice for
    - **visit_date**: Date of planned visit in ISO format (YYYY-MM-DD)
    - **place_id**: Optional Google place_id for better location lookup
    - **category**: Optional category context
    """
    try:
        # Normalize location name (handle URL encoding)
        location_name = location_name.replace("%20", " ").replace("+", " ").strip()
        
        # Get location data from cache first
        location_data = None
        if request.place_id:
            all_locations = cache_service.get_locations_by_place_id(request.place_id, request.category)
        else:
            all_locations = cache_service.get_locations(category=request.category)
        
        # Find the specific location
        if all_locations:
            for location in all_locations:
                if location.get("name", "").lower() == location_name.lower():
                    location_data = location
                    break
        
        # Fallback location data if not found in cache
        if not location_data:
            location_data = {
                'name': location_name,
                'address': f"{location_name}, CA, USA",  # Fallback address
                'category': request.category or 'unknown'
            }
        
        # Get city name for weather lookup (always use city weather, not specific location)
        city_name = None
        
        # Try to get city from place_id first
        if request.place_id:
            city_metadata = cache_service.get_city_by_place_id(request.place_id)
            if city_metadata:
                city_name = city_metadata.get('name') or city_metadata.get('display_name', '').split(',')[0]
        
        # Fallback: try to extract city from cached location data
        if not city_name and location_data:
            # Look through all cached cities to find where this location exists
            all_cities = cache_service.get_all_cities_with_metadata()
            for city_data in all_cities:
                city_locations = cache_service.get_locations(city_data['name'], request.category)
                if city_locations:
                    for loc in city_locations:
                        if loc.get('name', '').lower() == location_name.lower():
                            city_name = city_data['name']
                            break
                    if city_name:
                        break
        
        # Final fallback: assume California and use simple city extraction
        if not city_name:
            # Default to major California cities for testing
            city_name = "San Francisco"  # Default fallback - could be made smarter
        
        # Get weather data for the CITY (not the specific location)
        weather_data = await asyncio.get_event_loop().run_in_executor(
            None,
            weather_service.get_weather_for_location_and_date,
            city_name,
            request.visit_date
        )
        
        if not weather_data:
            raise HTTPException(status_code=500, detail="Unable to get weather data")
        
        # Generate motherly weather advice
        weather_advice = await asyncio.get_event_loop().run_in_executor(
            None,
            weather_advisor.generate_motherly_weather_advice,
            location_data,
            weather_data,
            request.visit_date
        )
        
        return {
            "location": {
                "name": location_data.get("name"),
                "city": city_name,
                "address": location_data.get('address', f"{location_name}, CA, USA")
            },
            "visit_date": request.visit_date,
            "weather": weather_data,
            "mama_advice": weather_advice,
            "weather_note": f"Weather data is for {city_name} (city weather applies to all locations within the city)",
            "generated_at": asyncio.get_event_loop().time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weather advice: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)