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
    s.seller_id,
    s.seller_zip_code_prefix,
    s.seller_city,
    s.seller_state,
    ag.avg_geolocation_lat,
    ag.avg_geolocation_lng
FROM {{ source('olist_staging', 'sellers') }} s
LEFT JOIN avg_geolocation ag
    ON s.seller_zip_code_prefix = ag.geolocation_zip_code_prefix
