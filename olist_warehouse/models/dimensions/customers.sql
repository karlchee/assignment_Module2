{{ config(materialized='table') }}

WITH avg_geolocation AS (
    SELECT
        geolocation_zip_code_prefix,
        AVG(geolocation_lat) AS avg_geolocation_lat,
        AVG(geolocation_lng) AS avg_geolocation_lng
    FROM {{ source('olist_staging', 'geolocation') }}
    GROUP BY geolocation_zip_code_prefix
)

SELECT
    c.dbt_scd_id,
    c.customer_id,
    c.customer_unique_id,
    c.customer_zip_code_prefix,
    c.customer_city,
    c.customer_state,
    ag.avg_geolocation_lat,
    ag.avg_geolocation_lng,
    c.dbt_valid_from,
    c.dbt_valid_to
FROM {{ source('olist_snapshots', 'customers_snapshot') }} c
LEFT JOIN avg_geolocation ag
    ON c.customer_zip_code_prefix = ag.geolocation_zip_code_prefix

