/**
 * Fraud Detection Routes
 * Endpoints for fraud detection and risk analysis
 */

const express = require("express");
const router = express.Router();
const multer = require("multer");
const fraudController = require("../controllers/fraud.controller");

// Configure multer for file uploads
const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 50 * 1024 * 1024 }, // 50MB limit
    fileFilter: (req, file, cb) => {
        const allowedMimes = ["text/csv", "application/pdf"];
        if (allowedMimes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error("Invalid file type. Only CSV and PDF files are allowed."));
        }
    }
});

/**
 * POST /api/fraud/csv
 * Upload CSV file for fraud detection
 */
router.post("/fraud/csv", upload.single("file"), fraudController.detectFraudCSV);

/**
 * POST /api/fraud/pdf
 * Upload PDF file for fraud detection
 */
router.post("/fraud/pdf", upload.single("file"), fraudController.detectFraudPDF);

/**
 * POST /api/fraud/comprehensive
 * Comprehensive fraud detection (PDF + news sentiment)
 */
router.post("/fraud/comprehensive", upload.single("file"), fraudController.detectComprehensiveFraud);

/**
 * GET /api/fraud/risk/:ticker
 * Get fraud risk score for a ticker
 */
router.get("/fraud/risk/:ticker", fraudController.getFraudRisk);

/**
 * GET /api/fraud/results/:ticker
 * Get fraud detection results for a ticker
 */
router.get("/fraud/results/:ticker", fraudController.getFraudResults);

/**
 * GET /api/fraud/all
 * Get all recent fraud detection results
 */
router.get("/fraud/all", fraudController.getAllFraudResults);

module.exports = router;