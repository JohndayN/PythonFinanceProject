import React from "react";
import Plot from "react-plotly.js";

function CandlestickChart({ data }) {

  const dates = data.map(d => d.date);
  const open = data.map(d => d.open);
  const high = data.map(d => d.high);
  const low = data.map(d => d.low);
  const close = data.map(d => d.close);

  // Moving averages
  const ma20 = data.map((_, i, arr) =>
    i < 20 ? null :
    arr.slice(i - 20, i).reduce((a, b) => a + b.close, 0) / 20
  );

  const ma50 = data.map((_, i, arr) =>
    i < 50 ? null :
    arr.slice(i - 50, i).reduce((a, b) => a + b.close, 0) / 50
  );

  return (
    <Plot
      data={[
        {
          x: dates,
          open,
          high,
          low,
          close,
          type: "candlestick",
          name: "Price"
        },
        {
          x: dates,
          y: ma20,
          type: "scatter",
          mode: "lines",
          name: "MA20",
          line: { color: "blue" }
        },
        {
          x: dates,
          y: ma50,
          type: "scatter",
          mode: "lines",
          name: "MA50",
          line: { color: "orange" }
        }
      ]}
      layout={{
        title: "Stock Price Chart",
        dragmode: "zoom",
        showlegend: true,
        xaxis: { rangeslider: { visible: false } },
        height: 500
      }}
      style={{ width: "100%" }}
    />
  );
}

export default CandlestickChart;