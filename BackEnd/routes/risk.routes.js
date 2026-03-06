/**
 * Risk Analysis Routes
 * Endpoints for risk scoring and assessment
 */

const express = require("express");
const router = express.Router();
const riskController = require("../controllers/risk.controller");

/**
 * GET /api/risk/score/:ticker
 * Get risk score for a ticker
 */
router.get("/risk/score/:ticker", riskController.getRiskScore);

/**
 * POST /api/risk/save
 * Save risk scores for a ticker
 */
router.post("/risk/save", riskController.saveRiskScores);

/**
 * GET /api/risk/dashboard
 * Get risk dashboard with all metrics
 */
router.get("/risk/dashboard", riskController.getRiskDashboard);

/**
 * GET /api/risk/overall/:ticker
 * Get overall risk assessment for a ticker
 */
router.get("/risk/overall/:ticker", riskController.getOverallRiskAssessment);

module.exports = router;
