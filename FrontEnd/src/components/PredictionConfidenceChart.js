import React from "react";
import Plot from "react-plotly.js";

function PredictionConfidenceChart({ predictions, upper, lower }) {

    if (!predictions) return null;

    const days = predictions.map((_, i) => `Day ${i+1}`);

    return (
        <Plot
        data={[
            {
            x: days,
            y: lower,
            type: "scatter",
            mode: "lines",
            line: { width: 0 },
            name: "Lower",
            showlegend: false
            },
            {
            x: days,
            y: upper,
            type: "scatter",
            mode: "lines",
            fill: "tonexty",
            fillcolor: "rgba(0,100,255,0.2)",
            line: { width: 0 },
            name: "Confidence Band"
            },
            {
            x: days,
            y: predictions,
            type: "scatter",
            mode: "lines",
            line: { color: "#0284c7", width: 3 },
            name: "Prediction"
            }
        ]}
        layout={{
            title: "Forecast with Confidence Band",
            xaxis: { title: "Future Days" },
            yaxis: { title: "Price" },
            height: 450
        }}
        style={{ width: "100%" }}
        />
    );
}

export default PredictionConfidenceChart;
