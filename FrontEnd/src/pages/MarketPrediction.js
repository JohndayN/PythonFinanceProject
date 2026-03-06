import React, { useState } from 'react';
import './Pages.css';

function MarketPrediction() {
  const [stock, setStock] = useState('FPT');
  const [days, setDays] = useState('30');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePredict = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/prediction/forecast/${stock}?days=${days}`,
        { mode: 'cors', credentials: 'omit' }
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to predict market: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1>Market Prediction</h1>
      
      <div className="card">
        <h3>Predict Stock Prices</h3>
        <div className="form-group">
          <label>Stock Symbol:</label>
          <input 
            type="text" 
            value={stock}
            onChange={(e) => setStock(e.target.value)}
            placeholder="e.g., FPT"
          />
        </div>
        <div className="form-group">
          <label>Days to Predict:</label>
          <input 
            type="number" 
            value={days}
            onChange={(e) => setDays(e.target.value)}
            min="1"
            max="365"
          />
        </div>
        <button 
          onClick={handlePredict}
          disabled={loading}
        >
          {loading ? 'Predicting...' : 'Predict Prices'}
        </button>

        {results && (
          <div className="results">
            <h4>Prediction Results</h4>
            <pre>{JSON.stringify(results, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default MarketPrediction;
