import os

# Define base directory dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# File paths (relative)
#RAW_DATA_FILE = os.path.join(BASE_DIR, "data", "Continuous_Trades-FR-20240101.csv")
PROCESSED_DATA_FILE = os.path.join(BASE_DIR, "data", "processed_trades.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
