from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import asyncio
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

# Initialize Reddit scraper
scraper = RedditScraper()

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
        "endpoints": ["/scrape/{query}", "/locations/popular", "/health"]
    }

@app.get("/scrape/{query}")
async def scrape_locations(query: str, max_results: int = 5):
    """
    Scrape Reddit for nature locations
    
    - **query**: Search term (e.g., "hiking trails bay area")
    - **max_results**: Maximum number of Reddit posts to process (default: 5)
    """
    try:
        # Run scraping in thread to avoid blocking
        results = await asyncio.get_event_loop().run_in_executor(
            None, 
            scraper.scrape_for_locations, 
            query, 
            max_results
        )
        
        # Get top locations
        top_locations = scraper.get_top_locations_by_score(results, top_n=10)
        
        return {
            "query": query,
            "reddit_posts": results,
            "top_locations": top_locations,
            "total_posts": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/locations/popular")
async def get_popular_locations():
    """Get popular nature locations from recent scrapes"""
    # This would eventually pull from database
    # For now, return some sample Bay Area locations
    return {
        "locations": [
            {"name": "Sierra Vista Open Space", "type": "viewpoint", "region": "South Bay"},
            {"name": "Mt. Hamilton", "type": "mountain", "region": "South Bay"},
            {"name": "Communications Hill", "type": "viewpoint", "region": "South Bay"},
            {"name": "Muir Woods", "type": "forest", "region": "North Bay"},
            {"name": "Point Reyes", "type": "coastal", "region": "North Bay"},
            {"name": "Big Sur", "type": "coastal", "region": "Central Coast"}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)