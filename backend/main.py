from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import os
from reddit_scraper import RedditScraper
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


# Initialize Reddit scraper (with debug mode for development)
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
scraper = RedditScraper(debug_mode=DEBUG_MODE)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MommyNature API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test Reddit connection
        subreddit = scraper.reddit.subreddit("hiking")
        test_post = next(subreddit.hot(limit=1))
        reddit_status = "connected"
    except Exception as e:
        reddit_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "reddit_api": reddit_status,
        "endpoints": ["/scrape/url", "/locations/{city}/{category}", "/locations/{city}", "/health"]
    }

class ScrapeUrlRequest(BaseModel):
    url: str
    city: str
    category: str
    target_count: int = 10

@app.post("/scrape/url")
async def scrape_reddit_url(request: ScrapeUrlRequest):
    """
    Extract top locations from a specific Reddit URL
    
    - **url**: Reddit post URL to scrape
    - **city**: City name (e.g., "San Jose, CA")
    - **category**: Location category (e.g., "viewpoints", "hiking_trails", "dog_parks")
    - **target_count**: Number of top locations to extract (default: 10)
    """
    try:
        # Extract locations from the URL
        top_locations = await asyncio.get_event_loop().run_in_executor(
            None,
            scraper.extract_top_locations_from_url,
            request.url,
            request.city,
            request.category,
            request.target_count
        )
        
        return {
            "success": True,
            "city": request.city,
            "category": request.category,
            "url": request.url,
            "locations": top_locations,
            "count": len(top_locations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"URL scraping failed: {str(e)}")

@app.get("/locations/{city}/{category}")
async def get_locations_for_city_category(city: str, category: str):
    """Get saved locations for a specific city and category"""
    try:
        locations = scraper.get_locations_for_city_category(city, category)
        
        if not locations:
            return {
                "city": city,
                "category": category,
                "locations": [],
                "message": f"No saved locations found for {city} → {category}"
            }
        
        return {
            "city": city,
            "category": category,
            "locations": locations,
            "count": len(locations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving locations: {str(e)}")

@app.get("/locations/{city}")
async def get_all_locations_for_city(city: str):
    """Get all categories and locations for a specific city"""
    try:
        city_data = scraper.get_all_locations_for_city(city)
        
        if not city_data:
            return {
                "city": city,
                "categories": {},
                "message": f"No saved data found for {city}"
            }
        
        # Count total locations across all categories
        total_locations = sum(
            len(cat_data.get('locations', [])) for cat_data in city_data.values()
        )
        
        return {
            "city": city,
            "categories": city_data,
            "total_locations": total_locations,
            "categories_count": len(city_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving city data: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)