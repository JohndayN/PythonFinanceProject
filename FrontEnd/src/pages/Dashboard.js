import React, { useEffect, useState } from "react";
import "./Dashboard.css";

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/health");

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        const data = await response.json();

        setStats({
          apiStatus: "Running",
          timestamp: new Date().toLocaleString(),
          message: data.message,
        });
      } catch (err) {
        setError(`Failed to connect to API: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      <div className="stats-grid">
        <div className="card">
          <h3>System Status</h3>
          <p className={stats?.apiStatus === "Running" ? "status-ok" : "status-error"}>
            {stats?.apiStatus || "Unknown"}
          </p>
          <small>{stats?.timestamp}</small>
        </div>

        <div className="card">
          <h3>API Documentation</h3>
          <p>
            Visit{" "}
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
              API Docs
            </a>
          </p>
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