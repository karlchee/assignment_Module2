# Olist Data Warehouse — Design Documentation

A reference document for the star schema data warehouse built with dbt on Google BigQuery, using the Brazilian E-Commerce Olist dataset.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Star Schema Diagram](#star-schema-diagram)
- [Dimension Tables](#dimension-tables)
- [Fact Tables](#fact-tables)
- [SCD Type 2 Snapshots](#scd-type-2-snapshots)
- [Data Quality Tests](#data-quality-tests)
- [Example Queries](#example-queries)

---

## Architecture Overview

```
Raw Data (BigQuery: olist_staging)
        │
        ▼
dbt Snapshots ──► olist_snapshots
  customers_snapshot  (SCD Type 2 — check strategy)
  sellers_snapshot    (SCD Type 2 — check strategy)
        │
        ▼
dbt Models ──► olist_data_warehouse
  Dimensions: customers, sellers, products, date
  Facts:       order_items, order_payments, order_reviews
```

- **Platform**: Google BigQuery (`academic-era-488315-j5`)
- **Transformation tool**: dbt Core (`olist_warehouse` project)
- **Packages**: `dbt_utils`, `dbt_expectations`, `dbt_date`
- **Materialization**: All dimension and fact models are materialized as **tables**

---

## Star Schema Diagram

```
              ┌──────────────────┐
              │  dim_customers   │  (SCD Type 2)
              └────────┬─────────┘
                       │ customer_scd_id
    ┌──────────────────┼───────────────────────────┐
    │                  │                           │
┌───▼───────────┐  ┌───▼──────────────┐  ┌────────▼─────────────┐
│  dim_sellers  │  │ fact_order_items │  │ fact_order_reviews   │
│ (SCD Type 2)  │  └───┬──────────────┘  └──────────────────────┘
└───────────────┘      │ product_id
  seller_scd_id ───────┘
                   ┌───▼──────────────┐
                   │   dim_products   │
                   └──────────────────┘

fact_order_payments ──(order_id)──► fact_order_items
dim_date ────────────(order_purchase_date)──► fact_order_items
```

---

## Dimension Tables

### `dim_customers` — SCD Type 2

Reads from the `customers_snapshot` and enriches each record with averaged lat/lng coordinates joined from the `geolocation` source table.

| Column | Type | Description |
|---|---|---|
| `dbt_scd_id` | STRING | **Surrogate key** — unique per customer version; used as FK in fact tables |
| `customer_id` | STRING | Natural key from the source system |
| `customer_unique_id` | STRING | System-level unique customer identifier |
| `customer_zip_code_prefix` | STRING | Customer postal code |
| `customer_city` | STRING | Customer city |
| `customer_state` | STRING | Customer state (UF) |
| `avg_geolocation_lat` | FLOAT | Average latitude for the customer's zip code prefix |
| `avg_geolocation_lng` | FLOAT | Average longitude for the customer's zip code prefix |
| `dbt_valid_from` | TIMESTAMP | Start of this row's validity period |
| `dbt_valid_to` | TIMESTAMP | End of this row's validity period (`NULL` = currently active record) |

**Usage notes**
- To get the current customer record: `WHERE dbt_valid_to IS NULL`
- To join from a fact table at the time of a transaction: join on `dbt_scd_id` (resolved at load time in `fact_order_items`)

---

### `dim_sellers` — SCD Type 2

Reads from the `sellers_snapshot` to track historical seller address changes.

| Column | Type | Description |
|---|---|---|
| `dbt_scd_id` | STRING | **Surrogate key** — unique per seller version; used as FK in fact tables |
| `seller_id` | STRING | Natural key from the source system |
| `seller_zip_code_prefix` | STRING | Seller postal code |
| `seller_city` | STRING | Seller city |
| `seller_state` | STRING | Seller state (UF) |
| `dbt_valid_from` | TIMESTAMP | Start of this row's validity period |
| `dbt_valid_to` | TIMESTAMP | End of this row's validity period (`NULL` = currently active record) |

**Usage notes**
- To get the current seller record: `WHERE dbt_valid_to IS NULL`
- Surrogate keys in `fact_order_items` capture the seller's location **at the time of the order**

---

### `dim_products` — SCD Type 1

Joins the products source table with the English category name translation. Overwrites on refresh (no history kept).

| Column | Type | Description |
|---|---|---|
| `product_id` | STRING | **Primary key** |
| `product_category_name` | STRING | Category name in Portuguese |
| `product_category_name_english` | STRING | Category name translated to English |
| `product_name_lenght` | INT | Character count of the product name |
| `product_description_lenght` | INT | Character count of the product description |
| `product_photos_qty` | INT | Number of product photos |
| `product_weight_g` | DECIMAL | Weight in grams |
| `product_length_cm` | DECIMAL | Length in centimetres |
| `product_height_cm` | DECIMAL | Height in centimetres |
| `product_width_cm` | DECIMAL | Width in centimetres |

---

### `dim_date`

Conformed date dimension referenced by fact tables for temporal analysis.

| Column | Type | Description |
|---|---|---|
| `date_key` | INT | YYYYMMDD integer surrogate key |
| `full_date` | DATE | Calendar date |
| `day_of_month` | INT | 1–31 |
| `day_of_week` | INT | 1–7 |
| `day_name` | STRING | e.g. `Monday` |
| `week_of_year` | INT | 1–53 |
| `month` | INT | 1–12 |
| `month_name` | STRING | e.g. `January` |
| `quarter` | INT | 1–4 |
| `year` | INT | e.g. `2018` |
| `is_weekend` | BOOLEAN | `TRUE` for Saturday/Sunday |
| `is_holiday` | BOOLEAN | `TRUE` for Brazilian public holidays |

---

## Fact Tables

### `fact_order_items`

**Grain**: one row per order line item.

This is the central fact table. At load time it resolves SCD Type 2 surrogate keys for both customer and seller by performing a **temporal join** against the snapshot tables on `order_purchase_timestamp`, so each row captures the exact customer/seller profile that existed when the order was placed.

| Column | Type | Description |
|---|---|---|
| `order_id` | STRING | Order identifier |
| `order_item_id` | INT | Line item sequence within the order |
| `product_id` | STRING | FK → `dim_products.product_id` |
| `seller_scd_id` | STRING | FK → `dim_sellers.dbt_scd_id` (seller's state **at order time**) |
| `customer_scd_id` | STRING | FK → `dim_customers.dbt_scd_id` (customer's state **at order time**) |
| `order_purchase_date` | DATE | Date the order was placed |
| `price` | FLOAT64 | Unit price of the item |
| `freight_value` | FLOAT64 | Freight cost for this item |
| `payment_value` | FLOAT64 | `price + freight_value` |

**Temporal join pattern used in the model**:
```sql
AND TIMESTAMP(o.order_purchase_timestamp) >= snapshot.dbt_valid_from
AND (TIMESTAMP(o.order_purchase_timestamp) < snapshot.dbt_valid_to
     OR snapshot.dbt_valid_to IS NULL)
```

---

### `fact_order_payments`

**Grain**: one row per payment method per order. A single order may have multiple rows if the customer used more than one payment method.

| Column | Type | Description |
|---|---|---|
| `order_id` | STRING | FK → orders |
| `payment_sequential` | INT | Sequence number when multiple methods are used (1, 2, 3…) |
| `payment_type` | STRING | `credit_card`, `boleto`, `voucher`, `debit_card` |
| `payment_installments` | INT | Number of instalments elected |
| `payment_value` | FLOAT | Amount paid via this method |

---

### `fact_order_reviews`

**Grain**: one row per review (each order receives at most one review).

| Column | Type | Description |
|---|---|---|
| `review_id` | STRING | Primary key |
| `order_id` | STRING | FK → orders |
| `review_score` | INT | Star rating (1–5) |
| `review_comment_title` | STRING | Review headline |
| `review_comment_message` | STRING | Full review text |
| `review_creation_date` | DATE | Date the review was submitted |
| `review_answer_timestamp` | TIMESTAMP | Timestamp of the seller's response |

---

## SCD Type 2 Snapshots

Both `customers` and `sellers` are implemented as Slowly Changing Dimensions using dbt's `snapshot` feature with the **check** strategy. When any tracked column changes in the source, dbt closes the existing row (sets `dbt_valid_to`) and inserts a new row.

| Snapshot | Unique Key | Change-Tracked Columns | Hard Delete Handling |
|---|---|---|---|
| `customers_snapshot` | `customer_id` | `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state` | Invalidated (`dbt_is_deleted = TRUE`) |
| `sellers_snapshot` | `seller_id` | `seller_zip_code_prefix`, `seller_city`, `seller_state` | Invalidated (`dbt_is_deleted = TRUE`) |

Both snapshots write to the `olist_snapshots` dataset and have `invalidate_hard_deletes=True`.

**Run snapshots before dimension models**:
```bash
dbt snapshot   # must run first
dbt run        # then build dimension and fact models
```

---

## Data Quality Tests

Defined in `models/dimensions/schema.yml` and `models/facts/schema.yml` using dbt-native tests plus the `dbt_utils` and `dbt_expectations` packages.

| Model | Column | Test |
|---|---|---|
| `dim_customers` | `dbt_scd_id` | `unique`, `not_null` |
| `dim_sellers` | `dbt_scd_id` | `unique`, `not_null` |
| `dim_products` | `product_id` | `unique`, `not_null` |
| `fact_order_items` | `product_id` | `not_null`, referential integrity → `dim_products.product_id` |
| `fact_order_items` | `seller_scd_id` | `not_null`, referential integrity → `dim_sellers.dbt_scd_id` |
| `fact_order_items` | `customer_scd_id` | `not_null`, referential integrity → `dim_customers.dbt_scd_id` |
| `fact_order_items` | `order_purchase_date` | `not_null`, column type must be `date` (`dbt_expectations`) |
| `fact_order_items` | `payment_value` | `not_null`, value ≥ 0 (`dbt_utils.accepted_range`) |

Run all tests:
```bash
dbt test
```

---

## Example Queries

### Product sales by category
```sql
SELECT
  dp.product_category_name_english,
  SUM(oi.payment_value)        AS total_sales,
  COUNT(DISTINCT oi.order_id)  AS order_count,
  AVG(oi.price)                AS avg_unit_price
FROM `olist_data_warehouse.order_items` oi
JOIN `olist_data_warehouse.products` dp ON oi.product_id = dp.product_id
GROUP BY 1
ORDER BY total_sales DESC;
```

### Seller revenue with historical location (SCD2)
```sql
SELECT
  ds.seller_city,
  ds.seller_state,
  SUM(oi.payment_value)        AS revenue,
  COUNT(DISTINCT oi.order_id)  AS orders
FROM `olist_data_warehouse.order_items` oi
JOIN `olist_data_warehouse.sellers` ds ON oi.seller_scd_id = ds.dbt_scd_id
GROUP BY 1, 2
ORDER BY revenue DESC;
```

### Payment method breakdown
```sql
SELECT
  payment_type,
  COUNT(*)           AS transaction_count,
  SUM(payment_value) AS total_revenue,
  AVG(payment_value) AS avg_payment
FROM `olist_data_warehouse.order_payments`
GROUP BY 1
ORDER BY total_revenue DESC;
```

### Average review score by product category
```sql
SELECT
  dp.product_category_name_english,
  ROUND(AVG(r.review_score), 2) AS avg_score,
  COUNT(*)                      AS review_count
FROM `olist_data_warehouse.order_reviews` r
JOIN `olist_data_warehouse.order_items` oi ON r.order_id = oi.order_id
JOIN `olist_data_warehouse.products` dp    ON oi.product_id = dp.product_id
GROUP BY 1
ORDER BY avg_score DESC;
```

### Monthly revenue trend
```sql
SELECT
  FORMAT_DATE('%Y-%m', oi.order_purchase_date) AS month,
  SUM(oi.payment_value)                        AS revenue,
  COUNT(DISTINCT oi.order_id)                  AS orders
FROM `olist_data_warehouse.order_items` oi
GROUP BY 1
ORDER BY 1;
```
