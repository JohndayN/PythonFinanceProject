/**
 * MongoDB Service - Handles all database operations
 * Database: ticker_db
 * Primary Collection: mixed_ticker_data
 */

const { MongoClient } = require("mongodb");
const dotenv = require("dotenv");

dotenv.config();

const MONGO_URI = process.env.MONGO_URI || "mongodb+srv://nguyengiap211004_db_user:lwLOPZcGUqymEKj8@doantotnghiep.ygcj75m.mongodb.net/";
const DB_NAME = "ticker_db";
const MAIN_COLLECTION = "mixed_ticker_data";
const FRAUD_COLLECTION = "fraud_detection_results";
const ANOMALY_COLLECTION = "anomaly_detection_results";
const PORTFOLIO_COLLECTION = "portfolio_optimization_results";
const PREDICTION_COLLECTION = "market_prediction_results";
const TREND_COLLECTION = "trend_analysis_results";
const RISK_COLLECTION = "risk_scores";

let mongoClient = null;
let db = null;

/**
 * Connect to MongoDB
 */
const connectDB = async () => {
    try {
        if (mongoClient && db) {
            console.log("MongoDB already connected");
            return db;
        }

        mongoClient = new MongoClient(MONGO_URI, {
            maxPoolSize: 10,
            minPoolSize: 5
        });

        await mongoClient.connect();
        db = mongoClient.db(DB_NAME);

        // Verify connection
        await db.admin().ping();
        console.log(`✓ Connected to MongoDB - Database: ${DB_NAME}`);

        // Create indexes
        await createIndexes();

        return db;
    } catch (error) {
        console.error("MongoDB connection error:", error.message);
        process.exit(1);
    }
};

/**
 * Get database instance
 */
const getDB = () => {
    if (!db) {
        throw new Error("Database not connected. Call connectDB() first.");
    }
    return db;
};

/**
 * Create database indexes for fast queries
 */
const createIndexes = async () => {
    try {
        const collections = await db.listCollections().toArray();
        const collectionNames = collections.map(c => c.name);

        // Main ticker data indexes
        if (collectionNames.includes(MAIN_COLLECTION)) {
            const mainCol = db.collection(MAIN_COLLECTION);
            await mainCol.createIndex({ symbol: 1, time: -1 });
            await mainCol.createIndex({ symbol: 1 });
            await mainCol.createIndex({ time: -1 });
            console.log("✓ Indexes created for mixed_ticker_data");
        }

        // Fraud detection indexes
        if (collectionNames.includes(FRAUD_COLLECTION)) {
            const fraudCol = db.collection(FRAUD_COLLECTION);
            await fraudCol.createIndex({ timestamp: -1 });
            await fraudCol.createIndex({ ticker: 1 });
        }

        // Anomaly detection indexes
        if (collectionNames.includes(ANOMALY_COLLECTION)) {
            const anomalyCol = db.collection(ANOMALY_COLLECTION);
            await anomalyCol.createIndex({ ticker: 1, timestamp: -1 });
            await anomalyCol.createIndex({ timestamp: -1 });
        }

        // Portfolio optimization indexes
        if (collectionNames.includes(PORTFOLIO_COLLECTION)) {
            const portfolioCol = db.collection(PORTFOLIO_COLLECTION);
            await portfolioCol.createIndex({ timestamp: -1 });
            await portfolioCol.createIndex({ tickers: 1 });
        }

        // Market prediction indexes
        if (collectionNames.includes(PREDICTION_COLLECTION)) {
            const predictionCol = db.collection(PREDICTION_COLLECTION);
            await predictionCol.createIndex({ ticker: 1, timestamp: -1 });
            await predictionCol.createIndex({ timestamp: -1 });
        }

        // Trend analysis indexes
        if (collectionNames.includes(TREND_COLLECTION)) {
            const trendCol = db.collection(TREND_COLLECTION);
            await trendCol.createIndex({ ticker: 1, timestamp: -1 });
        }

        // Risk scores indexes
        if (collectionNames.includes(RISK_COLLECTION)) {
            const riskCol = db.collection(RISK_COLLECTION);
            await riskCol.createIndex({ ticker: 1, date: -1 });
        }

    } catch (error) {
        console.error("Error creating indexes:", error.message);
    }
};

/**
 * Get stock data by symbol
 */
const getStockData = async (symbol, limit = 100) => {
    try {
        const collection = db.collection(MAIN_COLLECTION);
        return await collection
            .find({ symbol: symbol.toUpperCase() })
            .sort({ time: -1 })
            .limit(limit)
            .toArray();
    } catch (error) {
        console.error(`Error fetching stock data for ${symbol}:`, error.message);
        throw error;
    }
};

/**
 * Get stock data within date range
 */
const getStockDataRange = async (symbol, startDate, endDate) => {
    try {
        const collection = db.collection(MAIN_COLLECTION);
        return await collection
            .find({
                symbol: symbol.toUpperCase(),
                time: { $gte: startDate, $lte: endDate }
            })
            .sort({ time: 1 })
            .toArray();
    } catch (error) {
        console.error(`Error fetching stock data range for ${symbol}:`, error.message);
        throw error;
    }
};

/**
 * Get available tickers
 */
const getAvailableTickers = async () => {
    try {
        const collection = db.collection(MAIN_COLLECTION);
        const tickers = await collection.distinct("symbol");
        return tickers.sort();
    } catch (error) {
        console.error("Error fetching available tickers:", error.message);
        throw error;
    }
};

/**
 * Save fraud detection result
 */
const saveFraudResult = async (result) => {
    try {
        const collection = db.collection(FRAUD_COLLECTION);
        result.timestamp = new Date();
        const inserted = await collection.insertOne(result);
        return { _id: inserted.insertedId, ...result };
    } catch (error) {
        console.error("Error saving fraud result:", error.message);
        throw error;
    }
};

/**
 * Get fraud detection results by ticker
 */
const getFraudResults = async (ticker, limit = 10) => {
    try {
        const collection = db.collection(FRAUD_COLLECTION);
        return await collection
            .find({ ticker: ticker.toUpperCase() })
            .sort({ timestamp: -1 })
            .limit(limit)
            .toArray();
    } catch (error) {
        console.error(`Error fetching fraud results for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Save anomaly detection result
 */
const saveAnomalyResult = async (result) => {
    try {
        const collection = db.collection(ANOMALY_COLLECTION);
        result.timestamp = new Date();
        const inserted = await collection.insertOne(result);
        return { _id: inserted.insertedId, ...result };
    } catch (error) {
        console.error("Error saving anomaly result:", error.message);
        throw error;
    }
};

/**
 * Get anomaly detection results by ticker
 */
const getAnomalyResults = async (ticker, limit = 10) => {
    try {
        const collection = db.collection(ANOMALY_COLLECTION);
        return await collection
            .find({ ticker: ticker.toUpperCase() })
            .sort({ timestamp: -1 })
            .limit(limit)
            .toArray();
    } catch (error) {
        console.error(`Error fetching anomaly results for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Save portfolio optimization result
 */
const savePortfolioResult = async (result) => {
    try {
        const collection = db.collection(PORTFOLIO_COLLECTION);
        result.timestamp = new Date();
        const inserted = await collection.insertOne(result);
        return { _id: inserted.insertedId, ...result };
    } catch (error) {
        console.error("Error saving portfolio result:", error.message);
        throw error;
    }
};

/**
 * Get latest portfolio optimization results
 */
const getPortfolioResults = async (limit = 10) => {
    try {
        const collection = db.collection(PORTFOLIO_COLLECTION);
        return await collection
            .find({})
            .sort({ timestamp: -1 })
            .limit(limit)
            .toArray();
    } catch (error) {
        console.error("Error fetching portfolio results:", error.message);
        throw error;
    }
};

/**
 * Save market prediction result
 */
const savePredictionResult = async (result) => {
    try {
        const collection = db.collection(PREDICTION_COLLECTION);
        result.timestamp = new Date();
        const inserted = await collection.insertOne(result);
        return { _id: inserted.insertedId, ...result };
    } catch (error) {
        console.error("Error saving prediction result:", error.message);
        throw error;
    }
};

/**
 * Get market prediction results by ticker
 */
const getPredictionResults = async (ticker, limit = 5) => {
    try {
        const collection = db.collection(PREDICTION_COLLECTION);
        return await collection
            .find({ ticker: ticker.toUpperCase() })
            .sort({ timestamp: -1 })
            .limit(limit)
            .toArray();
    } catch (error) {
        console.error(`Error fetching prediction results for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Save trend analysis result
 */
const saveTrendResult = async (result) => {
    try {
        const collection = db.collection(TREND_COLLECTION);
        result.timestamp = new Date();
        const inserted = await collection.insertOne(result);
        return { _id: inserted.insertedId, ...result };
    } catch (error) {
        console.error("Error saving trend result:", error.message);
        throw error;
    }
};

/**
 * Get trend analysis results by ticker
 */
const getTrendResults = async (ticker, limit = 10) => {
    try {
        const collection = db.collection(TREND_COLLECTION);
        return await collection
            .find({ ticker: ticker.toUpperCase() })
            .sort({ timestamp: -1 })
            .limit(limit)
            .toArray();
    } catch (error) {
        console.error(`Error fetching trend results for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Save risk scores
 */
const saveRiskScores = async (ticker, scores) => {
    try {
        const collection = db.collection(RISK_COLLECTION);
        const result = {
            ticker: ticker.toUpperCase(),
            date: new Date(),
            scores: scores
        };
        const inserted = await collection.insertOne(result);
        return { _id: inserted.insertedId, ...result };
    } catch (error) {
        console.error(`Error saving risk scores for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Get latest risk scores for ticker
 */
const getRiskScores = async (ticker) => {
    try {
        const collection = db.collection(RISK_COLLECTION);
        return await collection
            .findOne({ ticker: ticker.toUpperCase() }, { sort: { date: -1 } });
    } catch (error) {
        console.error(`Error fetching risk scores for ${ticker}:`, error.message);
        throw error;
    }
};

/**
 * Disconnect from MongoDB
 */
const disconnectDB = async () => {
    try {
        if (mongoClient) {
            await mongoClient.close();
            db = null;
            mongoClient = null;
            console.log("✓ Disconnected from MongoDB");
        }
    } catch (error) {
        console.error("Error disconnecting from MongoDB:", error.message);
    }
};

module.exports = {
    connectDB,
    getDB,
    disconnectDB,
    getStockData,
    getStockDataRange,
    getAvailableTickers,
    saveFraudResult,
    getFraudResults,
    saveAnomalyResult,
    getAnomalyResults,
    savePortfolioResult,
    getPortfolioResults,
    savePredictionResult,
    getPredictionResults,
    saveTrendResult,
    getTrendResults,
    saveRiskScores,
    getRiskScores
};
