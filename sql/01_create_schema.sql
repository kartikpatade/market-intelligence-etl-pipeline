-- ====================================================================
-- Market Intelligence & Revenue Management Data Warehouse Schema
-- Dimensional Star Schema Architecture (SQLite & MySQL Compatible)
-- ====================================================================

-- Drop existing tables to allow idempotent schema recreation
DROP TABLE IF EXISTS fact_market_rates;
DROP TABLE IF EXISTS dim_property;
DROP TABLE IF EXISTS dim_channel;
DROP TABLE IF EXISTS dim_room_type;
DROP TABLE IF EXISTS dim_date;

-- Dimension 1: Hotel Property Dimension
CREATE TABLE dim_property (
    property_id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_name VARCHAR(150) NOT NULL UNIQUE,
    city VARCHAR(50) NOT NULL,
    star_rating INTEGER NOT NULL
);

-- Dimension 2: Distribution Channel Dimension (Direct, OTA, Wholesaler)
CREATE TABLE dim_channel (
    channel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name VARCHAR(50) NOT NULL UNIQUE,
    channel_type VARCHAR(30) NOT NULL
);

-- Dimension 3: Room Type & Category Dimension
CREATE TABLE dim_room_type (
    room_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_type_name VARCHAR(50) NOT NULL UNIQUE
);

-- Dimension 4: Date Dimension (Calendar & Demand Seasonality)
CREATE TABLE dim_date (
    date_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_date DATE NOT NULL UNIQUE,
    day_name VARCHAR(15) NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL
);

-- Central Fact Table: Market Rates & Revenue Metrics
CREATE TABLE fact_market_rates (
    fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    room_type_id INTEGER NOT NULL,
    date_id INTEGER NOT NULL,
    observed_rate DECIMAL(10, 2) NOT NULL,
    baseline_rate DECIMAL(10, 2) NOT NULL,
    rate_spread DECIMAL(10, 2) NOT NULL,
    price_index DECIMAL(6, 2) NOT NULL,
    estimated_occupancy DECIMAL(5, 2) NOT NULL,
    market_demand_index INTEGER NOT NULL,
    is_parity_violation INTEGER NOT NULL,
    revpar_proxy DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (property_id) REFERENCES dim_property (property_id),
    FOREIGN KEY (channel_id) REFERENCES dim_channel (channel_id),
    FOREIGN KEY (room_type_id) REFERENCES dim_room_type (room_type_id),
    FOREIGN KEY (date_id) REFERENCES dim_date (date_id)
);

-- Performance Optimization Indexes for Analytical Queries
CREATE INDEX idx_fact_property ON fact_market_rates (property_id);
CREATE INDEX idx_fact_channel ON fact_market_rates (channel_id);
CREATE INDEX idx_fact_date ON fact_market_rates (date_id);
CREATE INDEX idx_fact_parity ON fact_market_rates (is_parity_violation);
