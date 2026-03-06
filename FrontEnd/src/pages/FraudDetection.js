import React, { useState } from 'react';
import './Pages.css';

function FraudDetection() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please select a file');
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/fraud/detect', {
        method: 'POST',
        body: formData,
        mode: 'cors',
        credentials: 'omit'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to process file: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1>Fraud Detection</h1>
      
      <div className="card">
        <h3>Upload Financial Data</h3>
        <input 
          type="file" 
          onChange={handleFileChange}
          accept=".csv,.pdf"
        />
        <button 
          onClick={handleUpload}
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Analyze for Fraud'}
        </button>

        {results && (
          <div className="results">
            <h4>Results</h4>
            <pre>{JSON.stringify(results, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default FraudDetection;
