/**
 * Trend Analysis Controller
 * Handles trend analysis and market analysis
 */

const mongoService = require("../services/mongo.service");
const apiService = require("../services/api.service");

/**
 * GET /api/trend/analyze/:ticker
 * Perform trend analysis on a ticker
 */
exports.analyzeTrend = async (req, res) => {
    try {
        const { ticker } = req.params;
        const { start_date, end_date } = req.query;

        // Fetch market data
        const marketData = await apiService.getMarketData(ticker, start_date, end_date);

        if (!marketData || !marketData.data) {
            return res.status(404).json({
                error: "No market data found for this ticker",
                ticker: ticker.toUpperCase()
            });
        }

        // Perform basic trend analysis
        const closes = marketData.data.close || [];
        const volumes = marketData.data.volume || [];
        const dates = marketData.data.dates || [];

        if (closes.length < 2) {
            return res.status(400).json({
                error: "Insufficient data for trend analysis"
            });
        }

        // Calculate trend metrics
        const trendResult = {
            ticker: ticker.toUpperCase(),
            period: { start: dates[0], end: dates[dates.length - 1] },
            dataPoints: closes.length,
            
            // Price metrics
            currentPrice: closes[closes.length - 1],
            openingPrice: closes[0],
            highestPrice: Math.max(...closes),
            lowestPrice: Math.min(...closes),
            priceChange: closes[closes.length - 1] - closes[0],
            priceChangePercent: ((closes[closes.length - 1] - closes[0]) / closes[0] * 100).toFixed(2),
            
            // Volume metrics
            totalVolume: volumes.reduce((a, b) => a + b, 0),
            averageVolume: (volumes.reduce((a, b) => a + b, 0) / volumes.length).toFixed(0),
            
            // Trend direction
            trend: closes[closes.length - 1] > closes[0] ? "UPTREND" : "DOWNTREND",
            
            // Volatility (simplified standard deviation)
            volatility: calculateVolatility(closes).toFixed(4),
            
            // Moving averages
            ma20: calculateMovingAverage(closes, 20),
            ma50: calculateMovingAverage(closes, 50),
            
            timestamp: new Date(),
            status: "success"
        };

        // Save to MongoDB
        const savedResult = await mongoService.saveTrendResult(trendResult);

        res.json({
            ...trendResult,
            _id: savedResult._id,
            saved: true
        });
    } catch (error) {
        console.error("Error in analyzeTrend:", error.message);
        res.status(error.response?.status || 400).json({
            error: "Trend analysis failed",
            message: error.message
        });
    }
};

/**
 * GET /api/trend/results/:ticker
 * Get trend analysis results for a ticker
 */
exports.getTrendResults = async (req, res) => {
    try {
        const { ticker } = req.params;
        const { limit = 10 } = req.query;

        const results = await mongoService.getTrendResults(ticker, parseInt(limit));

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No trend analysis results found for this ticker",
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
        console.error("Error in getTrendResults:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/trend/latest/:ticker
 * Get latest trend analysis for a ticker
 */
exports.getLatestTrend = async (req, res) => {
    try {
        const { ticker } = req.params;

        const results = await mongoService.getTrendResults(ticker, 1);

        if (!results || results.length === 0) {
            return res.status(404).json({
                error: "No trend analysis results found for this ticker",
                ticker: ticker.toUpperCase()
            });
        }

        res.json({
            ticker: ticker.toUpperCase(),
            result: results[0],
            status: "success"
        });
    } catch (error) {
        console.error("Error in getLatestTrend:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/trend/all
 * Get all recent trend analysis results
 */
exports.getAllTrends = async (req, res) => {
    try {
        const { limit = 50 } = req.query;
        const db = mongoService.getDB();
        const collection = db.collection("trend_analysis_results");

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
        console.error("Error in getAllTrends:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * POST /api/trend/compare
 * Compare trends for multiple tickers
 */
exports.compareTrends = async (req, res) => {
    try {
        const { tickers, start_date, end_date } = req.body;

        if (!tickers || !Array.isArray(tickers) || tickers.length === 0) {
            return res.status(400).json({
                error: "Tickers array is required"
            });
        }

        const comparisons = [];

        for (const ticker of tickers) {
            try {
                const marketData = await apiService.getMarketData(ticker, start_date, end_date);
                if (marketData && marketData.data) {
                    const closes = marketData.data.close || [];
                    const dates = marketData.data.dates || [];

                    comparisons.push({
                        ticker: ticker.toUpperCase(),
                        currentPrice: closes[closes.length - 1],
                        priceChange: closes[closes.length - 1] - closes[0],
                        priceChangePercent: ((closes[closes.length - 1] - closes[0]) / closes[0] * 100).toFixed(2),
                        trend: closes[closes.length - 1] > closes[0] ? "UPTREND" : "DOWNTREND",
                        volatility: calculateVolatility(closes).toFixed(4),
                        period: { start: dates[0], end: dates[dates.length - 1] }
                    });
                }
            } catch (error) {
                console.warn(`Error analyzing trend for ${ticker}:`, error.message);
            }
        }

        if (comparisons.length === 0) {
            return res.status(400).json({
                error: "Failed to analyze trends for any ticker"
            });
        }

        res.json({
            count: comparisons.length,
            comparisons: comparisons,
            status: "success"
        });
    } catch (error) {
        console.error("Error in compareTrends:", error.message);
        res.status(400).json({
            error: "Trend comparison failed",
            message: error.message
        });
    }
};

/**
 * Helper function: Calculate volatility (standard deviation)
 */
function calculateVolatility(prices) {
    if (prices.length < 2) return 0;
    
    const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
    const variance = prices.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / prices.length;
    return Math.sqrt(variance);
}

/**
 * Helper function: Calculate moving average
 */
function calculateMovingAverage(prices, period) {
    if (prices.length < period) return null;
    const slice = prices.slice(-period);
    return (slice.reduce((a, b) => a + b, 0) / period).toFixed(2);
}
