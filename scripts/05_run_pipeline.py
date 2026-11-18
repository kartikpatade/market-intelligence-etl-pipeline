"""
Master Pipeline Orchestration Runner
Executes the full Market Intelligence & Rate Analytics ETL lifecycle end-to-end:
1. Serialization Benchmarking (CSV vs JSON vs Parquet)
2. Automated Data Cleaning & Revenue Feature Engineering
3. Star Schema Ingestion (Fact & Dimension Tables)
4. Live Public API Ingestion (FX & Market Indicators)
5. SQL Analytics & Power BI Serving Export
"""

import os
import sys
import time
import subprocess

def run_step(step_num, title, script_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, "scripts", script_name)
    
    print("\n" + "=" * 70)
    print(f"  [STAGE {step_num}] {title.upper()}")
    print("=" * 70)
    
    start_time = time.perf_counter()
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    elapsed = time.perf_counter() - start_time
    
    if result.returncode != 0:
        print(f"\n[ERROR] Stage {step_num} failed with exit code {result.returncode}!")
        sys.exit(result.returncode)
    
    print(f"\n[SUCCESS] Stage {step_num} completed in {elapsed:.2f} seconds.")

def main():
    pipeline_start = time.perf_counter()
    print("*" * 70)
    print("  STARTING AUTOMATED MARKET INTELLIGENCE ETL & ANALYTICS PIPELINE")
    print("*" * 70)

    stages = [
        (1, "Storage Format Benchmarking", "01_storage_benchmark.py"),
        (2, "Data Cleansing & RMS Transformation", "02_clean_and_transform.py"),
        (3, "Star Schema Ingestion & Dimensional Modeling", "03_batch_ingestion.py"),
        (4, "Public API Ingestion (Live FX Rates)", "04_api_ingestion.py"),
        (5, "SQL Analytics Execution & BI Serving Export", "execute_analytics.py")
    ]

    for num, title, script in stages:
        run_step(num, title, script)

    total_time = time.perf_counter() - pipeline_start
    print("\n" + "*" * 70)
    print(f"  PIPELINE COMPLETE - ALL 5 STAGES EXECUTED SUCCESSFULLY ({total_time:.2f}s)")
    print("*" * 70)
    print("Data Warehouse: market_intelligence.db is populated and verified.")
    print("Serving Layer:  powerbi_serving_dataset.csv is ready for Power BI / BI tools.")

if __name__ == "__main__":
    main()
