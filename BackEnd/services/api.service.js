/**
 * API Service - Proxies requests to Python FastAPI backend
 */

const axios = require("axios");

const PYTHON_API = process.env.PYTHON_API_URL || "http://localhost:8000";

// Create axios instance with default config
const apiClient = axios.create({
    baseURL: PYTHON_API,
    timeout: 30000,
    headers: {
        "Content-Type": "application/json"
    }
});

/**
 * Fetch market data for a ticker via Python API
 */
const getMarketData = async (ticker, startDate, endDate) => {
    try {
        const response = await apiClient.post("/api/scraper/market-data", {
            ticker: ticker.toUpperCase(),
            start_date: startDate,
            end_date: endDate
        });
        return response.data;
    } catch (error) {
        console.error(`Error fetching market data for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Fetch HOSE market data
 */
const getHOSEMarketData = async () => {
    try {
        const response = await apiClient.get("/api/scraper/hose-market");
        return response.data;
    } catch (error) {
        console.error("Error fetching HOSE market data:", error.message);
        throw error;
    }
};

/**
 * Get available tickers
 */
const getAvailableTickers = async () => {
    try {
        const response = await apiClient.get("/api/data/available-tickers");
        return response.data;
    } catch (error) {
        console.error("Error fetching available tickers:", error.message);
        throw error;
    }
};

/**
 * Detect anomalies in market data
 */
const detectAnomalies = async (ticker, startDate, endDate) => {
    try {
        const response = await apiClient.post("/api/anomaly/detect", {
            ticker: ticker.toUpperCase(),
            start_date: startDate,
            end_date: endDate
        });
        return response.data;
    } catch (error) {
        console.error(`Error detecting anomalies for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Detect HOSE market anomalies
 */
const detectHOSEAnomalies = async () => {
    try {
        const response = await apiClient.get("/api/anomaly/hose-market");
        return response.data;
    } catch (error) {
        console.error("Error detecting HOSE anomalies:", error.message);
        throw error;
    }
};

/**
 * Detect fraud from CSV file
 */
const detectFraudCSV = async (fileBuffer, filename) => {
    try {
        const FormData = require("form-data");
        const form = new FormData();
        form.append("file", fileBuffer, filename);

        const response = await apiClient.post("/api/fraud/csv", form, {
            headers: form.getHeaders()
        });
        return response.data;
    } catch (error) {
        console.error("Error detecting fraud from CSV:", error.message);
        throw error;
    }
};

/**
 * Detect fraud from PDF file
 */
const detectFraudPDF = async (fileBuffer, filename) => {
    try {
        const FormData = require("form-data");
        const form = new FormData();
        form.append("file", fileBuffer, filename);

        const response = await apiClient.post("/api/fraud/pdf", form, {
            headers: form.getHeaders()
        });
        return response.data;
    } catch (error) {
        console.error("Error detecting fraud from PDF:", error.message);
        throw error;
    }
};

/**
 * Comprehensive fraud detection
 */
const detectComprehensiveFraud = async (fileBuffer, filename, ticker) => {
    try {
        const FormData = require("form-data");
        const form = new FormData();
        form.append("file", fileBuffer, filename);
        if (ticker) form.append("ticker", ticker);

        const response = await apiClient.post("/api/fraud/comprehensive", form, {
            headers: form.getHeaders()
        });
        return response.data;
    } catch (error) {
        console.error("Error in comprehensive fraud detection:", error.message);
        throw error;
    }
};

/**
 * Optimize portfolio
 */
const optimizePortfolio = async (tickers, riskAversion, fraudPenalty, startDate, endDate) => {
    try {
        const response = await apiClient.post("/api/portfolio/optimize", {
            tickers: tickers.map(t => t.toUpperCase()),
            risk_aversion: riskAversion || 0.6,
            fraud_penalty: fraudPenalty || 0.8,
            start_date: startDate,
            end_date: endDate
        });
        return response.data;
    } catch (error) {
        console.error("Error optimizing portfolio:", error.message);
        throw error;
    }
};

/**
 * Get market prediction
 */
const getMarketPrediction = async (ticker, days) => {
    try {
        const response = await apiClient.get(`/api/prediction/forecast/${ticker.toUpperCase()}`, {
            params: { days: days || 5 }
        });
        return response.data;
    } catch (error) {
        console.error(`Error getting prediction for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Health check on Python API
 */
const healthCheck = async () => {
    try {
        const response = await apiClient.get("/api/health");
        return response.data;
    } catch (error) {
        return {
            status: "error",
            message: "Python API is not responding"
        };
    }
};

module.exports = {
    apiClient,
    getMarketData,
    getHOSEMarketData,
    getAvailableTickers,
    detectAnomalies,
    detectHOSEAnomalies,
    detectFraudCSV,
    detectFraudPDF,
    detectComprehensiveFraud,
    optimizePortfolio,
    getMarketPrediction,
    healthCheck
};
