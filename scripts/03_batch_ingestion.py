"""
Database Ingestion & Dimensional Modeling Engine
Loads cleaned market intelligence data into a normalized Star Schema
inside SQLite / MySQL with referential integrity and dimension indexing.
"""

import os
import sqlite3
import pandas as pd

def run_batch_ingestion():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cleaned_csv = os.path.join(base_dir, "data", "processed", "market_rates_cleaned.csv")
    db_path = os.path.join(base_dir, "data", "processed", "market_intelligence.db")
    schema_sql_path = os.path.join(base_dir, "sql", "01_create_schema.sql")

    print("=================================================================")
    print("      BATCH INGESTION & STAR SCHEMA MODELING")
    print("=================================================================")
    print(f"Target Database: {db_path}")

    df = pd.read_csv(cleaned_csv)
    print(f"Loaded Cleaned Records for Ingestion: {len(df):,}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Execute DDL Schema Script
    with open(schema_sql_path, "r", encoding="utf-8") as f:
        schema_ddl = f.read()
    cursor.executescript(schema_ddl)
    conn.commit()
    print("Star Schema (Fact & Dimension Tables) created successfully.")

    # 2. Populate dim_property
    property_lookup = {}
    properties = df[["property_name", "city", "star_rating"]].drop_duplicates()
    for _, row in properties.iterrows():
        cursor.execute(
            "INSERT INTO dim_property (property_name, city, star_rating) VALUES (?, ?, ?)",
            (row["property_name"], row["city"], int(row["star_rating"]))
        )
        property_lookup[row["property_name"]] = cursor.lastrowid
    print(f"Populated dim_property: {len(property_lookup)} records")

    # 3. Populate dim_channel
    channel_lookup = {}
    channels = df["channel"].drop_duplicates()
    for ch in channels:
        ch_type = "Direct" if "Direct" in ch else "OTA"
        cursor.execute(
            "INSERT INTO dim_channel (channel_name, channel_type) VALUES (?, ?)",
            (ch, ch_type)
        )
        channel_lookup[ch] = cursor.lastrowid
    print(f"Populated dim_channel: {len(channel_lookup)} records")

    # 4. Populate dim_room_type
    room_lookup = {}
    room_types = df["room_type"].drop_duplicates()
    for rm in room_types:
        cursor.execute(
            "INSERT INTO dim_room_type (room_type_name) VALUES (?)",
            (rm,)
        )
        room_lookup[rm] = cursor.lastrowid
    print(f"Populated dim_room_type: {len(room_lookup)} records")

    # 5. Populate dim_date
    date_lookup = {}
    dates = df[["check_in_date_str", "day_name", "month", "quarter", "year", "is_weekend"]].drop_duplicates()
    for _, row in dates.iterrows():
        cursor.execute(
            """INSERT INTO dim_date (full_date, day_name, month, quarter, year, is_weekend)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (row["check_in_date_str"], row["day_name"], int(row["month"]), 
             int(row["quarter"]), int(row["year"]), int(row["is_weekend"]))
        )
        date_lookup[row["check_in_date_str"]] = cursor.lastrowid
    print(f"Populated dim_date: {len(date_lookup)} records")

    conn.commit()

    # 6. Bulk Insert into fact_market_rates
    fact_records = []
    for _, row in df.iterrows():
        p_id = property_lookup[row["property_name"]]
        c_id = channel_lookup[row["channel"]]
        r_id = room_lookup[row["room_type"]]
        d_id = date_lookup[row["check_in_date_str"]]

        fact_records.append((
            p_id, c_id, r_id, d_id,
            float(row["observed_rate_clean"]),
            float(row["baseline_rate"]),
            float(row["rate_spread"]),
            float(row["price_index"]),
            float(row["estimated_occupancy"]),
            int(row["market_demand_index"]),
            int(row["is_parity_violation"]),
            float(row["revpar_proxy"])
        ))

    cursor.executemany(
        """INSERT INTO fact_market_rates 
           (property_id, channel_id, room_type_id, date_id, observed_rate, 
            baseline_rate, rate_spread, price_index, estimated_occupancy, 
            market_demand_index, is_parity_violation, revpar_proxy)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        fact_records
    )
    conn.commit()

    # Validation
    cursor.execute("SELECT COUNT(*) FROM fact_market_rates")
    total_loaded = cursor.fetchone()[0]
    print(f"Successfully loaded {total_loaded:,} fact records into fact_market_rates.")
    assert total_loaded == len(df), f"Mismatch: {total_loaded} loaded vs {len(df)} expected"

    conn.close()
    return total_loaded

if __name__ == "__main__":
    run_batch_ingestion()
