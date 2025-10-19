import React, { useState } from 'react';
import axios from 'axios';
import TripForm from './components/TripForm';
import MapView from './components/MapView';
import ResultPanel from './components/ResultPanel';
import LogGridSvg from './components/LogGridSvg';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    current_location: '',
    pickup_location: '',
    dropoff_location: '',
    current_cycle_hours: 0,
    use_sleeper_berth: false
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [routePositions, setRoutePositions] = useState([]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post('https://app-production-6389.up.railway.app/api/trip/', formData);
      setResult(res.data);

      // Use the route coordinates from the response if available
      if (res.data.route_coordinates && res.data.route_coordinates.length > 0) {
        setRoutePositions(res.data.route_coordinates);
      } else if (res.data.locations) {
        // Fallback to simple positions from locations
        const positions = res.data.locations.map(loc => [loc.lat, loc.lon]);
        setRoutePositions(positions);
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      if (error.response && error.response.data) {
        // Display specific error messages from the backend
        const errorMsg = typeof error.response.data === 'string' 
          ? error.response.data 
          : JSON.stringify(error.response.data);
        setError(`Failed to generate route and logs: ${errorMsg}`);
      } else {
        setError('Failed to generate route and logs. Please check your inputs and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Truck Log App</h1>
      <div className="app-grid">
        <TripForm formData={formData} onChange={handleChange} onSubmit={handleSubmit} loading={loading} />
        <ResultPanel result={result} loading={loading} error={error} />
        <div className="full">
          <LogGridSvg data={result?.logs} />
        </div>
        <div className="full">
          <MapView routePositions={routePositions} />
        </div>
      </div>
    </div>
  );
}

export default App;
