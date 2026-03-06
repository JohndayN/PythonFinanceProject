/**
 * Market Data Routes
 * Endpoints for market data retrieval and analysis
 */

const express = require("express");
const router = express.Router();
const marketController = require("../controllers/market.controller");

/**
 * GET /api/stock/:symbol
 * Get stock data by symbol with optional limit
 */
router.get("/stock/:symbol", marketController.getStockData);

/**
 * GET /api/stock/:symbol/range
 * Get stock data within date range
 */
router.get("/stock/:symbol/range", marketController.getStockDataRange);

/**
 * GET /api/tickers
 * Get all available tickers
 */
router.get("/tickers", marketController.getAvailableTickers);

/**
 * GET /api/market-data/:ticker
 * Fetch fresh market data from Python API
 */
router.get("/market-data/:ticker", marketController.fetchMarketData);

/**
 * GET /api/hose-market
 * Get HOSE market data
 */
router.get("/hose-market", marketController.getHOSEMarketData);

/**
 * GET /api/data-stats
 * Get statistics about available data
 */
router.get("/data-stats", marketController.getDataStats);

module.exports = router;
