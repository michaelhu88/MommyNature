# MommyNature 🌲

Discover scenic nature spots near you, curated from Reddit discussions and enhanced with community-driven recommendations.

## What it does

MommyNature scrapes Reddit posts to find the best nature spots based on real user experiences. It analyzes discussions, extracts location mentions, and ranks them by community engagement to help you discover hidden gems.

## Live Application

**🌐 Frontend:** Deployed on Vercel  
**🚂 Backend API:** Deployed on Railway  
**🗄️ Database:** Vercel KV (Redis-based)  

The application is fully deployed and accessible online with a modern, scalable architecture.

## Local Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Reddit API credentials
- OpenAI API key
- Vercel KV database credentials (for caching)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see Environment Variables section below)
cp .env.example .env
# Edit .env with your API credentials

# Start the development server
python3 -m uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Reddit API credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=MommyNatureBot/0.1 by u/yourusername

# OpenAI API for location extraction and summaries
OPENAI_API_KEY=your_openai_api_key

# Google Places API for location verification
GOOGLE_PLACES_API_KEY=your_google_places_api_key

# Vercel KV Database (Redis-based caching)
KV_REST_API_URL=your_vercel_kv_url
KV_REST_API_TOKEN=your_vercel_kv_token

# Weather API (optional)
WEATHER_API_KEY=your_weather_api_key
```

### Production Environment Variables

For Railway (backend) deployment, set these environment variables in the Railway dashboard:
- All the above variables
- Ensure `PORT` is set to Railway's dynamic port (usually handled automatically)

For Vercel (frontend) deployment, no additional environment variables are needed as the frontend connects to the deployed Railway backend.

## API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /health` - Detailed health check with Reddit connection status

### Reddit & Location Processing
- `POST /api/transcript` - Extract Reddit post transcript from URL
- `POST /api/locations` - Extract and verify locations from Reddit URL with city/category context

### Cached Location Data
- `GET /api/places/cities` - Get all cached cities with metadata
- `GET /api/places/lookup/{place_id}` - Get city metadata by Google place_id
- `GET /api/places/{place_id}/locations/{category}` - Get locations by place_id and category
- `GET /locations/{city}/{category}` - Get cached locations by city and category (legacy)

### Location Details & Weather
- `GET /location/{location_name}/details` - Get detailed information about a specific location
- `POST /location/{location_name}/weather-advice` - Get motherly weather advice for location and date

## Example Usage

### API Examples
```bash
# Health check
curl "http://localhost:8000/health"

# Get all cached cities
curl "http://localhost:8000/api/places/cities"

# Get locations for a city by place_id
curl "http://localhost:8000/api/places/{place_id}/locations/viewpoints"

# Get location details
curl "http://localhost:8000/location/Lands%20End/details?place_id={place_id}&category=viewpoints"

# Extract locations from Reddit URL (POST request)
curl -X POST "http://localhost:8000/api/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "reddit_url": "https://www.reddit.com/r/hiking/comments/...",
    "city": "San Francisco",
    "category": "hiking_spots"
  }'
```

### Web Interface
1. Open the deployed frontend URL (Vercel deployment)
2. Search for nature spots by city using Google Places autocomplete
3. Browse categorized locations (viewpoints, dog parks, hiking spots)
4. View detailed location information with Google ratings and reviews
5. Get weather advice for planned visits

## Features

- **Smart Location Extraction**: GPT-powered identification of nature spots, parks, trails, and viewpoints from Reddit discussions
- **Google Places Integration**: Automatic verification and enrichment with Google ratings, reviews, and photos
- **Intelligent Caching**: Vercel KV (Redis) database for fast location lookup and persistent storage
- **Weather Intelligence**: Motherly weather advice for planned visits with location-specific recommendations
- **Modern UI**: Clean, responsive React interface with Google Places autocomplete
- **Real-time Processing**: Live extraction and verification of locations from Reddit posts
- **Mobile-Friendly**: Fully responsive design that works on all devices
- **Production Ready**: Deployed on modern cloud infrastructure with high availability

## Tech Stack

- **Backend**: FastAPI, Python, PRAW (Reddit API), OpenAI GPT, Google Places API
- **Frontend**: React, CSS, deployed on Vercel
- **Database**: Vercel KV (Redis-based) for caching and persistence
- **Deployment**: Railway (backend), Vercel (frontend)
- **APIs**: Reddit API, OpenAI API, Google Places API, Weather API
- **Key Libraries**: `upstash-redis`, `googlemaps`, `openai`, `fastapi`, `react-router-dom`

## Project Structure

```
MommyNature/
├── backend/
│   ├── main.py                      # FastAPI server with all API endpoints
│   ├── reddit_transcript.py         # Reddit post extraction service
│   ├── gpt_extraction.py           # GPT-powered location extraction
│   ├── google_places.py            # Google Places API integration
│   ├── vercel_kv_cache_service.py  # Vercel KV database service
│   ├── gpt_summary.py              # Location summary generation
│   ├── weather_service.py          # Weather data integration
│   ├── motherly_weather_advisor.py # Weather advice generation
│   ├── cache_manager.py            # Cache management utilities
│   ├── batch_processor.py          # Batch location processing
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js                  # Main React application
│   │   ├── SearchPage.js           # City search with Google autocomplete
│   │   ├── ResultsPage.js          # Location results display
│   │   ├── LocationDetailPage.js   # Detailed location view
│   │   ├── GooglePlacesAutocomplete.js # Google Places integration
│   │   └── *.css                   # Styling files
│   └── package.json                # Node dependencies
├── README.md                       # This file
└── claude.md                      # Development notes
```

## Database Architecture

### Vercel KV (Redis-based)

The application uses Vercel KV as its primary database for caching and persistence:

- **Storage Type**: Redis-compatible key-value store hosted on Vercel
- **Purpose**: Caches verified location data, city metadata, and Google Places information
- **Performance**: Ultra-fast lookup with global edge distribution
- **Scalability**: Automatic scaling with serverless architecture

#### Cache Structure
```
locations:{city}:{category}     # Location arrays
city_metadata:{city}           # City information with place_ids
metadata:{city}:{category}     # Category metadata
place_id_index                # Place ID to city mapping
cache_metadata                # Cache version and info
```

#### Cache Service Features
- Automatic location verification and Google Places enrichment
- City-based organization with place_id mapping
- Category-based filtering (viewpoints, dog_parks, hiking_spots)
- Batch location processing and updates
- Summary generation and caching

## Development

### Running Tests
```bash
# Test API health
curl "http://localhost:8000/health"

# Test Vercel KV cache connection
python3 backend/vercel_kv_cache_service.py

# Test Reddit transcript extraction
curl -X POST "http://localhost:8000/api/transcript" \
  -H "Content-Type: application/json" \
  -d '{"reddit_url": "your_reddit_url"}'

# Test location extraction with caching
curl -X POST "http://localhost:8000/api/locations" \
  -H "Content-Type: application/json" \
  -d '{
    "reddit_url": "your_reddit_url",
    "city": "San Francisco", 
    "category": "viewpoints"
  }'
```

### Common Issues

**Vercel KV Connection Failed**
- Check `KV_REST_API_URL` and `KV_REST_API_TOKEN` in `.env`
- Ensure your Vercel KV database is properly configured

**Reddit API Connection Failed**
- Check your Reddit API credentials in `.env`
- Ensure your Reddit app is configured correctly

**OpenAI API Errors**
- Verify `OPENAI_API_KEY` is set correctly
- Check your OpenAI account has sufficient credits

**Google Places API Issues**
- Ensure `GOOGLE_PLACES_API_KEY` is valid
- Check that Places API is enabled in Google Cloud Console

**Frontend Can't Connect to Backend**
- Make sure FastAPI is running on port 8000 (local development)
- Check CORS settings if testing from different domains
- For production, ensure the frontend points to the Railway backend URL

## Deployment

### Backend Deployment (Railway)

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard (see Environment Variables section)
3. Railway will automatically deploy from the `backend/` directory
4. The service will be available at your Railway URL

### Frontend Deployment (Vercel)

1. Connect your GitHub repository to Vercel
2. Set the build directory to `frontend/`
3. Configure build command: `npm run build`
4. Vercel will automatically deploy on pushes to main branch
5. Update frontend to use the Railway backend URL instead of localhost

### Database Setup (Vercel KV)

1. Create a KV database in your Vercel dashboard
2. Copy the connection credentials to your Railway environment variables
3. The backend will automatically connect and initialize the cache structure

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (including API endpoints and cache functionality)
5. Ensure all environment variables are documented
6. Submit a pull request

## License

MIT License - feel free to use this for your own projects!

---

*Built with ❤️ for nature lovers who want to discover amazing spots through community wisdom.*

## Architecture Overview

MommyNature uses a modern, scalable architecture:

- **Frontend**: React SPA deployed on Vercel with global CDN
- **Backend**: FastAPI REST API deployed on Railway with automatic scaling  
- **Database**: Vercel KV (Redis) for ultra-fast location caching and persistence
- **APIs**: Integrated with Reddit, OpenAI GPT, Google Places, and Weather APIs
- **Processing**: GPT-powered location extraction and verification pipeline

This setup provides high availability, global performance, and seamless scaling for discovering nature spots through Reddit community wisdom.