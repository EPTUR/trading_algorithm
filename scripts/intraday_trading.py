import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
from scripts.config import PROCESSED_DATA_FILE, OUTPUT_DIR  # Import OUTPUT_DIR from config

# Define parameters
volume_target = 5.0  # MW required
min_spread = 50  # Minimum Bid-Ask spread in EUR
time_window = "5min"  # 5-minute rolling window


def load_and_process_data():
    """Load and process trading data from the predefined file."""
    # Load the data
    df = pd.read_csv(PROCESSED_DATA_FILE)

    # Convert time columns to datetime
    datetime_columns = ['DeliveryStart', 'DeliveryEnd', 'ExecutionTime']
    for col in datetime_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Drop rows with invalid timestamps
    df = df.dropna(subset=datetime_columns)

    # Ensure ExecutionTime is timezone-aware if it's not already
    if df["ExecutionTime"].dt.tz is None:
        df["ExecutionTime"] = df["ExecutionTime"].dt.tz_localize("UTC", ambiguous="NaT", nonexistent="NaT")
    else:
        # If already timezone-aware but not UTC, convert to UTC
        df["ExecutionTime"] = df["ExecutionTime"].dt.tz_convert("UTC")

    return df


def find_opportunities_in_window(df, window_start, window_end, volume_target, min_spread):
    """Find trading opportunities within the specified time window."""
    # Filter data for current window
    window_data = df[(df['ExecutionTime'] >= window_start) & (df['ExecutionTime'] < window_end)]

    if len(window_data) < 2:
        return None  # Not enough data points in this window

    # Group by product and price, and sum volumes
    window_data_grouped = window_data.groupby(['Product Code', 'Price', 'DeliveryStart', 'DeliveryEnd']).agg({
        'Volume': 'sum',
        'ExecutionTime': 'first'  # Keep the first execution time for reference
    }).reset_index()

    # Find ask prices (for buying) - these are the lowest prices
    ask_candidates = window_data_grouped.sort_values(by="Price")

    # Find bid prices (for selling) - these are the highest prices
    bid_candidates = window_data_grouped.sort_values(by="Price", ascending=False)

    # Calculate best buys to reach target volume
    ask_trades = []
    remaining_volume = volume_target
    for _, row in ask_candidates.iterrows():
        if remaining_volume <= 0:
            break

        # Take either all available volume or just what we need
        trade_volume = min(row["Volume"], remaining_volume)

        ask_trades.append({
            "Product": row["Product Code"],
            "Time": row["ExecutionTime"],
            "Price": row["Price"],
            "Volume": trade_volume,
            "DeliveryStart": row["DeliveryStart"],
            "DeliveryEnd": row["DeliveryEnd"],
            "Available_Volume": row["Volume"]  # Store total available volume for reference
        })

        remaining_volume -= trade_volume

    # Check if we successfully filled the buy side
    if remaining_volume > 0.001:  # Allow for small floating point differences
        return None  # Couldn't meet volume target for buying

    # Reset for sell side
    remaining_volume = volume_target
    bid_trades = []

    # Calculate best sells to reach target volume
    for _, row in bid_candidates.iterrows():
        if remaining_volume <= 0:
            break

        trade_volume = min(row["Volume"], remaining_volume)

        bid_trades.append({
            "Product": row["Product Code"],
            "Time": row["ExecutionTime"],
            "Price": row["Price"],
            "Volume": trade_volume,
            "DeliveryStart": row["DeliveryStart"],
            "DeliveryEnd": row["DeliveryEnd"],
            "Available_Volume": row["Volume"]  # Store total available volume for reference
        })

        remaining_volume -= trade_volume

    # Check if we successfully filled the sell side
    if remaining_volume > 0.001:  # Allow for small floating point differences
        return None  # Couldn't meet volume target for selling

    # Calculate weighted average prices
    ask_weighted_price = sum(t["Price"] * t["Volume"] for t in ask_trades) / volume_target
    bid_weighted_price = sum(t["Price"] * t["Volume"] for t in bid_trades) / volume_target

    # Check if spread meets minimum requirement
    spread = bid_weighted_price - ask_weighted_price
    if spread >= min_spread:
        return {
            "window_start": window_start,
            "window_end": window_end,
            "ask_trades": ask_trades,
            "bid_trades": bid_trades,
            "ask_weighted_price": ask_weighted_price,
            "bid_weighted_price": bid_weighted_price,
            "spread": spread,
            "profit": spread * volume_target
        }

    return None


def find_all_trading_opportunities(df, time_window, volume_target, min_spread):
    """Find all trading opportunities across the entire dataset using rolling time windows."""
    # Sort by execution time
    df = df.sort_values(by="ExecutionTime")

    # Convert time_window to timedelta
    window_delta = pd.Timedelta(time_window)

    # Get unique 5-minute windows
    df["window_start"] = df["ExecutionTime"].dt.floor(time_window)
    window_starts = df["window_start"].unique()

    all_opportunities = []

    for start in window_starts:
        window_end = start + window_delta
        opportunity = find_opportunities_in_window(df, start, window_end, volume_target, min_spread)

        if opportunity:
            all_opportunities.append(opportunity)

    return all_opportunities


def format_output_dataframe(trades):
    """Format trades into a nice dataframe for display."""
    df = pd.DataFrame(trades)

    # Round values for display
    if 'Price' in df.columns:
        df['Price'] = df['Price'].round(2)
    if 'Volume' in df.columns:
        df['Volume'] = df['Volume'].round(2)

    # For partial fills, indicate what portion was used
    df['Usage'] = (df['Volume'] / df['Available_Volume'] * 100).round(1).astype(str) + '%'

    # Format columns for display
    display_columns = ["Product", "Time", "Price", "Volume", "Usage"]
    return df[display_columns]


def save_results(opportunities):
    """Save the results to JSON and CSV files in the outputs directory."""
    # Define output file paths
    json_path = os.path.join(OUTPUT_DIR, "trading_opportunities.json")
    csv_path = os.path.join(OUTPUT_DIR, "trading_opportunities.csv")

    # Save to JSON
    with open(json_path, "w") as json_file:
        json.dump(opportunities, json_file, indent=4, default=str)

    # Save to CSV
    # Flatten the data for CSV
    flattened_data = []
    for opp in opportunities:
        for trade_type in ["ask_trades", "bid_trades"]:
            for trade in opp[trade_type]:
                flattened_data.append({
                    "window_start": opp["window_start"],
                    "window_end": opp["window_end"],
                    "trade_type": trade_type.replace("_trades", ""),
                    "product": trade["Product"],
                    "time": trade["Time"],
                    "price": trade["Price"],
                    "volume": trade["Volume"],
                    "available_volume": trade["Available_Volume"],
                    "delivery_start": trade["DeliveryStart"],
                    "delivery_end": trade["DeliveryEnd"],
                    "ask_weighted_price": opp["ask_weighted_price"],
                    "bid_weighted_price": opp["bid_weighted_price"],
                    "spread": opp["spread"],
                    "profit": opp["profit"]
                })

    df = pd.DataFrame(flattened_data)
    df.to_csv(csv_path, index=False)


def main():
    """Main function to process data and find trading opportunities."""
    # Load and process data
    df = load_and_process_data()

    # Find all trading opportunities
    opportunities = find_all_trading_opportunities(df, time_window, volume_target, min_spread)

    # Check if there are opportunities and display them
    if opportunities:
        print(f"Found {len(opportunities)} trading opportunities:")

        # Print and format each opportunity
        for i, opp in enumerate(opportunities):
            print(f"\n--- Opportunity {i + 1} ---")
            print(f"Time Window: {opp['window_start']} to {opp['window_end']}")
            print(f"Weighted Ask Price: {opp['ask_weighted_price']:.2f} EUR/MWh")
            print(f"Weighted Bid Price: {opp['bid_weighted_price']:.2f} EUR/MWh")
            print(f"Spread: {opp['spread']:.2f} EUR/MWh")
            print(f"Total Profit: {opp['profit']:.2f} EUR")

            print("\nBuy Opportunities (ASK):")
            print(format_output_dataframe(opp['ask_trades']))

            print("\nSell Opportunities (BID):")
            print(format_output_dataframe(opp['bid_trades']))

        # Save results to JSON and CSV
        save_results(opportunities)
        print(f"\nResults saved to {OUTPUT_DIR}/trading_opportunities.json and {OUTPUT_DIR}/trading_opportunities.csv.")
    else:
        print("No trading opportunities found meeting the criteria.")


if __name__ == "__main__":
    main()