import React, { useEffect, useState } from 'react';
import './Dashboard.css';

function Dashboard() {
	const [stats, setStats] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	useEffect(() => {
		const fetchDashboard = async () => {
			try {
				const apiUrl = 'http://localhost:8000/api/health';
				console.log('Fetching from:', apiUrl);
				
				const response = await fetch(apiUrl, {
					method: 'GET',
					headers: {
						'Content-Type': 'application/json',
					},
					mode: 'cors',
					credentials: 'omit'
				});
				
				console.log('Response status:', response.status);
				
				if (!response.ok) {
					throw new Error(`HTTP error! status: ${response.status}`);
				}
				
				const data = await response.json();
				console.log('Response data:', data);
				
				setStats({
					apiStatus: 'Running',
					timestamp: new Date().toLocaleString(),
          message: data.message
        });
      } catch (err) {
        console.error('Error:', err);
        setError(`Failed to connect to API: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      
      <div className="stats-grid">
        <div className="card">
          <h3>System Status</h3>
          <p className={stats?.apiStatus === 'Running' ? 'status-ok' : 'status-error'}>
            {stats?.apiStatus || 'Unknown'}
          </p>
          <small>{stats?.timestamp}</small>
        </div>

        <div className="card">
          <h3>API Documentation</h3>
          <p>Visit <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
            API Docs
          </a> to explore all endpoints</p>
        </div>

        <div className="card">
          <h3>Features Available</h3>
          <ul>
            <li>Fraud Detection</li>
            <li>Anomaly Detection</li>
            <li>Portfolio Optimization</li>
            <li>Market Prediction</li>
          </ul>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
    </div>
  );
}

export default Dashboard;
