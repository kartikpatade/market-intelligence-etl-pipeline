"""
Public API Ingestion Engine
Demonstrates automated API extraction, handling REST endpoints,
graceful fallback handling, and storing semi-structured metadata into JSON & DB.
"""

import os
import json
import sqlite3
import datetime
import requests

def run_api_ingestion():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_json = os.path.join(base_dir, "data", "processed", "live_fx_rates.json")
    db_path = os.path.join(base_dir, "data", "processed", "market_intelligence.db")

    print("=================================================================")
    print("      PUBLIC API INGESTION: LIVE FX & MARKET RATES")
    print("=================================================================")

    # Free public FX API (No API key required)
    api_url = "https://api.frankfurter.dev/v1/latest?base=USD&symbols=INR,EUR,GBP"
    print(f"Requesting Live FX Rates from Endpoint: {api_url}")

    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        fx_data = response.json()
        print("API Response successfully received (HTTP 200 OK).")
    except Exception as e:
        print(f"Notice: Live network request failed ({e}). Falling back to cached benchmark payload.")
        fx_data = {
            "amount": 1.0,
            "base": "USD",
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "rates": {"EUR": 0.92, "GBP": 0.79, "INR": 86.50}
        }

    # Store raw JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(fx_data, f, indent=2)
    print(f"Saved raw API response to: {output_json}")

    # Persist into Database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_fx_rates (
            fx_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingestion_time DATETIME,
            base_currency VARCHAR(10),
            target_currency VARCHAR(10),
            exchange_rate REAL
        )
    """)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for currency, rate in fx_data.get("rates", {}).items():
        cursor.execute(
            "INSERT INTO market_fx_rates (ingestion_time, base_currency, target_currency, exchange_rate) VALUES (?, ?, ?, ?)",
            (now, fx_data.get("base", "USD"), currency, float(rate))
        )
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM market_fx_rates")
    total = cursor.fetchone()[0]
    print(f"API Ingestion complete. Total FX records in database: {total}\n")
    conn.close()

if __name__ == "__main__":
    run_api_ingestion()
