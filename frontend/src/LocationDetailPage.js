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
      if (searchContext?.city) params.append('city', searchContext.city);
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

        {/* Why awesome section */}
        {locationData.awesome_points && locationData.awesome_points.length > 0 && (
          <div className="awesome-section">
            <h2>Why This Place is Awesome</h2>
            <ul className="awesome-list">
              {locationData.awesome_points.map((point, index) => (
                <li key={index} className="awesome-item">
                  {point}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Stats section */}
        <div className="stats-section">
          <h3>Quick Stats</h3>
          <div className="stats-grid">
            {locationData.google_rating && (
              <div className="stat-card">
                <div className="stat-label">Google Rating</div>
                <div className="stat-value">⭐ {locationData.google_rating}/5</div>
                {locationData.google_reviews > 0 && (
                  <div className="stat-subtitle">{locationData.google_reviews} reviews</div>
                )}
              </div>
            )}
            
            {locationData.score && (
              <div className="stat-card">
                <div className="stat-label">Overall Score</div>
                <div className="stat-value">{locationData.score}/10</div>
              </div>
            )}
            
            {locationData.mentions > 0 && (
              <div className="stat-card">
                <div className="stat-label">Reddit Mentions</div>
                <div className="stat-value">{locationData.mentions}</div>
              </div>
            )}
          </div>
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