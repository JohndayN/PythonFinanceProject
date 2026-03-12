import React from "react";
import Plot from "react-plotly.js";

function CandlestickChart({ data = [], predictions = []}) {

  if (!data || data.length === 0) {
    return <p>No historical data available</p>;
  }

  // remove rows with missing OHLC
  const cleanData = data.filter(
    d => d.open != null && d.high != null && d.low != null && d.close != null
  );

  const dates = cleanData.map(d => d.date);
  const open = cleanData.map(d => d.open);
  const high = cleanData.map(d => d.high);
  const low = cleanData.map(d => d.low);
  const close = cleanData.map(d => d.close);

  // Moving averages
  const ma20 = close.map((_, i, arr) =>
    i < 20 ? null :
    arr.slice(i - 20, i).reduce((a, b) => a + b, 0) / 20
  );

  const ma50 = close.map((_, i, arr) =>
    i < 50 ? null :
    arr.slice(i - 50, i).reduce((a, b) => a + b, 0) / 50
  );

  return (
    <div className="candlestick-wrapper">

      <Plot
        data={[
          {
            x: dates,
            open: open,
            high: high,
            low: low,
            close: close,
            type: "candlestick",
            name: "Price",

            increasing: {
              line: { color: "#16a34a" }
            },

            decreasing: {
              line: { color: "#dc2626" }
            }
          },

          {
            x: dates,
            y: ma20,
            type: "scatter",
            mode: "lines",
            name: "MA20",
            line: { color: "#3b82f6", width: 2 }
          },

          {
            x: dates,
            y: ma50,
            type: "scatter",
            mode: "lines",
            name: "MA50",
            line: { color: "#f59e0b", width: 2 }
          }
        ]}

        layout={{
          title: "Stock Price Chart",
          dragmode: "zoom",
          showlegend: true,

          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",

          xaxis: {
            rangeslider: { visible: false },
            showgrid: false
          },

          yaxis: {
            showgrid: true,
            gridcolor: "rgba(200,200,200,0.2)"
          },

          margin: { t: 40, l: 50, r: 30, b: 40 },
          height: 500
        }}

        config={{
          responsive: true,
          displayModeBar: true
        }}

        style={{ width: "100%" }}
      />

    </div>
  );
}

export default CandlestickChart;
