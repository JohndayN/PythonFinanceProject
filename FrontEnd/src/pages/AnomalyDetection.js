import React, { useState } from 'react';
import './Pages.css';

function AnomalyDetection() {
  const [stock, setStock] = useState('FPT');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleDetect = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/anomaly/detect`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          mode: 'cors', 
          credentials: 'omit',
          body: JSON.stringify({ ticker: stock })
        }
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to detect anomalies: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1>Anomaly Detection</h1>
      
      <div className="card">
        <h3>Detect Market Anomalies</h3>
        <div className="form-group">
          <label>Stock Symbol:</label>
          <input 
            type="text" 
            value={stock}
            onChange={(e) => setStock(e.target.value)}
            placeholder="e.g., FPT, HPG, VNM"
          />
        </div>
        <button 
          onClick={handleDetect}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Detect Anomalies'}
        </button>

        {results && (
          <div className="results">
            <h4>Anomaly Detection Results</h4>
            <pre>{JSON.stringify(results, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnomalyDetection;
