"""
Automated Data Cleansing & Feature Engineering Engine
Transforms dirty, multi-channel competitor rate scrapes into standardized,
analytics-ready datasets with Revenue Management System (RMS) metrics.
"""

import os
import re
import numpy as np
import pandas as pd

USD_TO_INR_FX_RATE = 86.50

def parse_raw_rate(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if not s or s.upper() in ["SOLD OUT", "NAN", "NULL", "NONE"]:
        return np.nan

    # Check for negative value glitches
    if s.startswith("-"):
        return np.nan

    # Check for USD rate
    is_usd = "$" in s
    # Clean out currency characters, commas, and letters
    cleaned_num = re.sub(r"[^\d.]", "", s)
    if not cleaned_num:
        return np.nan

    try:
        rate = float(cleaned_num)
        if is_usd:
            rate = rate * USD_TO_INR_FX_RATE
        return rate if rate > 0 else np.nan
    except ValueError:
        return np.nan

def standardize_channel(name):
    if pd.isna(name):
        return "Unknown"
    norm = str(name).strip().lower()
    if "booking" in norm:
        return "Booking.com"
    elif "expedia" in norm:
        return "Expedia"
    elif "agoda" in norm:
        return "Agoda"
    elif "direct" in norm:
        return "Direct Website"
    elif "hotels" in norm:
        return "Hotels.com"
    elif "trip" in norm:
        return "Trip.com"
    else:
        return norm.title()

def run_cleaning_pipeline():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_csv = os.path.join(base_dir, "data", "raw", "market_rates_raw.csv")
    cleaned_csv = os.path.join(base_dir, "data", "processed", "market_rates_cleaned.csv")
    cleaned_parquet = os.path.join(base_dir, "data", "processed", "market_rates_cleaned.parquet")

    print("=================================================================")
    print("      DATA CLEANING & TRANSFORMATION PIPELINE")
    print("=================================================================")
    df = pd.read_csv(raw_csv)
    initial_count = len(df)
    print(f"Initial Raw Record Count: {initial_count:,}")

    # 1. Deduplication
    df = df.drop_duplicates()
    dedup_count = initial_count - len(df)
    print(f"Duplicates Removed:       {dedup_count:,}")

    # 2. Text Normalization
    df["property_name"] = df["property_name"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip()
    df["room_type"] = df["room_type"].astype(str).str.strip()
    df["channel"] = df["channel"].apply(standardize_channel)

    # 3. Numeric Rate Parsing & Currency Normalization
    df["observed_rate_clean"] = df["observed_rate"].apply(parse_raw_rate)
    invalid_rates = df["observed_rate_clean"].isna().sum()
    print(f"Invalid / Sold-Out Records Filtered: {invalid_rates:,}")
    df = df.dropna(subset=["observed_rate_clean"])

    # 4. Standardize Check-In Dates
    df["check_in_date"] = pd.to_datetime(df["check_in_date"], format="mixed", dayfirst=True)
    df["check_in_date_str"] = df["check_in_date"].dt.strftime("%Y-%m-%d")

    # 5. Missing Value Imputation (Occupancy)
    # Impute missing occupancy using property median
    property_median_occ = df.groupby("property_name")["estimated_occupancy"].transform("median")
    df["estimated_occupancy"] = df["estimated_occupancy"].fillna(property_median_occ).round(1)

    # 6. Feature Engineering for Revenue Intelligence (RMS Metrics)
    # Rate Spread = Competitor Rate - Baseline Direct Rate
    df["rate_spread"] = (df["observed_rate_clean"] - df["baseline_rate"]).round(2)

    # Price Index: (Observed Rate / Baseline Rate) * 100
    df["price_index"] = ((df["observed_rate_clean"] / df["baseline_rate"]) * 100).round(2)

    # Rate Parity Violation Flag (1 if third-party OTA is cheaper than Direct)
    df["is_parity_violation"] = np.where(
        (df["channel"] != "Direct Website") & (df["observed_rate_clean"] < df["baseline_rate"] * 0.98),
        1, 0
    )

    # RevPAR Proxy = Rate * (Occupancy / 100)
    df["revpar_proxy"] = (df["observed_rate_clean"] * (df["estimated_occupancy"] / 100.0)).round(2)

    # Date temporal features
    df["day_name"] = df["check_in_date"].dt.day_name()
    df["is_weekend"] = df["check_in_date"].dt.weekday.apply(lambda w: 1 if w >= 5 else 0)
    df["month"] = df["check_in_date"].dt.month
    df["quarter"] = df["check_in_date"].dt.quarter
    df["year"] = df["check_in_date"].dt.year

    final_count = len(df)
    print(f"Cleaned Analytical Records: {final_count:,} ({final_count/initial_count*100:.1f}% data retention)")

    # Data Quality Validation Assertions
    assert df["observed_rate_clean"].min() > 0, "Validation Failure: Rates must be strictly positive"
    assert df["is_parity_violation"].isin([0, 1]).all(), "Validation Failure: Parity violation flag must be binary"
    assert df["estimated_occupancy"].between(0, 100).all(), "Validation Failure: Occupancy must be 0-100%"

    # Save to disk
    df.to_csv(cleaned_csv, index=False)
    df.to_parquet(cleaned_parquet, engine="pyarrow", compression="snappy")
    print(f"Exported Cleaned Dataset:")
    print(f"  -> CSV:     {cleaned_csv}")
    print(f"  -> Parquet: {cleaned_parquet}\n")

    return df

if __name__ == "__main__":
    run_cleaning_pipeline()
