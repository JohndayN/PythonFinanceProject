import React, { useState } from "react";
import "./Pages.css";

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
            onChange={(e) => setDays(e.target.value)}
          />
        </div>

        <button onClick={handlePredict} disabled={loading}>
          {loading ? "Predicting..." : "Predict Prices"}
        </button>

        {results && (
          <div className="results">

            <h4>Prediction Trend ({results.ticker})</h4>

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
        )}

      </div>

    </div>
  );
}

export default MarketPrediction;