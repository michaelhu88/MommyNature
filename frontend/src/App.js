import React, { useState } from 'react';
import './App.css';

function App() {
  const [searchParams, setSearchParams] = useState({
    location_type: 'viewpoints',
    city: '',
    state: '',
    max_results: 5
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Location type options
  const locationTypes = [
    { value: 'viewpoints', label: 'Scenic Viewpoints' },
    { value: 'hiking', label: 'Hiking Trails' },
    { value: 'dog_parks', label: 'Dog Parks' }
  ];

  // US States options
  const usStates = [
    { value: '', label: 'Select state' },
    { value: 'CA', label: 'California (CA)' },
    { value: 'NY', label: 'New York (NY)' },
    { value: 'TX', label: 'Texas (TX)' },
    { value: 'FL', label: 'Florida (FL)' },
    { value: 'WA', label: 'Washington (WA)' },
    { value: 'OR', label: 'Oregon (OR)' },
    { value: 'CO', label: 'Colorado (CO)' },
    { value: 'AZ', label: 'Arizona (AZ)' },
    { value: 'NV', label: 'Nevada (NV)' },
    { value: 'UT', label: 'Utah (UT)' },
    { value: 'NM', label: 'New Mexico (NM)' },
    { value: 'ID', label: 'Idaho (ID)' },
    { value: 'MT', label: 'Montana (MT)' },
    { value: 'WY', label: 'Wyoming (WY)' },
    { value: 'NC', label: 'North Carolina (NC)' },
    { value: 'SC', label: 'South Carolina (SC)' },
    { value: 'GA', label: 'Georgia (GA)' },
    { value: 'AL', label: 'Alabama (AL)' },
    { value: 'TN', label: 'Tennessee (TN)' },
    { value: 'KY', label: 'Kentucky (KY)' },
    { value: 'VA', label: 'Virginia (VA)' },
    { value: 'WV', label: 'West Virginia (WV)' },
    { value: 'MD', label: 'Maryland (MD)' },
    { value: 'PA', label: 'Pennsylvania (PA)' },
    { value: 'NJ', label: 'New Jersey (NJ)' },
    { value: 'CT', label: 'Connecticut (CT)' },
    { value: 'MA', label: 'Massachusetts (MA)' },
    { value: 'VT', label: 'Vermont (VT)' },
    { value: 'NH', label: 'New Hampshire (NH)' },
    { value: 'ME', label: 'Maine (ME)' },
    { value: 'RI', label: 'Rhode Island (RI)' }
  ];

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchParams.city.trim()) {
      setError('Please enter a city');
      return;
    }
    if (!searchParams.state) {
      setError('Please select a state');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      // Combine city and state into "City, State" format
      const cityStateCombo = `${searchParams.city.trim()}, ${searchParams.state}`;
      console.log('🔍 handleSearch - combined city,state:', cityStateCombo);
      
      // Clean any potential issues (fallback in case user somehow added extra text)
      let cleanedCity = cityStateCombo;
      if (cleanedCity.toUpperCase().endsWith('USA')) {
        cleanedCity = cleanedCity.slice(0, -3).trim();
      }
      if (cleanedCity.endsWith(',')) {
        cleanedCity = cleanedCity.slice(0, -1).trim();
      }
      console.log('🧹 handleSearch - final cleaned city:', cleanedCity);
      const encodedCity = encodeURIComponent(cleanedCity.trim());
      const encodedCategory = encodeURIComponent(searchParams.location_type);
      
      const response = await fetch(`http://localhost:8000/locations/${encodedCity}/${encodedCategory}`);
      
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
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="nav-left">
          <button className="hamburger-menu">
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
        <div className="nav-center">
          <h1 className="nav-title">🌲 MommyNature</h1>
        </div>
        <div className="nav-right">
          <button className="nav-button">EXPLORE</button>
        </div>
      </nav>

      <div className="main-container">
        {/* Header */}
        <header className="app-header">
          <p className="app-subtitle">Discover Scenic Nature Spots Curated from Reddit</p>
        </header>

        {/* Main Search Section */}
        <section className="search-main">
          <div className="search-wrapper">
            <h2 className="search-title">What are you looking for?</h2>
            
            {/* Category Selection */}
            <div className="category-grid">
              {locationTypes.map(type => (
                <button
                  key={type.value}
                  className={`category-pill ${
                    searchParams.location_type === type.value ? 'active' : ''
                  }`}
                  onClick={() => setSearchParams({...searchParams, location_type: type.value})}
                >
                  {type.label}
                </button>
              ))}
            </div>

            {/* Search Form */}
            <form onSubmit={handleSearch} className="search-form">
              <div className="search-bar">
                <input
                  type="text"
                  value={searchParams.city}
                  onChange={(e) => {
                    console.log('🔄 App.js received city update:', e.target.value);
                    setSearchParams({...searchParams, city: e.target.value});
                  }}
                  placeholder="Enter city name (e.g., San Francisco)"
                  className="search-input city-input"
                />
                <select
                  value={searchParams.state}
                  onChange={(e) => {
                    console.log('🔄 App.js received state update:', e.target.value);
                    setSearchParams({...searchParams, state: e.target.value});
                  }}
                  className="search-input state-select"
                >
                  {usStates.map(state => (
                    <option key={state.value} value={state.value}>
                      {state.label}
                    </option>
                  ))}
                </select>
              </div>
              <button 
                type="submit" 
                disabled={loading || !searchParams.city.trim() || !searchParams.state} 
                className="search-button"
              >
                {loading ? 'Searching...' : 'Find Places'}
              </button>
            </form>
          </div>
        </section>

        <main className="content-main">

        {error && (
          <div className="error">
            <p>Error: {error}</p>
            <p>Make sure your FastAPI backend is running on http://localhost:8000</p>
          </div>
        )}

        {results && (
          <div className="results">
            <div className="results-header">
              <h2>Found {results.count || 0} {locationTypes.find(t => t.value === results.category)?.label} in {results.city}</h2>
            </div>

            {results.locations && results.locations.length > 0 ? (
              <div className="top-locations">
                <h3>🏆 Top Recommended Locations</h3>
                <div className="locations-grid">
                  {results.locations.map((location, index) => (
                    <div key={index} className="location-card">
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
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="no-results">
                <h3>No locations found</h3>
                <p>{results.message || `No ${locationTypes.find(t => t.value === results.category)?.label} found in ${results.city}`}</p>
                <p>Try a different city or category, or check if the city name is spelled correctly.</p>
              </div>
            )}
          </div>
        )}
        </main>
      </div>
    </div>
  );
}

export default App;