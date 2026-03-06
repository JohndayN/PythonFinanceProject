from datetime import datetime, timedelta

SEQ_LENGTH = 30
TRAIN_RATIO = 0.8
HIDDEN_DIM = 64
NUM_LAYERS = 2
LR = 0.001
EPOCHS = 150

start_date = "2020-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")

TICKERS = []

MONGO_URI = "" #Input your MongoDB URI here, e.g. "mongodb+srv://username:password@host:port/"
DB_NAME = "" #Input your MongoDB database name here
COLLECTION_NAME = ""  #Input your MongoDB collection name here