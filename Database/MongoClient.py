from pymongo import MongoClient
import datetime
import config

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]
collection = db["portfolio_results"]

def save_results(results):

    document = {
        "timestamp": datetime.datetime.utcnow(),
        "results": results
    }

    collection.insert_one(document)

    print("Saved to MongoDB successfully.")