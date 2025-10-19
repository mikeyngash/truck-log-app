import React, { useState } from 'react';

const TripForm = ({ formData, onChange, onSubmit, loading }) => {
  const [searchTerms, setSearchTerms] = useState({
    current_location: formData.current_location || '',
    pickup_location: formData.pickup_location || '',
    dropoff_location: formData.dropoff_location || ''
  });
  const [suggestions, setSuggestions] = useState({
    current_location: [],
    pickup_location: [],
    dropoff_location: []
  });
  const [showSuggestions, setShowSuggestions] = useState({
    current_location: false,
    pickup_location: false,
    dropoff_location: false
  });

  const searchLocations = async (field, query) => {
    if (query.length < 3) {
      setSuggestions(prev => ({ ...prev, [field]: [] }));
      return;
    }
    
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/locations/search/?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSuggestions(prev => ({ ...prev, [field]: data }));
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const handleSearchChange = (field, value) => {
    setSearchTerms(prev => ({ ...prev, [field]: value }));
    setShowSuggestions(prev => ({ ...prev, [field]: true }));
    searchLocations(field, value);
    // Also update the form data
    onChange({ target: { name: field, value } });
  };

  const handleSuggestionClick = (field, suggestion) => {
    setSearchTerms(prev => ({ ...prev, [field]: suggestion.name }));
    onChange({ target: { name: field, value: suggestion.name } });
    setShowSuggestions(prev => ({ ...prev, [field]: false }));
  };

  return (
    <form onSubmit={onSubmit}>
      {/* Current Location */}
      <div>
        <label htmlFor="current_location">Current Location:</label>
        <div className="autocomplete-container">
          <input
            id="current_location"
            type="text"
            value={searchTerms.current_location}
            onChange={(e) => handleSearchChange('current_location', e.target.value)}
            onFocus={() => setShowSuggestions(prev => ({ ...prev, current_location: true }))}
            onBlur={() => setTimeout(() => setShowSuggestions(prev => ({ ...prev, current_location: false })), 200)}
            placeholder="Enter location (e.g., Green Bay, WI)"
            required
            aria-label="Enter your current location"
          />
          {showSuggestions.current_location && suggestions.current_location.length > 0 && (
            <ul className="suggestions-list">
              {suggestions.current_location.map((suggestion, index) => (
                <li 
                  key={index}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSuggestionClick('current_location', suggestion);
                  }}
                >
                  {suggestion.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Pickup Location */}
      <div>
        <label htmlFor="pickup_location">Pickup Location:</label>
        <div className="autocomplete-container">
          <input
            id="pickup_location"
            type="text"
            value={searchTerms.pickup_location}
            onChange={(e) => handleSearchChange('pickup_location', e.target.value)}
            onFocus={() => setShowSuggestions(prev => ({ ...prev, pickup_location: true }))}
            onBlur={() => setTimeout(() => setShowSuggestions(prev => ({ ...prev, pickup_location: false })), 200)}
            placeholder="Enter location (e.g., Fond du Lac, WI)"
            required
            aria-label="Enter pickup location"
          />
          {showSuggestions.pickup_location && suggestions.pickup_location.length > 0 && (
            <ul className="suggestions-list">
              {suggestions.pickup_location.map((suggestion, index) => (
                <li 
                  key={index}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSuggestionClick('pickup_location', suggestion);
                  }}
                >
                  {suggestion.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Dropoff Location */}
      <div>
        <label htmlFor="dropoff_location">Dropoff Location:</label>
        <div className="autocomplete-container">
          <input
            id="dropoff_location"
            type="text"
            value={searchTerms.dropoff_location}
            onChange={(e) => handleSearchChange('dropoff_location', e.target.value)}
            onFocus={() => setShowSuggestions(prev => ({ ...prev, dropoff_location: true }))}
            onBlur={() => setTimeout(() => setShowSuggestions(prev => ({ ...prev, dropoff_location: false })), 200)}
            placeholder="Enter location (e.g., Edwardsville, IL)"
            required
            aria-label="Enter dropoff location"
          />
          {showSuggestions.dropoff_location && suggestions.dropoff_location.length > 0 && (
            <ul className="suggestions-list">
              {suggestions.dropoff_location.map((suggestion, index) => (
                <li 
                  key={index}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSuggestionClick('dropoff_location', suggestion);
                  }}
                >
                  {suggestion.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Current Cycle Hours */}
      <div>
        <label htmlFor="current_cycle_hours">Current Cycle Hours:</label>
        <input
          id="current_cycle_hours"
          type="number"
          name="current_cycle_hours"
          value={formData.current_cycle_hours}
          onChange={(e) => {
            const value = parseFloat(e.target.value) || 0;
            onChange({ target: { name: 'current_cycle_hours', value } });
          }}
          step="0.1"
          min="0"
          required
          aria-label="Enter current cycle hours"
        />
      </div>

      {/* Sleeper Berth */}
      <div>
        <label htmlFor="use_sleeper_berth">
          <input
            id="use_sleeper_berth"
            type="checkbox"
            name="use_sleeper_berth"
            checked={formData.use_sleeper_berth}
            onChange={(e) => onChange({ target: { name: 'use_sleeper_berth', value: e.target.checked } })}
            aria-label="Use sleeper berth for breaks"
          />
          Use Sleeper Berth (splits 10+ hour breaks into 7 hours berth + 3 hours off-duty)
        </label>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Generating...' : 'Generate Route & Logs'}
      </button>
    </form>
  );
};

export default TripForm;
