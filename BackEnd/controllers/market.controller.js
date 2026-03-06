/**
 * Market Data Controller
 * Handles stock market data operations
 */

const mongoService = require("../services/mongo.service");
const apiService = require("../services/api.service");

/**
 * GET /api/stock/:symbol
 * Get stock data by symbol
 */
exports.getStockData = async (req, res) => {
    try {
        const { symbol } = req.params;
        const { limit = 100 } = req.query;

        const data = await mongoService.getStockData(symbol, parseInt(limit));

        if (!data || data.length === 0) {
            return res.status(404).json({
                error: "No data found for this symbol",
                symbol: symbol.toUpperCase()
            });
        }

        res.json({
            symbol: symbol.toUpperCase(),
            count: data.length,
            data: data,
            status: "success"
        });
    } catch (error) {
        console.error("Error in getStockData:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/stock/:symbol/range
 * Get stock data within date range
 */
exports.getStockDataRange = async (req, res) => {
    try {
        const { symbol } = req.params;
        const { start, end } = req.query;

        if (!start || !end) {
            return res.status(400).json({
                error: "Start and end dates are required"
            });
        }

        const data = await mongoService.getStockDataRange(symbol, start, end);

        if (!data || data.length === 0) {
            return res.status(404).json({
                error: "No data found for this symbol in the specified range",
                symbol: symbol.toUpperCase(),
                range: { start, end }
            });
        }

        res.json({
            symbol: symbol.toUpperCase(),
            range: { start, end },
            count: data.length,
            data: data,
            status: "success"
        });
    } catch (error) {
        console.error("Error in getStockDataRange:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/tickers
 * Get all available tickers
 */
exports.getAvailableTickers = async (req, res) => {
    try {
        const tickers = await mongoService.getAvailableTickers();

        res.json({
            tickers: tickers,
            count: tickers.length,
            status: "success"
        });
    } catch (error) {
        console.error("Error in getAvailableTickers:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};

/**
 * GET /api/market-data/:ticker
 * Fetch market data from Python API and save to DB
 */
exports.fetchMarketData = async (req, res) => {
    try {
        const { ticker } = req.params;
        const { start_date, end_date } = req.query;

        const marketData = await apiService.getMarketData(ticker, start_date, end_date);

        res.json(marketData);
    } catch (error) {
        console.error("Error in fetchMarketData:", error.message);
        res.status(error.response?.status || 500).json({
            error: "Failed to fetch market data",
            message: error.message
        });
    }
};

/**
 * GET /api/hose-market
 * Fetch HOSE market data
 */
exports.getHOSEMarketData = async (req, res) => {
    try {
        const data = await apiService.getHOSEMarketData();

        res.json(data);
    } catch (error) {
        console.error("Error in getHOSEMarketData:", error.message);
        res.status(error.response?.status || 500).json({
            error: "Failed to fetch HOSE market data",
            message: error.message
        });
    }
};

/**
 * GET /api/data-stats
 * Get statistics about available data
 */
exports.getDataStats = async (req, res) => {
    try {
        const tickers = await mongoService.getAvailableTickers();

        const stats = {
            totalTickers: tickers.length,
            tickers: tickers,
            status: "success"
        };

        res.json(stats);
    } catch (error) {
        console.error("Error in getDataStats:", error.message);
        res.status(500).json({
            error: "Internal server error",
            message: error.message
        });
    }
};
