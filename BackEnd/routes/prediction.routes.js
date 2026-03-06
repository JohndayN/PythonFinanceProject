/**
 * Market Prediction Routes
 * Endpoints for market prediction and forecasting
 */

const express = require("express");
const router = express.Router();
const predictionController = require("../controllers/prediction.controller");

/**
 * GET /api/prediction/forecast/:ticker
 * Get market prediction for a ticker
 */
router.get("/prediction/forecast/:ticker", predictionController.getPrediction);

/**
 * GET /api/prediction/results/:ticker
 * Get prediction results for a ticker
 */
router.get("/prediction/results/:ticker", predictionController.getPredictionResults);

/**
 * GET /api/prediction/latest/:ticker
 * Get latest prediction for a ticker
 */
router.get("/prediction/latest/:ticker", predictionController.getLatestPrediction);

/**
 * GET /api/prediction/compare
 * Compare predictions for multiple tickers
 */
router.get("/prediction/compare", predictionController.comparePredictions);

/**
 * GET /api/prediction/all
 * Get all recent predictions
 */
router.get("/prediction/all", predictionController.getAllPredictions);

module.exports = router;
