/**
 * Fraud Detection Controller
 * Handles fraud detection and risk analysis operations
 */

const mongoService = require("../services/mongo.service");
const apiService = require("../services/api.service");

/**
 * POST /api/fraud/csv
 * Detect fraud from CSV file
 */
exports.detectFraudCSV = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({
                error: "No file uploaded"
            });
        }

        const fileBuffer = req.file.buffer || Buffer.from(req.file.data);
        const filename = req.file.originalname;

        // Call Python API for fraud detection
        const fraudResult = await apiService.detectFraudCSV(fileBuffer, filename);

        // Save to MongoDB
        const savedResult = await mongoService.saveFraudResult(fraudResult);

        res.json({
            ...fraudResult,
            _id: savedResult._id,
            saved: true
        });
    } catch (error) {
        console.error("Error in detectFraudCSV:", error.message);
        res.status(400).json({
            error: "Fraud detection failed",
            message: error.message
        });
    }
};

/**
 * POST /api/fraud/pdf
 * Detect fraud from PDF file
 */
exports.detectFraudPDF = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({
                error: "No file uploaded"
            });
        }

        const fileBuffer = req.file.buffer || Buffer.from(req.file.data);
        const filename = req.file.originalname;

        // Call Python API for fraud detection
        const fraudResult = await apiService.detectFraudPDF(fileBuffer, filename);

        // Save to MongoDB
        const savedResult = await mongoService.saveFraudResult(fraudResult);

        res.json({
            ...fraudResult,
            _id: savedResult._id,
            saved: true
        });
    } catch (error) {
        console.error("Error in detectFraudPDF:", error.message);
        res.status(400).json({
            error: "Fraud detection failed",
            message: error.message
        });
    }
};

/**
 * POST /api/fraud/comprehensive
 * Comprehensive fraud detection (PDF + news sentiment)
 */
exports.detectComprehensiveFraud = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({
                error: "No file uploaded"
            });
        }

        const fileBuffer = req.file.buffer || Buffer.from(req.file.data);
        const filename = req.file.originalname;
        const { ticker } = req.query;

        // Call Python API for comprehensive fraud detection
        const fraudResult = await apiService.detectComprehensiveFraud(fileBuffer, filename, ticker);

        // Save to MongoDB
        const savedResult = await mongoService.saveFraudResult(fraudResult);

        res.json({
            ...fraudResult,
            _id: savedResult._id,
            saved: true
        });
    } catch (error) {
        console.error("Error in detectComprehensiveFraud:", error.message);
        res.status(400).json({
            error: "Fraud detection failed",
            message: error.message
        });
    }
};

/**
 * GET /api/fraud/results/:ticker
 * Get fraud detection results for a ticker
 */
exports.getFraudResults = async (req, res) => {
    try {
        const { ticker } = req.params;
        const { limit = 10 } = req.query;

        const results = await mongoService.getFraudResults(ticker, parseInt(limit));

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No fraud detection results found for this ticker",
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
        console.error("Error in getFraudResults:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/fraud/risk/:ticker
 * Get latest fraud risk score for a ticker
 */
exports.getFraudRisk = async (req, res) => {
    try {
        const { ticker } = req.params;

        const riskScore = await mongoService.getRiskScores(ticker);

        if (!riskScore) {
            return res.status(404).json({
                error: "No risk score found for this ticker",
                ticker: ticker.toUpperCase()
            });
        }

        res.json({
            ticker: ticker.toUpperCase(),
            risk: riskScore,
            status: "success"
        });
    } catch (error) {
        console.error("Error in getFraudRisk:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/all-fraud-results
 * Get all recent fraud detection results
 */
exports.getAllFraudResults = async (req, res) => {
    try {
        const { limit = 50 } = req.query;
        const db = mongoService.getDB();
        const collection = db.collection("fraud_detection_results");

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
        console.error("Error in getAllFraudResults:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};