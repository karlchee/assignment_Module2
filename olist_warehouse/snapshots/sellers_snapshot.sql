{% snapshot sellers_snapshot %}
{{
  config(
    target_schema='olist_snapshots',
    unique_key='seller_id',
    strategy='check',
    check_cols=['seller_zip_code_prefix', 'seller_city', 'seller_state'],
    invalidate_hard_deletes=True
  )
}}
SELECT
  seller_id,
  seller_zip_code_prefix,
  seller_city,
  seller_state
FROM {{ source('olist_staging', 'sellers') }}
{% endsnapshot %}