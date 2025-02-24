from scripts.data_processing import process_data
from scripts.visualization import plot_trade_prices, plot_vwap
from scripts.intraday_trading import find_all_trading_opportunities

def main():
    print("🚀 Running Trading Analysis Pipeline...")

    # Step 1: Process Data
    df = process_data()  # Ensure that `process_data()` returns the DataFrame

    # Step 2: Generate Visualizations
    #plot_trade_prices()
    #plot_vwap()

    # Step 3: Define trading parameters
    time_window = '5min'  # 5 minutes for example
    volume_target = 5.0  # Target volume in MW (adjust this)
    min_spread = 0.5  # Minimum bid-ask spread in EUR (adjust this)

    # Step 4: Run Trading Algorithm
    find_all_trading_opportunities(df, time_window, volume_target, min_spread)

    print("✅ Analysis Completed!")

if __name__ == "__main__":
    main()
