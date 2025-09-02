import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';

function LocationDetailPage() {
  const { locationName } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [locationData, setLocationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedPhotoIndex, setSelectedPhotoIndex] = useState(0);
  
  // Weather advice state
  const [selectedDate, setSelectedDate] = useState('');
  const [weatherAdvice, setWeatherAdvice] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState(null);

  // Try to get location data from navigation state first
  const passedLocationData = location.state?.locationData;
  const searchContext = location.state?.searchContext;

  const fetchLocationDetails = useCallback(async () => {
    console.log('🔍 FRONTEND DEBUG: Starting fetchLocationDetails for:', locationName);
    setLoading(true);
    setError(null);
    
    try {
      let url = `http://localhost:8000/location/${encodeURIComponent(locationName)}/details`;
      
      // Add context parameters if available
      const params = new URLSearchParams();
      if (searchContext?.place_id) params.append('place_id', searchContext.place_id);
      if (searchContext?.category) params.append('category', searchContext.category);
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      console.log('📡 FRONTEND DEBUG: Fetching from URL:', url);
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('Failed to fetch location details');
      }
      
      const data = await response.json();
      console.log('📦 FRONTEND DEBUG: Received data:', data);
      console.log('📸 FRONTEND DEBUG: Photo URLs:', data.location?.photo_urls);
      
      setLocationData(data.location);
    } catch (err) {
      console.error('❌ FRONTEND DEBUG: Error fetching location details:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [locationName, searchContext]);

  useEffect(() => {
    console.log('🔄 FRONTEND DEBUG: useEffect triggered');
    console.log('  - passedLocationData:', !!passedLocationData);
    console.log('  - locationName:', locationName);
    
    if (passedLocationData) {
      console.log('📋 FRONTEND DEBUG: Using passed location data:', passedLocationData);
      console.log('📸 FRONTEND DEBUG: Passed photo URLs:', passedLocationData.photo_urls);
      
      // Check if photo data is missing from passed data
      if (!passedLocationData.photo_urls || passedLocationData.photo_urls.length === 0) {
        console.log('🔄 FRONTEND DEBUG: No photos in passed data, fetching fresh from API');
        fetchLocationDetails();
      } else {
        setLocationData(passedLocationData);
      }
    } else {
      console.log('🌐 FRONTEND DEBUG: Fetching location details from API');
      fetchLocationDetails();
    }
  }, [locationName, passedLocationData, fetchLocationDetails]);

  const handleBack = () => {
    navigate(-1); // Go back to previous page
  };

  const getTagColor = (color) => {
    const colorMap = {
      'green': 'var(--primary-green)',
      'blue': '#3b82f6',
      'yellow': '#f59e0b',
      'red': '#ef4444',
      'purple': '#8b5cf6',
      'brown': '#92400e',
      'gray': 'var(--soft-gray)',
      'gold': '#f59e0b'
    };
    return colorMap[color] || 'var(--soft-gray)';
  };

  // Weather advice handlers
  const handleDateChange = (e) => {
    setSelectedDate(e.target.value);
    setWeatherAdvice(null);
    setWeatherError(null);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const getWeatherAdvice = async () => {
    if (!selectedDate || !locationData) return;

    setWeatherLoading(true);
    setWeatherError(null);
    setWeatherAdvice(null);

    try {
      const requestBody = {
        location_name: locationData.name,
        visit_date: selectedDate,
        place_id: searchContext?.place_id || null,
        category: searchContext?.category || null
      };

      console.log('🌤️ FRONTEND DEBUG: Weather request:', requestBody);

      const response = await fetch(
        `http://localhost:8000/location/${encodeURIComponent(locationData.name)}/weather-advice`, 
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody)
        }
      );

      if (!response.ok) {
        throw new Error(`Weather service error: ${response.status}`);
      }

      const data = await response.json();
      console.log('🌈 FRONTEND DEBUG: Weather advice received:', data);
      
      setWeatherAdvice(data);
    } catch (err) {
      console.error('❌ FRONTEND DEBUG: Weather advice error:', err);
      setWeatherError(
        "I'm having trouble getting the weather right now, sweetie! " +
        "Maybe try again in a moment, or check your local weather forecast. " +
        "Either way, dress in layers and have a wonderful time! 💕"
      );
    } finally {
      setWeatherLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="main-container">
        <div className="loading-container">
          <h2>Loading location details...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="main-container">
        <div className="error-container">
          <h2>Error loading location</h2>
          <p>{error}</p>
          <button onClick={handleBack} className="search-button">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!locationData) {
    return (
      <div className="main-container">
        <div className="error-container">
          <h2>Location not found</h2>
          <button onClick={handleBack} className="search-button">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const hasPhotos = locationData.photo_urls && locationData.photo_urls.length > 0;
  const currentPhoto = hasPhotos ? locationData.photo_urls[selectedPhotoIndex] : null;
  
  // Debug logging for photo display
  console.log('🖼️ FRONTEND DEBUG: Photo display check for', locationData.name);
  console.log('  - photo_urls field exists:', !!locationData.photo_urls);
  console.log('  - photo_urls:', locationData.photo_urls);
  console.log('  - hasPhotos:', hasPhotos);
  console.log('  - selectedPhotoIndex:', selectedPhotoIndex);
  console.log('  - currentPhoto URL:', currentPhoto);

  return (
    <div className="main-container">
      {/* Back button */}
      <div className="detail-header">
        <button onClick={handleBack} className="back-button">
          ← Back to Results
        </button>
      </div>

      {/* Hero section with photo */}
      <div className="hero-section">
        {hasPhotos ? (
          <div className="hero-image-container">
            <img 
              src={currentPhoto} 
              alt={locationData.name}
              className="hero-image"
              onLoad={(e) => {
                console.log('✅ FRONTEND DEBUG: Image loaded successfully:', currentPhoto);
                console.log('  - Image dimensions:', e.target.naturalWidth, 'x', e.target.naturalHeight);
              }}
              onError={(e) => {
                console.error('❌ FRONTEND DEBUG: Image failed to load:', currentPhoto);
                console.error('  - Error details:', e);
                e.target.style.display = 'none';
                e.target.nextElementSibling.style.display = 'flex';
              }}
            />
            <div className="hero-fallback" style={{ display: 'none' }}>
              <div className="hero-fallback-content">
                <h1>📍</h1>
                <p>Photo not available</p>
              </div>
            </div>
            
            {/* Photo navigation */}
            {locationData.photo_urls.length > 1 && (
              <div className="photo-nav">
                {locationData.photo_urls.map((_, index) => (
                  <button
                    key={index}
                    className={`photo-nav-dot ${index === selectedPhotoIndex ? 'active' : ''}`}
                    onClick={() => setSelectedPhotoIndex(index)}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="hero-fallback">
            <div className="hero-fallback-content">
              <h1>🏞️</h1>
              <p>No photos available</p>
            </div>
          </div>
        )}
        
        {/* Hero overlay text */}
        <div className="hero-overlay">
          <h1 className="hero-title">{locationData.name}</h1>
          {locationData.address && (
            <p className="hero-address">📍 {locationData.address}</p>
          )}
        </div>
      </div>

      {/* Content section */}
      <div className="detail-content">
        
        {/* Tags section */}
        {locationData.tags && locationData.tags.length > 0 && (
          <div className="tags-section">
            <div className="tags-container">
              {locationData.tags.map((tag, index) => (
                <span 
                  key={index} 
                  className="location-tag"
                  style={{ backgroundColor: getTagColor(tag.color) }}
                >
                  {tag.label}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Mama Knows Best section */}
        {locationData.mama_summary && (
          <div className="mama-section">
            <h2>Mama Knows Best 💝</h2>
            <div className="mama-summary">
              {locationData.mama_summary}
            </div>
          </div>
        )}

        {/* When Are You Going? section */}
        <div className="when-going-section">
          <h2>When Are You Going? 📅</h2>
          <div className="date-picker-container">
            <div className="date-input-wrapper">
              <label htmlFor="visit-date" className="date-label">
                Tell mama when you're planning to visit:
              </label>
              <input
                type="date"
                id="visit-date"
                className="date-input"
                min={new Date().toISOString().split('T')[0]}
                max={new Date(Date.now() + 5*24*60*60*1000).toISOString().split('T')[0]}
                onChange={handleDateChange}
                value={selectedDate}
              />
            </div>
            
            {selectedDate && (
              <button 
                onClick={getWeatherAdvice}
                className="weather-button"
                disabled={weatherLoading}
              >
                {weatherLoading ? '🌤️ Getting weather...' : '🌤️ Get Weather Advice'}
              </button>
            )}
          </div>

          {/* Weather advice display */}
          {weatherAdvice && (
            <div className="weather-advice-container">
              <div className="weather-info">
                <h3>Weather Forecast for {formatDate(selectedDate)}</h3>
                <div className="weather-details">
                  <div className="temp-display">
                    <span className="temperature">
                      {weatherAdvice.weather.temperature || weatherAdvice.weather.avg_temp}°F
                    </span>
                    {weatherAdvice.weather.high_temp && weatherAdvice.weather.low_temp && (
                      <span className="temp-range">
                        {weatherAdvice.weather.low_temp}° - {weatherAdvice.weather.high_temp}°
                      </span>
                    )}
                  </div>
                  <div className="weather-condition">
                    {weatherAdvice.weather.description || 'Partly cloudy'}
                  </div>
                </div>
              </div>
              
              <div className="mama-weather-advice">
                <h3>Mama's Weather Wisdom 🌈</h3>
                <div className="weather-advice-text">
                  {weatherAdvice.mama_advice}
                </div>
              </div>
            </div>
          )}

          {weatherError && (
            <div className="weather-error">
              <h3>Oops! 😅</h3>
              <div className="error-message">
                {weatherError}
              </div>
            </div>
          )}
        </div>

        {/* Data source info */}
        <div className="source-info">
          <p className="source-text">
            Data sourced from Reddit discussions and Google Places
          </p>
        </div>
      </div>
    </div>
  );
}

export default LocationDetailPage;