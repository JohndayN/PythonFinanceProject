# Finance Backend API Documentation

## Overview

The Finance Backend is a Node.js/Express server that provides a comprehensive REST API for financial data analysis, fraud detection, anomaly analysis, portfolio optimization, and market prediction. It serves as a proxy to the Python FastAPI backend and provides MongoDB integration for data persistence.

**Database**: MongoDB (ticker_db.mixed_ticker_data)
**Primary Server Port**: 3002
**Python API Port**: 8000

## Architecture

```
FrontEnd (Vue.js)
│
├─→ Node.js Backend (Port 3002) ──┐
│   ├─ Fraud Detection              │
│   ├─ Anomaly Detection            ├──→ Python FastAPI (Port 8000)
│   ├─ Portfolio Optimization       │
│   ├─ Market Prediction            │
│   ├─ Trend Analysis               │
│   └─ Risk Analysis                │
│
└─→ MongoDB (ticker_db)
    └─ mixed_ticker_data collection
```

## Quick Start

### Prerequisites
- Node.js 14+ and npm
- Python 3.8+ (for Python API)
- MongoDB Atlas account (already configured)

### Installation

1. **Install Dependencies**
```bash
cd BackEnd
npm install
```

2. **Environment Setup**
```bash
cp .env.example .env
# Edit .env with your configuration if needed
```

3. **Start the Server**
```bash
npm start      # Production
npm run dev    # Development with auto-reload
```

## API Endpoints

### Health & Status

```
GET  /health              - Server health check
GET  /api/health          - API health check with Python backend status
```

### Market Data

```
GET  /api/stock/:symbol              - Get stock data by symbol (limit=100)
GET  /api/stock/:symbol/range        - Get stock data within date range
GET  /api/tickers                    - Get all available tickers
GET  /api/market-data/:ticker        - Fetch market data from Python API
GET  /api/hose-market                - Get HOSE market data
GET  /api/data-stats                 - Get data statistics
```

### Fraud Detection

```
POST /api/fraud/csv                  - Upload CSV for fraud detection
POST /api/fraud/pdf                  - Upload PDF for fraud detection
POST /api/fraud/comprehensive        - Comprehensive fraud detection
GET  /api/fraud/risk/:ticker         - Get fraud risk score
GET  /api/fraud/results/:ticker      - Get fraud detection results
GET  /api/fraud/all                  - Get all fraud results (limit)
```

### Anomaly Detection

```
POST /api/anomaly/detect/:ticker     - Detect anomalies in market data
GET  /api/anomaly/hose-market        - Detect HOSE market anomalies
GET  /api/anomaly/results/:ticker    - Get anomaly results for ticker
GET  /api/anomaly/latest/:ticker     - Get latest anomaly detection
GET  /api/anomaly/all                - Get all anomaly results
```

### Portfolio Optimization

```
POST /api/portfolio/optimize         - Optimize portfolio weights
GET  /api/portfolio/results          - Get portfolio results
GET  /api/portfolio/latest           - Get latest portfolio result
POST /api/portfolio/compare          - Compare multiple portfolios
```

### Market Prediction

```
GET  /api/prediction/forecast/:ticker        - Get market prediction
GET  /api/prediction/results/:ticker         - Get prediction results
GET  /api/prediction/latest/:ticker          - Get latest prediction
GET  /api/prediction/compare?tickers=...     - Compare predictions
GET  /api/prediction/all                     - Get all predictions
```

### Trend Analysis

```
GET  /api/trend/analyze/:ticker      - Analyze ticker trend
GET  /api/trend/results/:ticker      - Get trend results
GET  /api/trend/latest/:ticker       - Get latest trend
POST /api/trend/compare              - Compare trends for multiple tickers
GET  /api/trend/all                  - Get all trend results
```

### Risk Analysis

```
GET  /api/risk/score/:ticker         - Get risk score for ticker
POST /api/risk/save                  - Save risk scores
GET  /api/risk/dashboard             - Get risk dashboard
GET  /api/risk/overall/:ticker       - Get overall risk assessment
```

### Database History

```
GET  /api/db/status                           - Database connection status
GET  /api/db/fraud-detection-history          - Fraud detection history
GET  /api/db/anomaly-detection-history        - Anomaly detection history
GET  /api/db/portfolio-optimization-history   - Portfolio optimization history
GET  /api/db/market-prediction-history        - Market prediction history
GET  /api/db/trend-analysis-history           - Trend analysis history
```

## Request Examples

### Fraud Detection (CSV)
```bash
curl -X POST http://localhost:3002/api/fraud/csv \
  -F "file=@data.csv"
```

### Fraud Detection (PDF)
```bash
curl -X POST http://localhost:3002/api/fraud/pdf \
  -F "file=@financial_statement.pdf"
```

### Portfolio Optimization
```bash
curl -X POST http://localhost:3002/api/portfolio/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["VCB", "VIC", "VNM"],
    "risk_aversion": 0.6,
    "fraud_penalty": 0.8,
    "start_date": "2020-01-01",
    "end_date": "2024-12-31"
  }'
```

### Get Stock Data
```bash
curl http://localhost:3002/api/stock/VCB?limit=50
```

### Get Stock Data in Range
```bash
curl "http://localhost:3002/api/stock/VCB/range?start=2024-01-01&end=2024-12-31"
```

### Trend Analysis
```bash
curl http://localhost:3002/api/trend/analyze/VCB
```

### Risk Dashboard
```bash
curl "http://localhost:3002/api/risk/dashboard?tickers=VCB,VIC,VNM"
```

## Database Schema

### Main Collection: mixed_ticker_data
Location: `ticker_db.mixed_ticker_data`

Fields:
- `symbol` (string) - Stock ticker symbol
- `time` (string/date) - Timestamp of the data point
- `open` (number) - Opening price
- `high` (number) - Highest price
- `low` (number) - Lowest price
- `close` (number) - Closing price
- `volume` (number) - Trading volume

**Indexes**:
- `{ symbol: 1, time: -1 }` - Primary index for symbol queries
- `{ symbol: 1 }` - For ticker queries
- `{ time: -1 }` - For time-based queries

### Analysis Results Collections

**fraud_detection_results**
- Document structure:
  ```json
  {
    "_id": ObjectId,
    "timestamp": Date,
    "fraud_risk": Number,
    "fraud_indicators": Object,
    "file_type": String,
    "ticker": String,
    "status": String
  }
  ```

**anomaly_detection_results**
- Document structure:
  ```json
  {
    "_id": ObjectId,
    "timestamp": Date,
    "ticker": String,
    "anomaly_score": Number,
    "anomalies": Array,
    "status": String
  }
  ```

**portfolio_optimization_results**
- Document structure:
  ```json
  {
    "_id": ObjectId,
    "timestamp": Date,
    "tickers": Array,
    "optimal_weights": Object,
    "expected_return": Number,
    "portfolio_risk": Number,
    "status": String
  }
  ```

**market_prediction_results**
- Document structure:
  ```json
  {
    "_id": ObjectId,
    "timestamp": Date,
    "ticker": String,
    "predictions": Array,
    "confidence": Number,
    "days_predicted": Number,
    "status": String
  }
  ```

**trend_analysis_results**
- Document structure:
  ```json
  {
    "_id": ObjectId,
    "timestamp": Date,
    "ticker": String,
    "trend_data": Object,
    "status": String
  }
  ```

**risk_scores**
- Document structure:
  ```json
  {
    "_id": ObjectId,
    "ticker": String,
    "date": Date,
    "scores": Object
  }
  ```

## Service Architecture

### MongoDB Service (`services/mongo.service.js`)
Handles all MongoDB operations:
- `connectDB()` - Establish database connection
- `getStockData(symbol, limit)` - Get stock data
- `getStockDataRange(symbol, start, end)` - Get data in date range
- `getAvailableTickers()` - Get all available tickers
- `saveFraudResult(result)` - Save fraud detection results
- `saveAnomalyResult(result)` - Save anomaly detection results
- `savePortfolioResult(result)` - Save portfolio optimization results
- `savePredictionResult(result)` - Save market prediction results
- `saveTrendResult(result)` - Save trend analysis results
- `saveRiskScores(ticker, scores)` - Save risk scores

### API Service (`services/api.service.js`)
Proxies requests to Python FastAPI backend:
- `getMarketData(ticker, start, end)` - Fetch market data
- `getHOSEMarketData()` - Fetch HOSE data
- `detectAnomalies(ticker, start, end)` - Detect anomalies
- `detectFraudCSV(buffer, filename)` - CSV fraud detection
- `detectFraudPDF(buffer, filename)` - PDF fraud detection
- `optimizePortfolio(...)` - Portfolio optimization
- `getMarketPrediction(ticker, days)` - Market prediction
- `healthCheck()` - Check Python API status

## Controllers

Each controller handles business logic for its domain:

- **market.controller.js** - Market data operations
- **fraud.controller.js** - Fraud detection operations
- **anomaly.controller.js** - Anomaly detection operations
- **portfolio.controller.js** - Portfolio optimization
- **prediction.controller.js** - Market predictions
- **trend.controller.js** - Trend analysis
- **risk.controller.js** - Risk scoring and assessment

## Error Handling

All endpoints return standardized error responses:

```json
{
  "error": "Description of the error",
  "message": "Additional details",
  "timestamp": "ISO timestamp",
  "status_code": 400
}
```

Common HTTP Status Codes:
- `200` - Success
- `400` - Bad request (invalid parameters)
- `404` - Not found (no data for ticker, etc.)
- `500` - Server error (database connection, etc.)
- `503` - Service unavailable (Python API not responding)

## Running the Backend

### Development Mode
```bash
npm run dev
```
- Auto-reloads on file changes (requires nodemon)
- Shows detailed logging

### Production Mode
```bash
npm start
```
- Runs the server without auto-reload
- Optimized for performance

### Docker (Optional)
```bash
docker build -t finance-backend .
docker run -p 3002:3002 -e PORT=3002 finance-backend
```

## Integration with Python API

The backend automatically proxies requests to the Python FastAPI backend at `http://localhost:8000`. Ensure the Python API is running before starting the Node backend.

### Starting Python API
```bash
cd PythonFinanceProject
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

## Database Connection

The backend uses the MongoDB connection string and database configuration from the Python config file (`../../config.py`):

```python
MONGO_URI = "mongodb+srv://..."
DB_NAME = "ticker_db"
COLLECTION_NAME = "mixed_ticker_data"
```

Connection is automatically established on server startup.

## Troubleshooting

### MongoDB Connection Error
```
MongoClient connection error: Unable to connect
```
**Solution**: 
- Verify MongoDB URI in config.py
- Check network connectivity to MongoDB Atlas
- Ensure IP whitelist is configured in MongoDB Atlas

### Python API Not Responding
```
Error: Python API is not responding
```
**Solution**:
- Verify Python API is running on port 8000
- Check Python API logs for errors
- Ensure PYTHON_API_URL environment variable is correct

### File Upload Size Error
```
Error: File is too large
```
**Solution**: Maximum file size is 50MB. Split larger files.

### Port Already in Use
```
Error: Port 3002 is already in use
```
**Solution**: 
- Use a different port: `PORT=3003 npm start`
- Kill the process using port 3002

## Performance Tips

1. **Use database indexes** - Already created on startup
2. **Limit result sets** - Use `limit` parameter in queries
3. **Cache frequent queries** - Consider implementing Redis
4. **Use connection pooling** - Already configured in MongoDB settings
5. **Monitor response times** - Check logs for slow operations

## Security Features

- CORS enabled for authorized origins
- File upload size limits (50MB)
- File type validation (CSV, PDF only)
- Input validation on all endpoints
- HTTP exception handling
- Graceful shutdown on signals

## Contributing

When adding new features:
1. Create new controller in `controllers/`
2. Create new routes file in `routes/`
3. Add service methods in `services/`
4. Register routes in `server.js`
5. Update this documentation

## License

MIT

## Support

For issues or questions:
1. Check the logs in the terminal
2. Review API responses for error details
3. Verify database connection status at `/api/db/status`
4. Check Python API health at `/api/health`
