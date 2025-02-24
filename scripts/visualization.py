import pandas as pd
import plotly.express as px
import os
from scripts.config import PROCESSED_DATA_FILE, OUTPUT_DIR

def plot_trade_prices():
    df = pd.read_csv(PROCESSED_DATA_FILE)

    # Scatter plot of trade prices over time
    fig = px.scatter(
        df,
        x="ExecutionTime",
        y="Price",
        title="Trade Prices Over Time",
        labels={"ExecutionTime": "Execution Time", "Price": "Price (EUR)"},
        height=800, width=1000
    )

    output_path = os.path.join(OUTPUT_DIR, "trade_prices.html")
    fig.write_html(output_path)
    print(f"📊 Trade Prices plot saved: {output_path}")

def plot_vwap():
    df = pd.read_csv(PROCESSED_DATA_FILE)

    # Calculate VWAP
    df["VWAP"] = (df["Price"] * df["Volume"]).cumsum() / df["Volume"].cumsum()

    # Plot VWAP
    fig = px.line(
        df,
        x="ExecutionTime",
        y="VWAP",
        title="Volume Weighted Average Price (VWAP) Over Time",
        labels={"ExecutionTime": "Execution Time", "VWAP": "VWAP (EUR)"},
        height=800, width=1000
    )

    output_path = os.path.join(OUTPUT_DIR, "vwap.html")
    fig.write_html(output_path)
    print(f"📊 VWAP plot saved: {output_path}")

if __name__ == "__main__":
    plot_trade_prices()
    plot_vwap()

