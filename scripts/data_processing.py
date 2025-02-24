import pandas as pd
import os
from scripts.config import RAW_DATA_FILE, PROCESSED_DATA_FILE  # Ensure paths are configured correctly

def process_data():
    """Load, clean, and process electricity trading data from CSV file."""
    # Load raw CSV
    df = pd.read_csv(RAW_DATA_FILE)

    # Convert time columns to datetime
    df["DeliveryStart"] = pd.to_datetime(df["DeliveryStart"], errors='coerce')
    df["DeliveryEnd"] = pd.to_datetime(df["DeliveryEnd"], errors='coerce')
    df["ExecutionTime"] = pd.to_datetime(df["ExecutionTime"], errors='coerce')

    # Drop rows with invalid timestamps
    df = df.dropna(subset=["DeliveryStart", "DeliveryEnd", "ExecutionTime"])

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

    # Divide Volume by 2 or 4 for HH products(or QH products) or duration 30 minutes(or 15 min
    df.loc[(df["Product Code"].str.startswith("HH")) | (df["Duration"] == 30), "Volume"] /= 2
    #df.loc[(df["Product Code"].str.startswith("QH")) | (df["Duration"] == 15), "Volume"] /= 4

    # Save processed file
    df.to_csv(PROCESSED_DATA_FILE, index=False)
    print(f"✅ Processed data saved at {PROCESSED_DATA_FILE}")
    return df

if __name__ == "__main__":
    process_data()



