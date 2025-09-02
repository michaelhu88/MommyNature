import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  
  const { results, searchParams } = location.state || {};

  if (!results || !searchParams) {
    navigate('/');
    return null;
  }

  const locationTypes = [
    { value: 'viewpoints', label: 'Scenic Viewpoints' },
    { value: 'hiking', label: 'Hiking Trails' },
    { value: 'dog_parks', label: 'Dog Parks' }
  ];

  const handleNewSearch = () => {
    navigate('/');
  };

  const handleLocationClick = (location) => {
    navigate(`/location/${encodeURIComponent(location.name)}`, {
      state: {
        locationData: location,
        searchContext: {
          city: results.city_metadata?.display_name || results.city_metadata?.name,
          category: results.category,
          place_id: results.place_id
        }
      }
    });
  };

  return (
    <div className="main-container">
      <div className="results-header-section">
        <button onClick={handleNewSearch} className="back-button">
          ← New Search
        </button>
        <div className="results-header">
          <h2>Found {results.count || 0} {locationTypes.find(t => t.value === results.category)?.label} in {results.city_metadata?.display_name || results.city_metadata?.name}</h2>
        </div>
      </div>

      <main className="content-main">
        {results && (
          <div className="results">
            {results.locations && results.locations.length > 0 ? (
              <div className="top-locations">
                <h3>🏆 Top Recommended Locations</h3>
                <div className="locations-grid">
                  {results.locations.map((location, index) => (
                    <div key={index} className="location-card clickable" onClick={() => handleLocationClick(location)}>
                      <div className="location-rank">#{index + 1}</div>
                      <div className="location-name">{location.name}</div>
                      <div className="location-stats">
                        Score: {location.score?.toFixed(1) || 'N/A'} | Mentions: {location.mentions || 0}
                        {location.google_rating && ` | ⭐ ${location.google_rating}/5`}
                      </div>
                      {location.address && (
                        <div className="location-address">
                          📍 {location.address}
                        </div>
                      )}
                      {location.validated && (
                        <div className="location-validation">
                          ✅ Verified with Google Places
                        </div>
                      )}
                      <div className="location-action">
                        <span className="view-details">View Details →</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="no-results">
                <h3>No locations found</h3>
                <p>{results.message || `No ${locationTypes.find(t => t.value === results.category)?.label} found in ${results.city_metadata?.display_name || results.city_metadata?.name}`}</p>
                <p>Try a different city or category, or check if the city name is spelled correctly.</p>
                <button onClick={handleNewSearch} className="search-button">
                  Try Another Search
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default ResultsPage;