import pandas as pd
import os
from scripts.config import PROCESSED_DATA_FILE
from scripts.visualization import plot_trade_prices, plot_vwap
from scripts.intraday_trading import find_all_trading_opportunities

def main():
    print("🚀 Running Trading Analysis Pipeline...")

    # Step 1: Load Processed Data
    #if not os.path.exists(PROCESSED_DATA_FILE):
        #print(f"❌ Processed data file not found: {PROCESSED_DATA_FILE}")
        #return

    #df = pd.read_csv(PROCESSED_DATA_FILE)

    # Step 2: Generate Visualizations
    #plot_trade_prices()
    #plot_vwap()

    # Step 3: Define trading parameters
    time_window = '5min'  # Change to 2, 5, 10, etc.
    volume_target = 5.0  # Target volume in MW (adjust this)
    min_spread = 0.5  # Minimum bid-ask spread in EUR (adjust this)

    # Step 4: Run Trading Algorithm
    print("🔍 Running trading algorithm...")
    opportunities = find_all_trading_opportunities(df, time_window, volume_target, min_spread)

    #if opportunities is None or len(opportunities) == 0:
        #print("❌ No trading opportunities found!")
    #else:
        #print(f"✅ Found {len(opportunities)} trading opportunities!")

    print("✅ Analysis Completed!")


if __name__ == "__main__":
    main()
