import React, { useState } from "react";
import "./Pages.css";
import CandlestickChart from "../components/CandlestickChart";
import PredictionConfidenceChart from "../components/PredictionConfidenceChart";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

function MarketPrediction() {

  const [stock, setStock] = useState("FPT");
  const [days, setDays] = useState(30);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePredict = async () => {
    setResults(null);
    setLoading(true);

    try {
      const response = await fetch(
        `http://localhost:8000/api/prediction/forecast/${stock}?days=${days}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      setResults(data);

    } catch (err) {
      console.error(err);
      alert("Prediction failed");
    }

    setLoading(false);
  };

  // Convert predictions → chart format
  let chartData = [];

  if (results && results.predictions) {
    chartData = results.predictions.map((price, index) => ({
      day: index + 1,
      price: Number(price.toFixed(2))
    }));
  }

  // Add prediction summary after chart data
  let firstPrice = null;
  let lastPrice = null;
  let change = null;

  if (chartData.length > 0) {
    firstPrice = chartData[0].price;
    lastPrice = chartData[chartData.length - 1].price;
    change = ((lastPrice - firstPrice) / firstPrice) * 100;
  }

  return (
    <div className="page">

      <h1>Market Prediction</h1>

      <div className="card">

        <h3>Predict Stock Prices</h3>

        <div className="form-group">
          <label>Stock Symbol</label>
          <input
            type="text"
            value={stock}
            onChange={(e) => setStock(e.target.value.toUpperCase())}
          />
        </div>

        <div className="form-group">
          <label>Days to Predict</label>
          <input
            type="number"
            value={days}
            min="1"
            max="365"
            onChange={(e) => setDays(Number(e.target.value))}
          />
        </div>

        <button onClick={handlePredict} disabled={loading}>
          {loading ? "Predicting..." : "Predict Prices"}
        </button>

        {results && (
          <>

            <div className="prediction-summary">

              <div className="summary-box">
                <div className="summary-title">Start Price</div>
                <div className="summary-value">{firstPrice}</div>
              </div>

              <div className="summary-box">
                <div className="summary-title">Predicted Price</div>
                <div className="summary-value">{lastPrice}</div>
              </div>

              <div className="summary-box">
                <div className="summary-title">Expected Change</div>
                <div className={`summary-value ${change > 0 ? "positive" : "negative"}`}>
                  {change?.toFixed(2)}%
                </div>
              </div>

            </div>

            <div className="results">

              <h4>Prediction Trend ({results.ticker})</h4>
              <div className="chart-container">

                <ResponsiveContainer width="100%" height={350}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />

                    <XAxis
                      dataKey="day"
                      label={{
                        value: "Future Days",
                        position: "insideBottomRight",
                        offset: -5
                      }}
                    />

                    <YAxis
                      label={{
                        value: "Price",
                        angle: -90,
                        position: "insideLeft"
                      }}
                    />

                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke="#0284c7"
                      strokeWidth={3}
                      dot={false}
                    />

                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="card">

                <PredictionConfidenceChart
                  predictions={results.predictions}
                  upper={results.upper}
                  lower={results.lower}
                />

              </div>

            </div>

            {results?.historical && (
              <CandlestickChart
                data={results.historical}
                predictions={results.predictions}
              />
            )}

            <table className="prediction-table">
              <thead>
                <tr>
                  <th>Day</th>
                  <th>Predicted Price</th>
                </tr>
              </thead>

              <tbody>
                {chartData.map((row) => (
                  <tr key={row.day}>
                    <td>{row.day}</td>
                    <td>{row.price.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

      </div>

    </div>
  );
}

export default MarketPrediction;