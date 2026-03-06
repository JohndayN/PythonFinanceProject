/**
 * Anomaly Detection Routes
 * Endpoints for anomaly detection in market data
 */

const express = require("express");
const router = express.Router();
const anomalyController = require("../controllers/anomaly.controller");

/**
 * POST /api/anomaly/detect/:ticker
 * Detect anomalies in market data for a ticker
 */
router.post("/anomaly/detect/:ticker", anomalyController.detectAnomalies);

/**
 * GET /api/anomaly/hose-market
 * Detect anomalies in HOSE market
 */
router.get("/anomaly/hose-market", anomalyController.detectHOSEAnomalies);

/**
 * GET /api/anomaly/results/:ticker
 * Get anomaly detection results for a ticker
 */
router.get("/anomaly/results/:ticker", anomalyController.getAnomalyResults);

/**
 * GET /api/anomaly/latest/:ticker
 * Get latest anomaly detection result for a ticker
 */
router.get("/anomaly/latest/:ticker", anomalyController.getLatestAnomalyResult);

/**
 * GET /api/anomaly/all
 * Get all recent anomaly detection results
 */
router.get("/anomaly/all", anomalyController.getAllAnomalyResults);

module.exports = router;
