import React, { useEffect, useRef, useState } from 'react';

const GooglePlacesAutocomplete = ({ 
  onPlaceSelect, 
  placeholder = "Enter city name", 
  className = "",
  value = "",
  disabled = false 
}) => {
  const inputRef = useRef(null);
  const autocompleteRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    const loadGooglePlacesAPI = () => {
      if (window.google && window.google.maps && window.google.maps.places) {
        initializeAutocomplete();
        return;
      }

      const apiKey = process.env.REACT_APP_GOOGLE_PLACES_API_KEY;
      if (!apiKey) {
        console.error('Google Places API key not found in environment variables');
        return;
      }

      if (!document.querySelector('#google-places-script')) {
        const script = document.createElement('script');
        script.id = 'google-places-script';
        script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
        script.async = true;
        script.onload = initializeAutocomplete;
        document.head.appendChild(script);
      }
    };

    const initializeAutocomplete = () => {
      if (!inputRef.current || autocompleteRef.current) return;

      autocompleteRef.current = new window.google.maps.places.Autocomplete(inputRef.current, {
        types: ['(cities)'],
        componentRestrictions: { country: 'us' }
      });

      autocompleteRef.current.addListener('place_changed', handlePlaceSelect);
    };

    const handlePlaceSelect = () => {
      if (!autocompleteRef.current) return;
      
      setIsLoading(true);
      const place = autocompleteRef.current.getPlace();
      
      if (place && place.place_id && place.geometry) {
        const selectedPlace = {
          place_id: place.place_id,
          name: place.name,
          formatted_address: place.formatted_address,
          display_name: place.formatted_address || place.name,
          geometry: place.geometry.location ? {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng()
          } : null
        };
        
        setDisplayValue(selectedPlace.display_name);
        onPlaceSelect(selectedPlace);
      } else {
        console.warn('Selected place missing required data:', place);
        onPlaceSelect(null);
      }
      
      setIsLoading(false);
    };

    loadGooglePlacesAPI();

    return () => {
      if (autocompleteRef.current) {
        window.google?.maps?.event?.clearInstanceListeners(autocompleteRef.current);
      }
    };
  }, [onPlaceSelect]);

  useEffect(() => {
    setDisplayValue(value);
  }, [value]);

  const handleInputChange = (e) => {
    setDisplayValue(e.target.value);
    if (!e.target.value.trim()) {
      onPlaceSelect(null);
    }
  };

  return (
    <div className="google-places-autocomplete-wrapper">
      <input
        ref={inputRef}
        type="text"
        value={displayValue}
        onChange={handleInputChange}
        placeholder={placeholder}
        className={`${className} ${isLoading ? 'loading' : ''}`}
        disabled={disabled || isLoading}
        autoComplete="off"
      />
      {isLoading && <div className="autocomplete-loading">Loading...</div>}
    </div>
  );
};

export default GooglePlacesAutocomplete;