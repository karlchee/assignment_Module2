{% snapshot customers_snapshot %}
{{
  config(
    target_schema='olist_snapshots',
    unique_key='customer_id',
    strategy='check',
    check_cols=['customer_unique_id', 'customer_zip_code_prefix', 'customer_city', 'customer_state'],
    invalidate_hard_deletes=True
  )
}}
SELECT
  customer_id,
  customer_unique_id,
  customer_zip_code_prefix,
  customer_city,
  customer_state
FROM {{ source('olist_staging', 'customers') }}
{% endsnapshot %}