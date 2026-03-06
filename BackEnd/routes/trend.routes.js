/**
 * Trend Analysis Routes
 * Endpoints for market trend analysis
 */

const express = require("express");
const router = express.Router();
const trendController = require("../controllers/trend.controller");

/**
 * GET /api/trend/analyze/:ticker
 * Perform trend analysis on a ticker
 */
router.get("/trend/analyze/:ticker", trendController.analyzeTrend);

/**
 * GET /api/trend/results/:ticker
 * Get trend analysis results for a ticker
 */
router.get("/trend/results/:ticker", trendController.getTrendResults);

/**
 * GET /api/trend/latest/:ticker
 * Get latest trend analysis for a ticker
 */
router.get("/trend/latest/:ticker", trendController.getLatestTrend);

/**
 * POST /api/trend/compare
 * Compare trends for multiple tickers
 */
router.post("/trend/compare", trendController.compareTrends);

/**
 * GET /api/trend/all
 * Get all recent trend analysis results
 */
router.get("/trend/all", trendController.getAllTrends);

module.exports = router;
