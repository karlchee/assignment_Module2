{{ config(materialized='table') }}

SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    cs.dbt_scd_id AS seller_scd_id,
    cc.dbt_scd_id AS customer_scd_id,
    DATE(TIMESTAMP(o.order_purchase_timestamp)) AS order_purchase_date,
    CAST(oi.price AS FLOAT64) AS price,
    CAST(oi.freight_value AS FLOAT64) AS freight_value,
    CAST(oi.price AS FLOAT64) + CAST(oi.freight_value AS FLOAT64) AS payment_value
FROM {{ source('olist_staging', 'order_items') }} oi
LEFT JOIN {{ source('olist_staging', 'orders') }} o
    ON oi.order_id = o.order_id
LEFT JOIN {{ source('olist_snapshots', 'customers_snapshot') }} cc
    ON o.customer_id = cc.customer_id
    AND TIMESTAMP(o.order_purchase_timestamp) >= cc.dbt_valid_from
    AND (TIMESTAMP(o.order_purchase_timestamp) < cc.dbt_valid_to OR cc.dbt_valid_to IS NULL)
LEFT JOIN {{ source('olist_snapshots', 'sellers_snapshot') }} cs
    ON oi.seller_id = cs.seller_id
    AND TIMESTAMP(o.order_purchase_timestamp) >= cs.dbt_valid_from
    AND (TIMESTAMP(o.order_purchase_timestamp) < cs.dbt_valid_to OR cs.dbt_valid_to IS NULL)


    
