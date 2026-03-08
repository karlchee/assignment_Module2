{{ config(materialized='table') }}

SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    o.customer_id,
    DATE(TIMESTAMP(o.order_purchase_timestamp)) AS order_purchase_date,
    CAST(oi.price AS FLOAT64) AS price,
    CAST(oi.freight_value AS FLOAT64) AS freight_value,
    CAST(oi.price AS FLOAT64) * CAST(oi.freight_value AS FLOAT64) AS payment_value
FROM {{ source('olist_staging', 'order_items') }} oi
LEFT JOIN {{ source('olist_staging', 'orders') }} o
ON oi.order_id = o.order_id


    
