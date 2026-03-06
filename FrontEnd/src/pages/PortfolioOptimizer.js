import React, { useState, useEffect } from 'react';
import { Pie } from "react-chartjs-2";
import './Pages.css';
import { Chart as ChartJS, ArcElement, Tooltip, Legend} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

function PortfolioOptimizer() {
  const [availableTickers, setAvailableTickers] = useState([]);
  useEffect(() => {
    fetch("http://localhost:8000/api/data/available-tickers")
      .then(res => res.json())
      .then(data => setAvailableTickers(data.tickers || []))
      .catch(() => setAvailableTickers(['FPT','HPG','VNM']));
  }, []);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stocks, setStocks] = useState('FPT,HPG,VNM');

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const stockList = stocks.split(',').map(s => s.trim()).filter(s => s);
      const response = await fetch(
        `http://localhost:8000/api/portfolio/optimize`,
        { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          mode: 'cors', 
          credentials: 'omit',
          body: JSON.stringify({ tickers: stockList })
        }
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to optimize portfolio: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1>Portfolio Optimizer</h1>
      
      <div className="card">
        <h3>Optimize Your Portfolio</h3>
        <div className="form-group">
          <label>Stocks (comma-separated):</label>
          <input 
            type="text" 
            value={stocks}
            onChange={(e) => setStocks(e.target.value)}
            placeholder="e.g., FPT,HPG,VNM"
          />
        </div>
        <button 
          onClick={handleOptimize}
          disabled={loading}
        >
          {loading ? 'Optimizing...' : 'Optimize Portfolio'}
        </button>

        {results && (
          <div className="results">
            <h4>Optimized Portfolio</h4>

            <table className="data-table">
              <thead>
                <tr>
                  <th>Stock</th>
                  <th>Weight</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(results.weights || {}).map(([ticker, weight]) => (
                  <tr key={ticker}>
                    <td>{ticker}</td>
                    <td>{(weight * 100).toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="portfolio-metrics">
              <p><strong>Expected Return:</strong> {(results.expected_return * 100).toFixed(2)}%</p>
              <p><strong>Volatility:</strong> {(results.volatility * 100).toFixed(2)}%</p>
              <p><strong>Sharpe Ratio:</strong> {results.sharpe_ratio?.toFixed(2)}</p>
            </div>
          </div>
        )}

        {results && (
          <Pie
            data={{
              labels: Object.keys(results.weights || {}),
              datasets: [
                {
                  data: Object.values(results.weights || {}),
                },
              ],
            }}
          />
        )}
      </div>
    </div>
  );
}

export default PortfolioOptimizer;
