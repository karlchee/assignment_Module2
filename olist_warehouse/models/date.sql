{{ config(materialized='table') }}

-- This model creates a date dimension table that can be used for time-based analysis in the data warehouse.
-- It contains dates from year 2015 to current date
WITH date_range AS (
    -- BigQuery-compatible generator: unnest a date array from start to today
    SELECT
        day AS full_date
    FROM UNNEST(GENERATE_DATE_ARRAY(DATE '2015-01-01', CURRENT_DATE())) AS day
)

SELECT
    full_date,
    EXTRACT(YEAR FROM full_date) AS year,
    EXTRACT(QUARTER FROM full_date) AS quarter,
    EXTRACT(MONTH FROM full_date) AS month,
    EXTRACT(DAY FROM full_date) AS day,
    EXTRACT(DAYOFWEEK FROM full_date) AS day_of_week,
    FORMAT_DATE('%B', full_date) AS month_name,
    FORMAT_DATE('%A', full_date) AS day_name,
    CASE WHEN EXTRACT(DAYOFWEEK FROM full_date) IN (1, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM date_range
WHERE full_date <= CURRENT_DATE() -- Ensure we only include dates up to the current date
