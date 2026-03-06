/**
 * Portfolio Optimization Controller
 * Handles portfolio optimization and analysis
 */

const mongoService = require("../services/mongo.service");
const apiService = require("../services/api.service");

/**
 * POST /api/portfolio/optimize
 * Optimize portfolio weights
 */
exports.optimizePortfolio = async (req, res) => {
    try {
        const { tickers, risk_aversion, fraud_penalty, start_date, end_date } = req.body;

        if (!tickers || !Array.isArray(tickers) || tickers.length < 2) {
            return res.status(400).json({
                error: "At least 2 tickers are required for portfolio optimization"
            });
        }

        // Call Python API for portfolio optimization
        const portfolioResult = await apiService.optimizePortfolio(
            tickers,
            risk_aversion,
            fraud_penalty,
            start_date,
            end_date
        );

        // Save to MongoDB
        const savedResult = await mongoService.savePortfolioResult(portfolioResult);

        res.json({
            ...portfolioResult,
            _id: savedResult._id,
            saved: true
        });
    } catch (error) {
        console.error("Error in optimizePortfolio:", error.message);
        res.status(error.response?.status || 400).json({
            error: "Portfolio optimization failed",
            message: error.message
        });
    }
};

/**
 * GET /api/portfolio/results
 * Get portfolio optimization results
 */
exports.getPortfolioResults = async (req, res) => {
    try {
        const { limit = 10 } = req.query;

        const results = await mongoService.getPortfolioResults(parseInt(limit));

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No portfolio optimization results found"
            });
        }

        res.json({
            count: results.length,
            results: results,
            status: "success"
        });
    } catch (error) {
        console.error("Error in getPortfolioResults:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/portfolio/latest
 * Get latest portfolio optimization result
 */
exports.getLatestPortfolioResult = async (req, res) => {
    try {
        const results = await mongoService.getPortfolioResults(1);

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No portfolio optimization results found"
            });
        }

        res.json({
            result: results[0],
            status: "success"
        });
    } catch (error) {
        console.error("Error in getLatestPortfolioResult:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * POST /api/portfolio/compare
 * Compare multiple portfolio configurations
 */
exports.comparePortfolios = async (req, res) => {
    try {
        const { portfolios } = req.body;

        if (!portfolios || !Array.isArray(portfolios) || portfolios.length < 2) {
            return res.status(400).json({
                error: "At least 2 portfolio configurations are required"
            });
        }

        const results = [];
        for (const portfolio of portfolios) {
            try {
                const result = await apiService.optimizePortfolio(
                    portfolio.tickers,
                    portfolio.risk_aversion || 0.6,
                    portfolio.fraud_penalty || 0.8,
                    portfolio.start_date,
                    portfolio.end_date
                );
                results.push({
                    config: portfolio,
                    result: result
                });
            } catch (error) {
                console.warn(`Error optimizing portfolio with tickers ${portfolio.tickers}:`, error.message);
            }
        }

        if (results.length === 0) {
            return res.status(400).json({
                error: "Failed to optimize any portfolio"
            });
        }

        res.json({
            count: results.length,
            comparisons: results,
            status: "success"
        });
    } catch (error) {
        console.error("Error in comparePortfolios:", error.message);
        res.status(400).json({
            error: "Portfolio comparison failed",
            message: error.message
        });
    }
};
