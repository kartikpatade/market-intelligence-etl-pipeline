"""
SQL Analytics Runner & BI Data Serving Engine
Executes complex analytical queries on the Star Schema, formats output tables,
and exports the serving layer for Power BI dashboard consumption.
"""

import os
import sqlite3
import pandas as pd

def run_analytics_and_serving():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "processed", "market_intelligence.db")
    serving_csv = os.path.join(base_dir, "data", "processed", "powerbi_serving_dataset.csv")

    print("=================================================================")
    print("      REVENUE INTELLIGENCE & SQL ANALYTICS REPORT")
    print("=================================================================\n")

    conn = sqlite3.connect(db_path)

    # Query 1: Property ADR & RevPAR
    q1 = """
    SELECT 
        p.property_name AS "Property Name",
        p.star_rating AS "Stars",
        COUNT(f.fact_id) AS "Observations",
        ROUND(AVG(f.observed_rate), 2) AS "ADR (INR)",
        ROUND(AVG(f.estimated_occupancy), 1) AS "Avg Occupancy %",
        ROUND(AVG(f.revpar_proxy), 2) AS "RevPAR (INR)"
    FROM fact_market_rates f
    JOIN dim_property p ON f.property_id = p.property_id
    GROUP BY p.property_id, p.property_name, p.star_rating
    ORDER BY "RevPAR (INR)" DESC;
    """
    df1 = pd.read_sql_query(q1, conn)
    print(">>> 1. PROPERTY BENCHMARKS: AVERAGE DAILY RATE (ADR) & RevPAR")
    print(df1.to_string(index=False))
    print("\n" + "-"*75 + "\n")

    # Query 2: Rate Parity Violations
    q2 = """
    SELECT 
        c.channel_name AS "Channel",
        c.channel_type AS "Type",
        COUNT(f.fact_id) AS "Scrapes",
        SUM(f.is_parity_violation) AS "Parity Violations",
        ROUND(SUM(f.is_parity_violation) * 100.0 / COUNT(f.fact_id), 2) AS "Violation Rate %",
        ROUND(AVG(f.price_index), 2) AS "Avg Price Index"
    FROM fact_market_rates f
    JOIN dim_channel c ON f.channel_id = c.channel_id
    WHERE c.channel_name != 'Direct Website'
    GROUP BY c.channel_id, c.channel_name, c.channel_type
    ORDER BY "Violation Rate %" DESC;
    """
    df2 = pd.read_sql_query(q2, conn)
    print(">>> 2. DISTRIBUTION CHANNEL RATE PARITY LEAKAGE")
    print(df2.to_string(index=False))
    print("\n" + "-"*75 + "\n")

    # Query 3: Weekend vs. Weekday Surge Dynamics
    q3 = """
    SELECT 
        CASE WHEN d.is_weekend = 1 THEN 'Weekend (Fri-Sun)' ELSE 'Weekday (Mon-Thu)' END AS "Day Type",
        ROUND(AVG(f.market_demand_index), 1) AS "Demand Index",
        ROUND(AVG(f.estimated_occupancy), 1) AS "Occupancy %",
        ROUND(AVG(f.observed_rate), 2) AS "ADR (INR)",
        ROUND(AVG(f.revpar_proxy), 2) AS "RevPAR (INR)"
    FROM fact_market_rates f
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.is_weekend;
    """
    df3 = pd.read_sql_query(q3, conn)
    print(">>> 3. WEEKEND VS. WEEKDAY DYNAMIC PRICING SPREAD")
    print(df3.to_string(index=False))
    print("\n" + "-"*75 + "\n")

    # 4. Generate Denormalized Serving Layer for Power BI
    serving_query = """
    SELECT 
        f.fact_id,
        d.full_date AS check_in_date,
        d.day_name,
        d.is_weekend,
        d.month,
        d.quarter,
        p.property_name,
        p.city,
        p.star_rating,
        c.channel_name,
        c.channel_type,
        r.room_type_name,
        f.observed_rate,
        f.baseline_rate,
        f.rate_spread,
        f.price_index,
        f.estimated_occupancy,
        f.market_demand_index,
        f.is_parity_violation,
        f.revpar_proxy
    FROM fact_market_rates f
    JOIN dim_property p ON f.property_id = p.property_id
    JOIN dim_channel c ON f.channel_id = c.channel_id
    JOIN dim_room_type r ON f.room_type_id = r.room_type_id
    JOIN dim_date d ON f.date_id = d.date_id;
    """
    df_serving = pd.read_sql_query(serving_query, conn)
    df_serving.to_csv(serving_csv, index=False)
    print(f"Exported Power BI Serving Dataset: {serving_csv} ({len(df_serving):,} records)")

    conn.close()

if __name__ == "__main__":
    run_analytics_and_serving()
