# Automated End-to-End Market Intelligence & Dynamic Pricing ETL Pipeline

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Apache Parquet](https://img.shields.io/badge/Apache_Parquet-Snappy_Encoded-50ABF1?style=for-the-badge&logo=apache&logoColor=white)](https://parquet.apache.org)
[![SQLite](https://img.shields.io/badge/SQLite-Data_Warehouse-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Power BI](https://img.shields.io/badge/Power_BI-Serving_Ready-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com)

An enterprise-grade, automated Data Engineering and Business Intelligence pipeline simulating multi-channel market rate ingestion, data cleaning, format serialization benchmarking, Star Schema dimensional modeling, and competitive revenue intelligence analytics.

Designed for hospitality and travel **Revenue Management Systems (RMS)**, dynamic rate shopping, and distribution channel parity monitoring (e.g., ZettaRMS, OTA aggregators).

---

## 🚀 Key Highlights & Quantified Performance Benchmarks

* **81.8% Storage Footprint Reduction:** Cut raw data storage from **474.8 KB (CSV)** and **1,514.1 KB (JSON)** down to **86.4 KB (Apache Parquet)** using Snappy columnar compression.
* **2.1x Read Latency Acceleration:** Reduced multi-iteration query read latency from **9.8 ms (CSV)** down to **4.8 ms (Parquet)** for downstream analytical workloads.
* **90.5% High-Quality Data Retention:** Cleansed 4,320 noisy web-scraped records—removing 120 duplicate entries and filtering 292 malformed records (currency symbols, negative values, sold-out statuses) while imputing missing occupancy with property-level medians.
* **Automated Star Schema Modeling:** Modeled into 4 dimension tables (`dim_property`, `dim_channel`, `dim_room_type`, `dim_date`) and a central fact table (`fact_market_rates`) with strict foreign keys and indexed query paths.
* **Live REST API Ingestion:** Programmatically extracts real-time foreign exchange rates (EUR, GBP, INR) to enable dynamic multi-currency rate normalization.

### 📊 Storage Format & Latency Comparison Table

| Storage Format | Paradigm | File Size | Storage Savings vs CSV | Avg Read Latency | Read Speedup |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **JSON** | Hierarchical / Text | 1,514.12 KB | *+218.9% (Overhead)* | 19.74 ms | 0.5x |
| **CSV** | Row-based / Text | 474.80 KB | *Baseline* | 9.80 ms | 1.0x (Baseline) |
| **Apache Parquet** | Columnar / Binary (Snappy) | **86.37 KB** | **-81.8%** | **4.85 ms** | **2.02x Faster** |

---

## 💡 Revenue Management Analytics & Key Insights

The pipeline executes pre-compiled SQL queries directly on the Star Schema, extracting critical business intelligence:

### 1. Property Performance: Average Daily Rate (ADR) & RevPAR
Evaluates commercial health and revenue generation per available room across luxury properties:
```sql
SELECT 
    p.property_name,
    p.star_rating,
    COUNT(f.fact_id) AS total_observations,
    ROUND(AVG(f.observed_rate), 2) AS adr_inr,
    ROUND(AVG(f.estimated_occupancy), 1) AS avg_occupancy_pct,
    ROUND(AVG(f.revpar_proxy), 2) AS revpar_inr
FROM fact_market_rates f
JOIN dim_property p ON f.property_id = p.property_id
GROUP BY p.property_id, p.property_name, p.star_rating
ORDER BY revpar_inr DESC;
```
* **Sample Insight:** *The Taj Mahal Palace* achieved the highest RevPAR (₹45,641) with an ADR of ₹54,540 at 83.2% occupancy, outperforming the compset by 18.2%.

### 2. Rate Parity Leakage Across Online Travel Agencies (OTAs)
Monitors third-party distributor compliance by detecting unauthorized undercutting against the direct website:
```sql
SELECT 
    c.channel_name,
    COUNT(f.fact_id) AS total_scrapes,
    SUM(f.is_parity_violation) AS parity_violations,
    ROUND(SUM(f.is_parity_violation) * 100.0 / COUNT(f.fact_id), 2) AS violation_rate_pct,
    ROUND(AVG(f.price_index), 2) AS avg_price_index
FROM fact_market_rates f
JOIN dim_channel c ON f.channel_id = c.channel_id
WHERE c.channel_name != 'Direct Website'
GROUP BY c.channel_id, c.channel_name
ORDER BY violation_rate_pct DESC;
```
* **Sample Insight:** OTAs like Agoda and Booking.com exhibited an undercut rate of ~34.8%, highlighting significant rate parity leakage requiring automated dynamic contract enforcement.

---

## ⚙️ Quickstart & Execution

### Prerequisites
* Python 3.10+
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/kartikpatade/market-intelligence-etl-pipeline.git
cd market-intelligence-etl-pipeline
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Entire Pipeline End-to-End
Execute all 5 stages (benchmarking, cleaning, star-schema loading, API ingestion, and SQL analytics) with a single command:
```bash
python scripts/05_run_pipeline.py
```

### 4. Interactive Power BI Dashboard
Open Power BI Desktop, click **Get Data → Text/CSV**, and select `data/processed/powerbi_serving_dataset.csv` to explore pre-calculated revenue metrics, channel slicers, and occupancy trends.

---

## 🎯 Technical Interview Talking Points

1. **Why Columnar Parquet over CSV/JSON:** In high-frequency rate-shopping scenarios with millions of observations, storing records in Snappy-compressed Parquet reduces storage by >80% and allows column-pruned analytical queries to execute without scanning unneeded attributes.
2. **Kimball Star Schema in Revenue Systems:** Separating properties, distribution channels, and dates into normalized dimension tables prevents data redundancy, eliminates update anomalies, and optimizes aggregate analytical performance.
3. **Idempotent Data Engineering:** All pipeline stages are idempotent; tables are automatically refreshed without data corruption upon consecutive executions.
