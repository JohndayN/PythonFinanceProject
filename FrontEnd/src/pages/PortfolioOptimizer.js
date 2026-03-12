import React, { useState, useEffect } from "react";
import { Pie, Scatter } from "react-chartjs-2";
import "./Pages.css";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  LinearScale,
  Title
} from "chart.js";

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  PointElement,
  LineElement,
  LinearScale,
  Title
);

function PortfolioOptimizer() {

  const [availableTickers, setAvailableTickers] = useState([]);
  const [stocks, setStocks] = useState("FPT,HPG,VNM");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  // ================= FETCH AVAILABLE TICKERS =================
  useEffect(() => {

    fetch("http://localhost:8000/api/data/available-tickers")
      .then(res => res.json())
      .then(data => {
        setAvailableTickers(data.tickers || []);
      })
      .catch(() => {
        setAvailableTickers(["FPT","HPG","VNM"]);
      });

  }, []);

  // ================= OPTIMIZE =================
  const handleOptimize = async () => {

    const stockList = stocks
      .split(",")
      .map(s => s.trim().toUpperCase())
      .filter(Boolean);

    if (stockList.length === 0) {
      alert("Please enter at least 1 ticker.");
      return;
    }

    setLoading(true);
    setResults(null);

    try {

      const response = await fetch(
        "http://localhost:8000/api/portfolio/optimize",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tickers: stockList
          })
        }
      );

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);

    } catch (error) {

      console.error(error);
      alert("Portfolio optimization failed");

    } finally {

      setLoading(false);

    }
  };

  // ================= PIE COLORS =================
  const pieColors = [
    "#4CAF50",
    "#2196F3",
    "#FFC107",
    "#FF5722",
    "#9C27B0",
    "#00BCD4",
    "#E91E63"
  ];

  // ================= PIE DATA =================
  const pieData = results
    ? {
        labels: Object.keys(results.weights || {}),
        datasets: [
          {
            data: Object.values(results.weights || {}),
            backgroundColor: pieColors,
            borderWidth: 1
          }
        ]
      }
    : null;

  // ================= EFFICIENT FRONTIER + CONFIDENCE BAND =================
  const frontierData = results?.efficient_frontier
    ? {
        datasets: [

          // Efficient Frontier
          {
            label: "Efficient Frontier",
            data: results.efficient_frontier.map(p => ({
              x: p.risk,
              y: p.return
            })),
            borderColor: "#2196F3",
            backgroundColor: "#2196F3",
            showLine: true,
            tension: 0.3,
            fill: false
          },

          // Optimal Portfolio
          {
            label: "Optimal Portfolio",
            data: [{
              x: results.volatility,
              y: results.expected_return
            }],
            backgroundColor: "red",
            pointRadius: 6
          },

          // Upper Confidence Band
          {
            type: "line",
            label: "Upper Confidence",
            data: results.frontier_confidence_band
              ? results.frontier_confidence_band.map(p => ({
                  x: p.risk,
                  y: p.upper
                }))
              : [],
            borderColor: "rgba(0,200,83,0.5)",
            backgroundColor: "rgba(0,200,83,0.2)",
            showLine: true,
            tension: 0.3,
            pointRadius: 0
          },

          // Lower Confidence Band
          {
            type: "line",
            label: "Lower Confidence",
            data: results.frontier_confidence_band
              ? results.frontier_confidence_band.map(p => ({
                  x: p.risk,
                  y: p.lower
                }))
              : [],
            borderColor: "rgba(255,82,82,0.5)",
            backgroundColor: "rgba(255,82,82,0.2)",
            showLine: true,
            tension: 0.3,
            pointRadius: 0
          }

        ]
      }
    : null;

  // ================= FRONTIER OPTIONS =================
  const frontierOptions = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: {
        display: true,
        text: "Efficient Frontier with Confidence Band"
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `Return: ${(context.raw.y * 100).toFixed(2)}% | Risk: ${(context.raw.x * 100).toFixed(2)}%`;
          }
        }
      }
    },
    scales: {
      x: {
        type: "linear",
        position: "bottom",
        title: {
          display: true,
          text: "Risk (Volatility)"
        }
      },
      y: {
        title: {
          display: true,
          text: "Expected Return"
        }
      }
    }
  };

  return (

    <div className="page">

      <h1>Portfolio Optimizer</h1>

      <div className="card">

        <h3>Optimize Your Portfolio</h3>

        <div className="form-group">
          <label>Stocks (comma separated)</label>

          <input
            type="text"
            value={stocks}
            onChange={(e) => setStocks(e.target.value)}
            placeholder="FPT,HPG,VNM"
          />
        </div>

        <button
          onClick={handleOptimize}
          disabled={loading}
        >
          {loading ? "Optimizing..." : "Optimize Portfolio"}
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

                {Object.entries(results.weights || {}).map(
                  ([ticker, weight]) => (

                  <tr key={ticker}>
                    <td>{ticker}</td>
                    <td>{(weight * 100).toFixed(2)}%</td>
                  </tr>

                ))}

              </tbody>

            </table>

            <div className="portfolio-metrics">

              <div className="metric-card">
                <span className="metric-title">Expected Return</span>
                <span className="metric-value">
                  {(results.expected_return * 100).toFixed(2)}%
                </span>
              </div>

              <div className="metric-card">
                <span className="metric-title">Volatility</span>
                <span className="metric-value">
                  {(results.volatility * 100).toFixed(2)}%
                </span>
              </div>

              <div className="metric-card">
                <span className="metric-title">Sharpe Ratio</span>
                <span className="metric-value">
                  {results.sharpe_ratio?.toFixed(2)}
                </span>
              </div>

            </div>

            {pieData && (
              <div style={{ width: "400px", margin: "auto" }}>
                <Pie data={pieData} />
              </div>
            )}

            {frontierData && (
              <div style={{ width: "550px", margin: "40px auto" }}>
                <Scatter
                  data={frontierData}
                  options={frontierOptions}
                />
              </div>
            )}

          </div>

        )}

      </div>

    </div>

  );

}

export default PortfolioOptimizer;
