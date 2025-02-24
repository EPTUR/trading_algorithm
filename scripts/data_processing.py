import pandas as pd
import os
from scripts.config import RAW_DATA_FILE, PROCESSED_DATA_FILE  # Ensure paths are configured correctly

def load_and_process_data():
    """Load and process trading data from the predefined file."""
    # Load raw CSV
    df = pd.read_csv(RAW_DATA_FILE)

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

    # Extract Date from DeliveryStart
    df["Date"] = df["DeliveryStart"].dt.date

    # Compute Duration in minutes
    df["Duration"] = (df["DeliveryEnd"] - df["DeliveryStart"]).dt.total_seconds() / 60

    # Function to assign product codes
    def get_product_code(delivery_end, duration):
        """Assign Product Code based on DeliveryEnd time and Duration."""
        hour = f"{delivery_end.hour:02d}"  # Ensure two-digit hour format
        minute = delivery_end.minute

        if duration == 60:
            return f"PH-{hour}"  # Power-Hour

        elif duration == 30:
            num = f"{delivery_end.hour * 2 + (1 if minute == 30 else 0):02d}"
            return f"HH-{num}"  # Half-Hour

        elif duration == 15:
            num = f"{delivery_end.hour * 4 + minute // 15:02d}"
            return f"QH-{num}"  # Quarter-Hour

        else:
            return "Unknown"

    # Apply function to assign Product Code
    df["Product Code"] = df.apply(lambda row: get_product_code(row["DeliveryEnd"], row["Duration"]), axis=1)

    # Divide Volume by 2 or 4 for HH products (or QH products) or duration 30 minutes (or 15 min)
    df.loc[(df["Product Code"].str.startswith("HH")) | (df["Duration"] == 30), "Volume"] /= 2
    # df.loc[(df["Product Code"].str.startswith("QH")) | (df["Duration"] == 15), "Volume"] /= 4

    # Save processed file
    df.to_csv(PROCESSED_DATA_FILE, index=False)
    print(f"✅ Processed data saved at {PROCESSED_DATA_FILE}")
    df = df.drop_duplicates()

    return df


def process_data():
    """Processes data and prepares it for trading analysis."""
    df = load_and_process_data()
    return df


if __name__ == "__main__":
    process_data()
