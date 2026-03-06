/**
 * Risk Analysis Controller
 * Handles risk scoring and assessment
 */

const mongoService = require("../services/mongo.service");

/**
 * GET /api/risk/score/:ticker
 * Get risk score for a ticker
 */
exports.getRiskScore = async (req, res) => {
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
        console.error("Error in getRiskScore:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * POST /api/risk/save
 * Save risk scores for a ticker
 */
exports.saveRiskScores = async (req, res) => {
    try {
        const { ticker, scores } = req.body;

        if (!ticker || !scores) {
            return res.status(400).json({
                error: "Ticker and scores are required"
            });
        }

        const savedResult = await mongoService.saveRiskScores(ticker, scores);

        res.json({
            ...savedResult,
            status: "success"
        });
    } catch (error) {
        console.error("Error in saveRiskScores:", error.message);
        res.status(500).json({
            error: "Error saving risk scores",
            message: error.message
        });
    }
};

/**
 * GET /api/risk/dashboard
 * Get risk dashboard with all risk metrics
 */
exports.getRiskDashboard = async (req, res) => {
    try {
        const { tickers } = req.query;

        if (!tickers) {
            return res.status(400).json({
                error: "Tickers parameter is required"
            });
        }

        const tickerArray = Array.isArray(tickers) ? tickers : [tickers];
        const riskData = [];

        for (const ticker of tickerArray) {
            try {
                const riskScore = await mongoService.getRiskScores(ticker);
                const fraudResults = await mongoService.getFraudResults(ticker, 1);
                const anomalyResults = await mongoService.getAnomalyResults(ticker, 1);

                riskData.push({
                    ticker: ticker.toUpperCase(),
                    riskScore: riskScore ? riskScore.scores : null,
                    fraudRisk: fraudResults.length > 0 ? fraudResults[0] : null,
                    anomalyRisk: anomalyResults.length > 0 ? anomalyResults[0] : null
                });
            } catch (error) {
                console.warn(`Error fetching risk data for ${ticker}:`, error.message);
            }
        }

        res.json({
            count: riskData.length,
            riskData: riskData,
            status: "success"
        });
    } catch (error) {
        console.error("Error in getRiskDashboard:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/risk/overall/:ticker
 * Get overall risk assessment for a ticker
 */
exports.getOverallRiskAssessment = async (req, res) => {
    try {
        const { ticker } = req.params;

        const riskScore = await mongoService.getRiskScores(ticker);
        const fraudResults = await mongoService.getFraudResults(ticker, 1);
        const anomalyResults = await mongoService.getAnomalyResults(ticker, 1);

        const assessment = {
            ticker: ticker.toUpperCase(),
            overallRiskLevel: "MEDIUM",
            riskComponents: {
                riskScore: riskScore ? riskScore.scores : null,
                fraudRisk: fraudResults.length > 0 ? fraudResults[0].fraud_risk : null,
                anomalyRisk: anomalyResults.length > 0 ? anomalyResults[0].anomaly_score : null
            },
            recommendation: "Perform additional due diligence",
            status: "success"
        };

        // Calculate overall risk level
        if (assessment.riskComponents.riskScore && assessment.riskComponents.fraudRisk !== null) {
            const avgRisk = (assessment.riskComponents.riskScore + (assessment.riskComponents.fraudRisk || 0)) / 2;
            if (avgRisk < 0.33) {
                assessment.overallRiskLevel = "LOW";
                assessment.recommendation = "Investment opportunity with low risk";
            } else if (avgRisk < 0.67) {
                assessment.overallRiskLevel = "MEDIUM";
                assessment.recommendation = "Monitor closely before investing";
            } else {
                assessment.overallRiskLevel = "HIGH";
                assessment.recommendation = "High risk - proceed with caution";
            }
        }

        res.json(assessment);
    } catch (error) {
        console.error("Error in getOverallRiskAssessment:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};
