/**
 * Express.js Backend Server
 * Proxies requests to Python FastAPI backend
 * Provides REST API for Vue.js frontend
 * Database: MongoDB (ticker_db.mixed_ticker_data)
 */

const express = require('express');
const cors = require('cors');
const axios = require('axios');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3002;
const PYTHON_API = process.env.PYTHON_API_URL || 'http://localhost:8000';

// ===================== MIDDLEWARE =====================

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// File upload configuration
const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 50 * 1024 * 1024 },
    fileFilter: (req, file, cb) => {
        const allowedMimes = ['text/csv', 'application/pdf'];
        if (allowedMimes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('Invalid file type'));
        }
    }
});

// ===================== DATABASE SETUP =====================

const mongoService = require('./services/mongo.service');

// Connect to MongoDB on startup
mongoService.connectDB().then(() => {
    console.log('Database connection established');
}).catch((error) => {
    console.error('Failed to connect to database:', error);
    process.exit(1);
});

// ===================== ROUTES IMPORT =====================

const marketRoutes = require('./routes/market.routes');
const fraudRoutes = require('./routes/fraud.routes');
const anomalyRoutes = require('./routes/anomaly.routes');
const portfolioRoutes = require('./routes/portfolio.routes');
const predictionRoutes = require('./routes/prediction.routes');
const trendRoutes = require('./routes/trend.routes');
const riskRoutes = require('./routes/risk.routes');

// ===================== HEALTH CHECK =====================

app.get('/health', async (req, res) => {
    try {
        const pythonHealth = await axios.get(`${PYTHON_API}/health`, { timeout: 5000 }).catch(() => ({ data: { status: 'unavailable' } }));
        res.json({
            status: 'healthy',
            backend: 'nodejs',
            database: 'mongodb',
            database_status: 'connected',
            python_api: pythonHealth.data
        });
    } catch (error) {
        res.status(503).json({
            status: 'unhealthy',
            error: error.message
        });
    }
});

app.get('/api/health', async (req, res) => {
    try {
        const pythonHealth = await axios.get(`${PYTHON_API}/api/health`, { timeout: 5000 }).catch(() => ({ data: { status: 'unavailable' } }));
        res.json({
            status: 'ok',
            message: 'Backend is running',
            python_api: pythonHealth.data,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(503).json({
            status: 'error',
            message: 'Python API is not responding'
        });
    }
});

// ===================== ROUTE REGISTRATION =====================

// API Routes with /api prefix
app.use('/api', marketRoutes);
app.use('/api', fraudRoutes);
app.use('/api', anomalyRoutes);
app.use('/api', portfolioRoutes);
app.use('/api', predictionRoutes);
app.use('/api', trendRoutes);
app.use('/api', riskRoutes);

// ===================== LEGACY ROUTES (Backward Compatibility) =====================

// Legacy fraud route
app.get('/fraud/risk/:ticker', async (req, res) => {
    try {
        const { ticker } = req.params;
        const db = mongoService.getDB();
        const data = await db.collection("fraud_detection_results")
            .find({ ticker: ticker.toUpperCase() })
            .sort({ timestamp: -1 })
            .limit(1)
            .toArray();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// ===================== ERROR HANDLING =====================

app.use((err, req, res, next) => {
    if (err instanceof multer.MulterError) {
        if (err.code === 'FILE_TOO_LARGE') {
            return res.status(400).json({
                error: 'File is too large. Maximum size is 50MB.'
            });
        }
    }

    if (err.message && err.message.includes('Invalid file type')) {
        return res.status(400).json({
            error: 'Invalid file type. Only CSV and PDF files are allowed.'
        });
    }

    console.error('Server error:', err);
    res.status(err.status || 500).json({
        error: err.message || 'Internal server error',
        timestamp: new Date().toISOString()
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        error: 'Route not found',
        path: req.path,
        method: req.method
    });
});

// ===================== GRACEFUL SHUTDOWN =====================

process.on('SIGINT', async () => {
    console.log('\nShutting down gracefully...');
    await mongoService.disconnectDB();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\nShutting down gracefully...');
    await mongoService.disconnectDB();
    process.exit(0);
});

// ===================== START SERVER =====================

app.listen(PORT, () => {
    console.log('\n╔════════════════════════════════════════════════════════╗');
    console.log('║         Finance Backend Server Started                 ║');
    console.log(`║      Port: ${PORT}                                          ║`);
    console.log(`║      Python API: ${PYTHON_API}                ║`);
    console.log('║      Database: MongoDB (ticker_db)                     ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');
    console.log(' Available Routes:');
    console.log('  Market Data: /api/stock, /api/tickers, /api/hose-market');
    console.log('  Fraud Detection: /api/fraud/csv, /api/fraud/pdf, /api/fraud/comprehensive');
    console.log('  Anomaly Detection: /api/anomaly/detect, /api/anomaly/hose-market');
    console.log('  Portfolio: /api/portfolio/optimize, /api/portfolio/compare');
    console.log('  Predictions: /api/prediction/forecast');
    console.log('  Trend Analysis: /api/trend/analyze, /api/trend/compare');
    console.log('  Risk Analysis: /api/risk/score, /api/risk/dashboard\n');
});

module.exports = app;
