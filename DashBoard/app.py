import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Import your modules
from Scraper.HOSE.GetHOSEMarketData import get_hose_market_data
from FeatureEngineering.hose_market_features import create_hose_market_features
from AnomalyDetection.HoseMarketIsolationForest import compute_hose_market_anomaly

st.set_page_config(layout="wide")

st.title("Vietnam Stock Fraud & Anomaly Dashboard")

# Load Hose Market data
st.sidebar.header("Settings")

selected_ticker = st.sidebar.text_input("Ticker", "VCB")

if st.sidebar.button("Refresh Data"):

    Hose_market_df = get_hose_market_data()
    features = create_hose_market_features(Hose_market_df)
    anomaly_df = compute_hose_market_anomaly(features)

    merged = Hose_market_df.merge(
        anomaly_df,
        left_on="securitySymbol",
        right_on="securitySymbol"
    )

    stock_data = merged[merged["securitySymbol"] == selected_ticker]

    if stock_data.empty:
        st.error("Ticker not found")
    else:

        row = stock_data.iloc[0]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Price Change %",
            f"{row['price_change_pct']:.2%}"
        )

        col2.metric(
            "Volume",
            f"{int(row['totalShare']):,}"
        )

        col3.metric(
            "Hose Market Anomaly Score",
            f"{row['Hose Market_anomaly_score']:.4f}"
        )

    
        # Cross-stock anomaly comparison
    

        st.subheader("Market-wide Hose Market Anomalies")

        fig = px.bar(
            merged.sort_values("Hose Market_anomaly_score", ascending=False).head(20),
            x="securitySymbol",
            y="Hose Market_anomaly_score",
            title="Top 20 Anomaly Scores"
        )

        st.plotly_chart(fig, use_container_width=True)