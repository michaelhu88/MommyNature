import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import GooglePlacesAutocomplete from './GooglePlacesAutocomplete';

function SearchPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useState({
    location_type: 'viewpoints',
    selectedPlace: null,
    max_results: 5
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const locationTypes = [
    { value: 'viewpoints', label: 'Scenic Viewpoints' },
    { value: 'hiking', label: 'Hiking Trails' },
    { value: 'dog_parks', label: 'Dog Parks' }
  ];

  const handlePlaceSelect = (place) => {
    console.log('🏙️ Selected place:', place);
    setSearchParams({...searchParams, selectedPlace: place});
    setError(null);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchParams.selectedPlace) {
      setError('Please select a location');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const placeId = searchParams.selectedPlace.place_id;
      const category = searchParams.location_type;
      console.log('🔍 handleSearch - using place_id:', placeId, 'category:', category);
      
      const response = await fetch(`https://mommynature-production.up.railway.app/api/places/${encodeURIComponent(placeId)}/locations/${encodeURIComponent(category)}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }
      
      const data = await response.json();
      
      navigate('/results', { 
        state: { 
          results: data, 
          searchParams: {
            ...searchParams,
            city: searchParams.selectedPlace.display_name
          }
        } 
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-container">
      <header className="app-header">
        <p className="app-subtitle">Discover Scenic Nature Spots Curated from Reddit</p>
      </header>

      <section className="search-main">
        <div className="search-wrapper">
          <h2 className="search-title">What are you looking for?</h2>
          
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

          <form onSubmit={handleSearch} className="search-form">
            <div className="search-bar">
              <GooglePlacesAutocomplete
                onPlaceSelect={handlePlaceSelect}
                placeholder="Enter city name (e.g., San Francisco)"
                className="search-input city-input"
                value={searchParams.selectedPlace?.display_name || ''}
                disabled={loading}
              />
            </div>
            <button 
              type="submit" 
              disabled={loading || !searchParams.selectedPlace?.place_id} 
              className="search-button"
            >
              {loading ? 'Searching...' : 'Find Places'}
            </button>
          </form>

          {error && (
            <div className="error">
              <p>Error: {error}</p>
              <p>Unable to connect to the backend server. Please try again.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default SearchPage;