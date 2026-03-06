/**
 * Portfolio Optimization Routes
 * Endpoints for portfolio optimization and analysis
 */

const express = require("express");
const router = express.Router();
const portfolioController = require("../controllers/portfolio.controller");

/**
 * POST /api/portfolio/optimize
 * Optimize portfolio weights based on risk and fraud scores
 */
router.post("/portfolio/optimize", portfolioController.optimizePortfolio);

/**
 * GET /api/portfolio/results
 * Get portfolio optimization results
 */
router.get("/portfolio/results", portfolioController.getPortfolioResults);

/**
 * GET /api/portfolio/latest
 * Get latest portfolio optimization result
 */
router.get("/portfolio/latest", portfolioController.getLatestPortfolioResult);

/**
 * POST /api/portfolio/compare
 * Compare multiple portfolio configurations
 */
router.post("/portfolio/compare", portfolioController.comparePortfolios);

module.exports = router;
