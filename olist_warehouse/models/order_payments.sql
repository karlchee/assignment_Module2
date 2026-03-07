{{ config(materialized='table') }}

SELECT
    op.order_id,
    op.payment_sequential,
    op.payment_type,
    op.payment_installments,
    op.payment_value
FROM {{ source('olist_staging', 'order_payments') }} op
