/**
 * Market Prediction Controller
 * Handles market prediction and forecasting
 */

const mongoService = require("../services/mongo.service");
const apiService = require("../services/api.service");

/**
 * GET /api/prediction/forecast/:ticker
 * Get market prediction for a ticker
 */
exports.getPrediction = async (req, res) => {
    try {
        const { ticker } = req.params;
        const { days = 5 } = req.query;

        // Call Python API for prediction
        const predictionResult = await apiService.getMarketPrediction(ticker, parseInt(days));

        // Save to MongoDB
        const savedResult = await mongoService.savePredictionResult(predictionResult);

        res.json({
            ...predictionResult,
            _id: savedResult._id,
            saved: true
        });
    } catch (error) {
        console.error("Error in getPrediction:", error.message);
        res.status(error.response?.status || 400).json({
            error: "Market prediction failed",
            message: error.message
        });
    }
};

/**
 * GET /api/prediction/results/:ticker
 * Get prediction results for a ticker
 */
exports.getPredictionResults = async (req, res) => {
    try {
        const { ticker } = req.params;
        const { limit = 5 } = req.query;

        const results = await mongoService.getPredictionResults(ticker, parseInt(limit));

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No prediction results found for this ticker",
                ticker: ticker.toUpperCase()
            });
        }

        res.json({
            ticker: ticker.toUpperCase(),
            count: results.length,
            results: results,
            status: "success"
        });
    } catch (error) {
        console.error("Error in getPredictionResults:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/prediction/latest/:ticker
 * Get latest prediction for a ticker
 */
exports.getLatestPrediction = async (req, res) => {
    try {
        const { ticker } = req.params;

        const results = await mongoService.getPredictionResults(ticker, 1);

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No prediction results found for this ticker",
                ticker: ticker.toUpperCase()
            });
        }

        res.json({
            ticker: ticker.toUpperCase(),
            result: results[0],
            status: "success"
        });
    } catch (error) {
        console.error("Error in getLatestPrediction:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/prediction/compare
 * Compare predictions for multiple tickers
 */
exports.comparePredictions = async (req, res) => {
    try {
        const { tickers, days = 5 } = req.query;

        if (!tickers) {
            return res.status(400).json({
                error: "Tickers are required"
            });
        }

        const tickerArray = Array.isArray(tickers) ? tickers : [tickers];
        const predictions = [];

        for (const ticker of tickerArray) {
            try {
                const prediction = await apiService.getMarketPrediction(ticker, parseInt(days));
                predictions.push(prediction);
            } catch (error) {
                console.warn(`Error getting prediction for ${ticker}:`, error.message);
            }
        }

        if (predictions.length === 0) {
            return res.status(400).json({
                error: "Failed to get predictions for any ticker"
            });
        }

        res.json({
            count: predictions.length,
            predictions: predictions,
            days: parseInt(days),
            status: "success"
        });
    } catch (error) {
        console.error("Error in comparePredictions:", error.message);
        res.status(400).json({
            error: "Prediction comparison failed",
            message: error.message
        });
    }
};

/**
 * GET /api/prediction/all
 * Get all recent predictions
 */
exports.getAllPredictions = async (req, res) => {
    try {
        const { limit = 50 } = req.query;
        const db = mongoService.getDB();
        const collection = db.collection("market_prediction_results");

        const results = await collection
            .find({})
            .sort({ timestamp: -1 })
            .limit(parseInt(limit))
            .toArray();

        res.json({
            count: results.length,
            results: results,
            status: "success"
        });
    } catch (error) {
        console.error("Error in getAllPredictions:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};
