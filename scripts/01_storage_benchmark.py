"""
Storage Serialization & Format Benchmarking Engine
Evaluates storage efficiency, compression ratio, and read latency
across CSV (Row-text), JSON (Document/Nested), and Apache Parquet (Columnar/Binary).
"""

import os
import time
import json
import pandas as pd

def run_storage_benchmark():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_csv_path = os.path.join(base_dir, "data", "raw", "market_rates_raw.csv")
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    json_path = os.path.join(processed_dir, "market_rates_benchmark.json")
    parquet_path = os.path.join(processed_dir, "market_rates_benchmark.parquet")
    csv_copy_path = os.path.join(processed_dir, "market_rates_benchmark.csv")

    print("=================================================================")
    print("      DATA SERIALIZATION & STORAGE BENCHMARK ENGINE")
    print("=================================================================")
    print(f"Loading Source Data: {raw_csv_path}")
    df = pd.read_csv(raw_csv_path)
    print(f"Dataset Dimensions: {df.shape[0]:,} rows x {df.shape[1]} columns\n")

    # 1. Serialization
    df.to_csv(csv_copy_path, index=False)
    df.to_json(json_path, orient="records", indent=2)
    df.to_parquet(parquet_path, engine="pyarrow", compression="snappy")

    # 2. File Size Footprint
    csv_size = os.path.getsize(csv_copy_path)
    json_size = os.path.getsize(json_path)
    parquet_size = os.path.getsize(parquet_path)

    # 3. Read Latency Benchmarks (Multi-iteration average)
    iterations = 10
    
    # CSV Read Latency
    start = time.perf_counter()
    for _ in range(iterations):
        _ = pd.read_csv(csv_copy_path)
    csv_avg_time = (time.perf_counter() - start) / iterations

    # JSON Read Latency
    start = time.perf_counter()
    for _ in range(iterations):
        _ = pd.read_json(json_path)
    json_avg_time = (time.perf_counter() - start) / iterations

    # Parquet Read Latency
    start = time.perf_counter()
    for _ in range(iterations):
        _ = pd.read_parquet(parquet_path, engine="pyarrow")
    parquet_avg_time = (time.perf_counter() - start) / iterations

    # Calculate metrics
    parquet_storage_savings = ((csv_size - parquet_size) / csv_size) * 100
    parquet_speedup_vs_csv = csv_avg_time / parquet_avg_time

    results = {
        "formats": {
            "CSV": {
                "size_bytes": csv_size,
                "size_formatted": f"{csv_size / 1024:.2f} KB",
                "read_time_seconds": round(csv_avg_time, 5),
                "type": "Row-based / Text"
            },
            "JSON": {
                "size_bytes": json_size,
                "size_formatted": f"{json_size / 1024:.2f} KB",
                "read_time_seconds": round(json_avg_time, 5),
                "type": "Hierarchical / Text"
            },
            "Parquet": {
                "size_bytes": parquet_size,
                "size_formatted": f"{parquet_size / 1024:.2f} KB",
                "read_time_seconds": round(parquet_avg_time, 5),
                "type": "Columnar / Binary (Snappy)"
            }
        },
        "summary": {
            "storage_reduction_pct": round(parquet_storage_savings, 2),
            "read_speedup_vs_csv": round(parquet_speedup_vs_csv, 2)
        }
    }

    # Print Report
    print("--- BENCHMARK RESULTS ---")
    print(f"{'Format':<10} | {'File Size':<14} | {'Avg Read Latency':<18} | {'Format Paradigm'}")
    print("-" * 68)
    for fmt, data in results["formats"].items():
        print(f"{fmt:<10} | {data['size_formatted']:<14} | {data['read_time_seconds']*1000:>8.2f} ms         | {data['type']}")
    print("-" * 68)
    print(f"Key Takeaway: Apache Parquet achieved a {parquet_storage_savings:.1f}% storage reduction")
    print(f"             and a {parquet_speedup_vs_csv:.1f}x read acceleration compared to raw CSV.\n")

    summary_file = os.path.join(processed_dir, "benchmark_metrics.json")
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    run_storage_benchmark()
