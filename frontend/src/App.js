import React, { useState } from 'react';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/scrape/${encodeURIComponent(query)}?max_results=5`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }
      
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🌲 MommyNature</h1>
        <p>Discover scenic nature spots near you, curated from Reddit</p>
      </header>

      <main className="App-main">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for nature spots (e.g., 'hiking trails bay area')"
            className="search-input"
          />
          <button type="submit" disabled={loading} className="search-button">
            {loading ? 'Searching...' : 'Find Spots'}
          </button>
        </form>

        {error && (
          <div className="error">
            <p>Error: {error}</p>
            <p>Make sure your FastAPI backend is running on http://localhost:8000</p>
          </div>
        )}

        {results && (
          <div className="results">
            <div className="results-header">
              <h2>Found {results.total_posts} Reddit discussions about "{results.query}"</h2>
            </div>

            {results.top_locations && results.top_locations.length > 0 && (
              <div className="top-locations">
                <h3>🏆 Top Recommended Locations</h3>
                <div className="locations-grid">
                  {results.top_locations.slice(0, 8).map((location, index) => (
                    <div key={index} className="location-card">
                      <div className="location-rank">#{index + 1}</div>
                      <div className="location-name">{location.name}</div>
                      <div className="location-stats">
                        Score: {location.score} | Mentions: {location.mentions}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {results.reddit_posts && results.reddit_posts.length > 0 && (
              <div className="reddit-posts">
                <h3>📱 Reddit Discussions</h3>
                {results.reddit_posts.map((post, index) => (
                  <div key={index} className="reddit-post">
                    <div className="post-header">
                      <h4>{post.title}</h4>
                      <span className="post-score">👍 {post.score}</span>
                    </div>
                    
                    {post.locations && post.locations.length > 0 && (
                      <div className="post-locations">
                        <strong>Locations mentioned:</strong> {post.locations.slice(0, 5).join(', ')}
                        {post.locations.length > 5 && ` and ${post.locations.length - 5} more`}
                      </div>
                    )}
                    
                    {post.top_comments && post.top_comments[0] && (
                      <div className="top-comment">
                        <strong>💬 Top comment:</strong>
                        <p>{post.top_comments[0].body.slice(0, 200)}...</p>
                      </div>
                    )}
                    
                    <a href={post.reddit_url} target="_blank" rel="noopener noreferrer" className="reddit-link">
                      View on Reddit →
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;