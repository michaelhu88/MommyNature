# MommyNature 🌲

Discover scenic nature spots near you, curated from Reddit discussions and enhanced with community-driven recommendations.

## What it does

MommyNature scrapes Reddit posts to find the best nature spots based on real user experiences. It analyzes discussions, extracts location mentions, and ranks them by community engagement to help you discover hidden gems.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Reddit API credentials

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Reddit API credentials

# Start the server
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

```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=MommyNatureBot/0.1 by u/yourusername
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health check with Reddit connection status
- `GET /scrape/{query}?max_results=5` - Scrape Reddit for nature locations
- `GET /locations/popular` - Get popular locations

## Example Usage

### Command Line
```bash
# Test the Reddit scraper directly
python3 reddit_scraper.py "hiking trails bay area"

# Test with options
python3 reddit_scraper.py "waterfalls santa cruz" --max-results 3
```

### API
```bash
# Get nature spots
curl "http://localhost:8000/scrape/hiking%20trails%20bay%20area?max_results=5"

# Check health
curl "http://localhost:8000/health"
```

### Web Interface
1. Open http://localhost:3000
2. Search for nature spots (e.g., "hiking trails bay area")
3. View top-ranked locations and Reddit discussions

## Features

- **Smart Location Extraction**: Identifies nature spots, parks, trails, and viewpoints
- **Community Scoring**: Ranks locations by Reddit upvotes and mentions
- **Real-time Search**: Live scraping of Reddit discussions
- **Clean Interface**: Simple, responsive web UI
- **Mobile-Friendly**: Works on all devices

## Tech Stack

- **Backend**: FastAPI, Python, PRAW (Reddit API)
- **Frontend**: React, CSS
- **Data**: Reddit posts and comments
- **APIs**: Reddit API, Google Search

## Project Structure

```
mommy-nature/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── reddit_scraper.py    # Reddit scraping logic
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   └── App.css         # Styling
│   └── package.json        # Node dependencies
├── README.md               # This file
└── claude.md              # Development notes
```

## Development

### Running Tests
```bash
# Test Reddit scraper
python3 reddit_scraper.py "test query" --test-connection

# Test API
curl "http://localhost:8000/health"
```

### Common Issues

**Reddit API Connection Failed**
- Check your Reddit API credentials in `.env`
- Ensure your Reddit app is configured correctly

**Frontend Can't Connect to Backend**
- Make sure FastAPI is running on port 8000
- Check CORS settings if testing from different domains

**No Results Found**
- Try different search terms
- Check if Reddit is accessible from your network

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - feel free to use this for your own projects!

---

*Built with ❤️ for nature lovers who want to discover amazing spots through community wisdom.*