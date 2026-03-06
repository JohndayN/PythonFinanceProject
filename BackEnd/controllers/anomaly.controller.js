/**
 * Anomaly Detection Controller
 * Handles anomaly detection operations
 */

const mongoService = require("../services/mongo.service");
const apiService = require("../services/api.service");

/**
 * POST /api/anomaly/detect/:ticker
 * Detect anomalies in market data
 */
exports.detectAnomalies = async (req, res) => {
    try {
        const { ticker } = req.params;
        const { start_date, end_date } = req.query;

        // Call Python API for anomaly detection
        const anomalyResult = await apiService.detectAnomalies(ticker, start_date, end_date);

        // Save to MongoDB
        const savedResult = await mongoService.saveAnomalyResult(anomalyResult);

        res.json({
            ...anomalyResult,
            _id: savedResult._id,
            saved: true
        });
    } catch (error) {
        console.error("Error in detectAnomalies:", error.message);
        res.status(error.response?.status || 400).json({
            error: "Anomaly detection failed",
            message: error.message
        });
    }
};

/**
 * GET /api/anomaly/hose-market
 * Detect anomalies in HOSE market data
 */
exports.detectHOSEAnomalies = async (req, res) => {
    try {
        const anomalyResult = await apiService.detectHOSEAnomalies();

        res.json(anomalyResult);
    } catch (error) {
        console.error("Error in detectHOSEAnomalies:", error.message);
        res.status(error.response?.status || 500).json({
            error: "HOSE anomaly detection failed",
            message: error.message
        });
    }
};

/**
 * GET /api/anomaly/results/:ticker
 * Get anomaly detection results for a ticker
 */
exports.getAnomalyResults = async (req, res) => {
    try {
        const { ticker } = req.params;
        const { limit = 10 } = req.query;

        const results = await mongoService.getAnomalyResults(ticker, parseInt(limit));

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No anomaly detection results found for this ticker",
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
        console.error("Error in getAnomalyResults:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/anomaly/latest/:ticker
 * Get latest anomaly detection result for a ticker
 */
exports.getLatestAnomalyResult = async (req, res) => {
    try {
        const { ticker } = req.params;

        const results = await mongoService.getAnomalyResults(ticker, 1);

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No anomaly detection results found for this ticker",
                ticker: ticker.toUpperCase()
            });
        }

        res.json({
            ticker: ticker.toUpperCase(),
            result: results[0],
            status: "success"
        });
    } catch (error) {
        console.error("Error in getLatestAnomalyResult:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/anomaly/all
 * Get all recent anomaly detection results
 */
exports.getAllAnomalyResults = async (req, res) => {
    try {
        const { limit = 50 } = req.query;
        const db = mongoService.getDB();
        const collection = db.collection("anomaly_detection_results");

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
        console.error("Error in getAllAnomalyResults:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};
