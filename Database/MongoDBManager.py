"""
MongoDB Manager for persisting analysis results
Handles connection, validation, and data storage for all analysis types
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import datetime
import config
import json
from typing import Dict, Any, Optional

class MongoDBManager:
    def __init__(self, uri: str = None, db_name: str = None, timeout: int = 5000):
        """
        Initialize MongoDB connection
        
        Args:
            uri: MongoDB connection string
            db_name: Database name
            timeout: Connection timeout in milliseconds
        """
        self.uri = uri or config.MONGO_URI
        self.db_name = db_name or config.DB_NAME
        self.client = None
        self.db = None
        self.is_connected = False
        self.timeout = timeout
        
    def connect(self) -> bool:
        """
        Establish MongoDB connection with error handling
        Returns True if successful, False otherwise
        """
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=self.timeout,
                connectTimeoutMS=self.timeout,
                socketTimeoutMS=self.timeout
            )
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.is_connected = True
            print("Successfully connected to MongoDB")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"MongoDB connection failed: {str(e)}")
            self.is_connected = False
            return False
        except Exception as e:
            print(f"Unexpected error connecting to MongoDB: {str(e)}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.is_connected = False

    def save_fraud_detection_result(self, result: Dict[str, Any]) -> Optional[str]:
        """
        Save fraud detection analysis result
        
        Args:
            result: Dictionary with keys: fraud_risk, fraud_indicators, file_type, extracted_text (optional)
        
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.is_connected:
            print("Not connected to MongoDB. Skipping save.")
            return None
            
        try:
            collection = self.db["fraud_detection_results"]
            document = {
                "timestamp": datetime.datetime.utcnow(),
                "fraud_risk": float(result.get("fraud_risk", 0)),
                "fraud_indicators": result.get("fraud_indicators", {}),
                "file_type": result.get("file_type", "unknown"),
                "extracted_text": result.get("extracted_text", "")[:1000],  # Truncate to 1000 chars
                "status": "completed"
            }
            
            inserted = collection.insert_one(document)
            print(f"Fraud detection result saved: {inserted.inserted_id}")
            return str(inserted.inserted_id)
        except Exception as e:
            print(f"Error saving fraud detection result: {str(e)}")
            return None

    def save_anomaly_detection_result(self, ticker: str, result: Dict[str, Any]) -> Optional[str]:
        """
        Save anomaly detection analysis result
        
        Args:
            ticker: Stock ticker symbol
            result: Dictionary with keys: anomaly_score, anomalies, status
        
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.is_connected:
            print("Not connected to MongoDB. Skipping save.")
            return None
            
        try:
            collection = self.db["anomaly_detection_results"]
            document = {
                "timestamp": datetime.datetime.utcnow(),
                "ticker": ticker,
                "anomaly_score": float(result.get("anomaly_score", 0)),
                "anomalies": result.get("anomalies", []),
                "status": result.get("status", "completed")
            }
            
            inserted = collection.insert_one(document)
            print(f"Anomaly detection result saved: {inserted.inserted_id}")
            return str(inserted.inserted_id)
        except Exception as e:
            print(f"Error saving anomaly detection result: {str(e)}")
            return None

    def save_portfolio_optimization_result(self, tickers: list, result: Dict[str, Any]) -> Optional[str]:
        """
        Save portfolio optimization result
        
        Args:
            tickers: List of stock tickers
            result: Dictionary with keys: optimal_weights, expected_return, portfolio_risk, status
        
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.is_connected:
            print("Not connected to MongoDB. Skipping save.")
            return None
            
        try:
            collection = self.db["portfolio_optimization_results"]
            document = {
                "timestamp": datetime.datetime.utcnow(),
                "tickers": tickers,
                "optimal_weights": result.get("optimal_weights", {}),
                "expected_return": float(result.get("expected_return", 0)),
                "portfolio_risk": float(result.get("portfolio_risk", 0)),
                "status": result.get("status", "completed")
            }
            
            inserted = collection.insert_one(document)
            print(f"Portfolio optimization result saved: {inserted.inserted_id}")
            return str(inserted.inserted_id)
        except Exception as e:
            print(f"Error saving portfolio optimization result: {str(e)}")
            return None

    def save_market_prediction_result(self, ticker: str, days: int, result: Dict[str, Any]) -> Optional[str]:
        """
        Save market prediction result
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days predicted
            result: Dictionary with keys: predictions, confidence, status
        
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.is_connected:
            print("Not connected to MongoDB. Skipping save.")
            return None
            
        try:
            collection = self.db["market_prediction_results"]
            document = {
                "timestamp": datetime.datetime.utcnow(),
                "ticker": ticker,
                "days_predicted": days,
                "predictions": result.get("predictions", []),
                "confidence": float(result.get("confidence", 0)),
                "status": result.get("status", "pending")
            }
            
            inserted = collection.insert_one(document)
            print(f"Market prediction result saved: {inserted.inserted_id}")
            return str(inserted.inserted_id)
        except Exception as e:
            print(f"Error saving market prediction result: {str(e)}")
            return None

    def get_recent_results(self, collection_name: str, limit: int = 10) -> list:
        """
        Retrieve recent analysis results
        
        Args:
            collection_name: Name of the collection to query
            limit: Maximum number of results to return
        
        Returns:
            List of recent results (excluding _id)
        """
        if not self.is_connected:
            return []
            
        try:
            collection = self.db[collection_name]
            results = list(collection.find({}).sort("timestamp", -1).limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
            
            return results
        except Exception as e:
            print(f"Error retrieving results: {str(e)}")
            return []

    def create_indexes(self):
        """Create database indexes for faster queries"""
        if not self.is_connected:
            return
            
        try:
            # Fraud detection indexes
            self.db["fraud_detection_results"].create_index("timestamp")
            self.db["fraud_detection_results"].create_index("file_type")
            self.db["fraud_detection_results"].create_index("ticker")
            
            # Anomaly detection indexes
            self.db["anomaly_detection_results"].create_index("ticker")
            self.db["anomaly_detection_results"].create_index("timestamp")
            
            # Portfolio optimization indexes
            self.db["portfolio_optimization_results"].create_index("timestamp")
            self.db["portfolio_optimization_results"].create_index([("tickers", 1)])
            
            # Market prediction indexes
            self.db["market_prediction_results"].create_index("ticker")
            self.db["market_prediction_results"].create_index("timestamp")
            
            # Trend analysis indexes
            self.db["trend_analysis_results"].create_index("ticker")
            self.db["trend_analysis_results"].create_index("timestamp")
            
            # Risk scores indexes
            self.db["risk_scores"].create_index("ticker")
            self.db["risk_scores"].create_index("date")
            
            # Mixed ticker data indexes (ticker_db)
            try:
                ticker_db = self.client["ticker_db"]
                ticker_db["mixed_ticker_data"].create_index([("symbol", 1), ("time", -1)])
                ticker_db["mixed_ticker_data"].create_index("symbol")
                ticker_db["mixed_ticker_data"].create_index("time")
            except Exception as e:
                print(f"Note: Could not create indexes for ticker_db: {str(e)}")
            
            print("Database indexes created successfully")
        except Exception as e:
            print(f"Error creating indexes: {str(e)}")

    def get_stock_from_ticker_db(self, symbol: str, limit: int = 100) -> list:
        """
        Get stock data from ticker_db.mixed_ticker_data
        
        Args:
            symbol: Stock symbol (ticker)
            limit: Maximum number of records to return
            
        Returns:
            List of stock records
        """
        try:
            ticker_db = self.client["ticker_db"]
            collection = ticker_db["mixed_ticker_data"]
            
            results = list(collection
                .find({"symbol": symbol.upper()})
                .sort("time", -1)
                .limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
            
            return results
        except Exception as e:
            print(f"Error fetching stock data from ticker_db: {str(e)}")
            return []

    def get_stock_range_from_ticker_db(self, symbol: str, start_date: str, end_date: str) -> list:
        """
        Get stock data from ticker_db within date range
        
        Args:
            symbol: Stock symbol
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            List of stock records
        """
        try:
            ticker_db = self.client["ticker_db"]
            collection = ticker_db["mixed_ticker_data"]
            
            results = list(collection
                .find({
                    "symbol": symbol.upper(),
                    "time": {"$gte": start_date, "$lte": end_date}
                })
                .sort("time", 1))
            
            # Convert ObjectId to string
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
            
            return results
        except Exception as e:
            print(f"Error fetching stock data range from ticker_db: {str(e)}")
            return []

    def get_available_tickers_from_ticker_db(self) -> list:
        """
        Get all available tickers from ticker_db.mixed_ticker_data
        
        Returns:
            List of unique ticker symbols
        """
        try:
            ticker_db = self.client["ticker_db"]
            collection = ticker_db["mixed_ticker_data"]
            
            tickers = collection.distinct("symbol")
            return sorted(tickers)
        except Exception as e:
            print(f"Error fetching available tickers from ticker_db: {str(e)}")
            return []

    def save_trend_analysis_result(self, ticker: str, result: Dict[str, Any]) -> Optional[str]:
        """
        Save trend analysis result
        
        Args:
            ticker: Stock ticker symbol
            result: Dictionary with trend analysis data
        
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.is_connected:
            print("Not connected to MongoDB. Skipping save.")
            return None
            
        try:
            collection = self.db["trend_analysis_results"]
            document = {
                "timestamp": datetime.datetime.utcnow(),
                "ticker": ticker.upper(),
                "trend_data": result,
                "status": "completed"
            }
            
            inserted = collection.insert_one(document)
            print(f"Trend analysis result saved: {inserted.inserted_id}")
            return str(inserted.inserted_id)
        except Exception as e:
            print(f"Error saving trend analysis result: {str(e)}")
            return None

    def get_all_results(self, collection_name: str, limit: int = 50) -> list:
        """
        Get all results from a collection with limit
        
        Args:
            collection_name: Name of the collection
            limit: Maximum number of results
            
        Returns:
            List of documents
        """
        try:
            collection = self.db[collection_name]
            results = list(collection
                .find({})
                .sort("timestamp", -1)
                .limit(limit))
            
            # Convert ObjectId to string
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
            
            return results
        except Exception as e:
            print(f"Error fetching results from {collection_name}: {str(e)}")
            return []


# Global manager instance
db_manager = None

def get_db_manager() -> MongoDBManager:
    """Get or create global MongoDB manager instance"""
    global db_manager
    
    if db_manager is None:
        db_manager = MongoDBManager()
        db_manager.connect()
    
    return db_manager


def save_results(results: Dict[str, Any]) -> bool:
    """
    Legacy function for backward compatibility
    """
    try:
        manager = get_db_manager()
        manager.save_fraud_detection_result(results)
        return True
    except Exception as e:
        print(f"Error in save_results: {str(e)}")
        return False
