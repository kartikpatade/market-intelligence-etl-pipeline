-- ====================================================================
-- Market Intelligence & Revenue Analytics Query Suite
-- Key Performance Indicators: ADR, RevPAR, Rate Parity, Price Index
-- ====================================================================

-- 1. Portfolio Overview: Average Daily Rate (ADR) & Estimated RevPAR by Property
SELECT 
    p.property_name,
    p.star_rating,
    COUNT(f.fact_id) AS total_rate_observations,
    ROUND(AVG(f.observed_rate), 2) AS adr_inr,
    ROUND(AVG(f.estimated_occupancy), 1) AS avg_occupancy_pct,
    ROUND(AVG(f.revpar_proxy), 2) AS revpar_inr
FROM fact_market_rates f
JOIN dim_property p ON f.property_id = p.property_id
GROUP BY p.property_id, p.property_name, p.star_rating
ORDER BY revpar_inr DESC;

-- 2. Channel Rate Parity Leakage Analysis
-- Identifies third-party OTAs that frequently undercut the direct brand rate
SELECT 
    c.channel_name,
    c.channel_type,
    COUNT(f.fact_id) AS total_scrapes,
    SUM(f.is_parity_violation) AS parity_violations,
    ROUND(SUM(f.is_parity_violation) * 100.0 / COUNT(f.fact_id), 2) AS violation_rate_pct,
    ROUND(AVG(f.price_index), 2) AS avg_price_index
FROM fact_market_rates f
JOIN dim_channel c ON f.channel_id = c.channel_id
WHERE c.channel_name != 'Direct Website'
GROUP BY c.channel_id, c.channel_name, c.channel_type
ORDER BY violation_rate_pct DESC;

-- 3. Room Category Pricing & Volatility Analysis
SELECT 
    r.room_type_name,
    COUNT(f.fact_id) AS rate_counts,
    ROUND(MIN(f.observed_rate), 2) AS min_rate_inr,
    ROUND(AVG(f.observed_rate), 2) AS avg_rate_inr,
    ROUND(MAX(f.observed_rate), 2) AS max_rate_inr,
    ROUND(MAX(f.observed_rate) - MIN(f.observed_rate), 2) AS rate_spread_range
FROM fact_market_rates f
JOIN dim_room_type r ON f.room_type_id = r.room_type_id
GROUP BY r.room_type_id, r.room_type_name
ORDER BY avg_rate_inr ASC;

-- 4. Weekend vs. Weekday Dynamic Demand & Rate Premium
SELECT 
    CASE WHEN d.is_weekend = 1 THEN 'Weekend (Fri-Sun)' ELSE 'Weekday (Mon-Thu)' END AS day_category,
    ROUND(AVG(f.market_demand_index), 1) AS avg_demand_index,
    ROUND(AVG(f.estimated_occupancy), 1) AS avg_occupancy_pct,
    ROUND(AVG(f.observed_rate), 2) AS avg_daily_rate_inr,
    ROUND(AVG(f.revpar_proxy), 2) AS revpar_proxy_inr
FROM fact_market_rates f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.is_weekend;

-- 5. Top 5 Highest Surge Check-In Dates by Regional Demand
SELECT 
    d.full_date,
    d.day_name,
    AVG(f.market_demand_index) AS avg_demand,
    ROUND(AVG(f.observed_rate), 2) AS avg_rate_inr,
    ROUND(AVG(f.revpar_proxy), 2) AS avg_revpar_inr
FROM fact_market_rates f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.date_id, d.full_date, d.day_name
ORDER BY avg_demand DESC
LIMIT 5;
