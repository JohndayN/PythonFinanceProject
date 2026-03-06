from datetime import datetime, timedelta

SEQ_LENGTH = 30
TRAIN_RATIO = 0.8
HIDDEN_DIM = 64
NUM_LAYERS = 2
LR = 0.001
EPOCHS = 150

start_date = "2020-01-01"
end_date = datetime.today().strftime("%Y-%m-%d")

TICKERS = ["VCB", "VIC", "VNM", "HPG", "FPT", "MWG", "TCB"]

MONGO_URI = "mongodb+srv://nguyengiap211004_db_user:lwLOPZcGUqymEKj8@doantotnghiep.ygcj75m.mongodb.net/"
DB_NAME = "ticker_db"
COLLECTION_NAME = "mixed_ticker_data"
