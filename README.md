# Olist Data Pipeline

A modern data pipeline that ingests Brazilian ecommerce data (Olist dataset) into Google BigQuery and transforms it into an analytics-ready data warehouse using Dagster and dbt.

## Overview

This project implements an **ELT** (Extract, Load, Transform) pipeline:
- **Extract & Load**: CSV files are loaded directly into BigQuery staging tables
- **Transform**: dbt transforms the staging data into a structured data warehouse
- **Orchestration**: Dagster orchestrates the entire workflow with dependency management

## Architecture

```
CSV Data Files
    ↓
load_to_bigquery.py
    ↓
BigQuery Staging Dataset (olist_staging)
    ↓
dbt Transformation
    ↓
BigQuery Data Warehouse (olist_data_warehouse)
```

## Project Structure

```
assignment_Module2/
├── data/                              # Source CSV files
│   ├── olist_customers_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   └── product_category_name_translation.csv
│
├── dagster_pipeline/                 # Dagster orchestration
│   ├── definitions.py                # Dagster definitions & asset graph
│   ├── assets.py                     # Asset definitions
│   └── __init__.py
│
├── olist_warehouse/                  # dbt transformation project
│   ├── dbt_project.yml              # dbt configuration
│   ├── profiles.yml                 # dbt database profiles
│   ├── models/                      # dbt SQL models
│   │   ├── order_items.sql
│   │   ├── order_payments.sql
│   │   ├── order_reviews.sql
│   │   ├── schema.yml               # dbt schema definitions
│   │   ├── source.yml               # dbt source definitions
│   │   └── star/                    # star schema models
│   ├── tests/                       # dbt tests
│   ├── macros/                      # dbt macros
│   └── dbt_packages/                # dbt package dependencies
│
├── load_to_bigquery.py              # Script to load CSV files to BigQuery
├── workspace.yaml                   # Dagster workspace configuration
└── README.md                        # This file
```

## Data Model

The pipeline processes the following tables:

| Table | Description |
|-------|-------------|
| customers | Customer information and location |
| sellers | Seller details |
| products | Product information with categories |
| products_category_name_translation | Translation of product category names |
| geolocation | Geographic location data |
| orders | Order header information |
| order_items | Line items for each order |
| order_payments | Payment details for orders |
| order_reviews | Customer review data |

## Prerequisites

- Python 3.8+
- Google Cloud Platform account with BigQuery access
- Service account credentials (JSON file) for BigQuery authentication
- dbt CLI
- Dagster

## Setup

### 1. Install Dependencies

```bash
pip install dagster pandas google-cloud-bigquery google-oauth2 dbt-bigquery
```

### 2. Configure BigQuery Authentication

Place your GCP service account JSON file at:
```
meltano-olist/academic-era-488315-j5-52715453be94.json
```

The `load_to_bigquery.py` script references this path to authenticate with BigQuery.

### 3. Configure dbt Profiles

Update `olist_warehouse/profiles.yml` with your BigQuery project details if needed.

## Running the Pipeline

### Option 1: Using Dagster UI (Recommended)

```bash
dagster dev
```

This starts the Dagster development server at `http://localhost:3000` where you can:
- View the asset graph
- Materialize assets manually
- Monitor pipeline runs
- View logs and metadata

### Option 2: Command Line

```bash
# Load data to BigQuery staging
python load_to_bigquery.py

# Run dbt transformations
cd olist_warehouse
dbt run
```

## Pipeline Steps

### Step 1: Data Ingestion (`staging_tables` asset)
- Reads CSV files from the `data/` directory
- Loads them as tables into BigQuery `olist_staging` dataset
- Creates/truncates tables as needed to maintain fresh data

**Output**: 9 staging tables in BigQuery

### Step 2: Data Transformation (`dbt_warehouse` asset)
- Depends on `staging_tables` (automatically triggered after ingestion)
- Runs dbt models to transform and structure the data
- Builds star schema and dimensional models
- Applies data quality tests

**Output**: Transformed tables in BigQuery data warehouse

## Configuration

### BigQuery Settings (in `load_to_bigquery.py`)
- **Project ID**: `academic-era-488315-j5`
- **Staging Dataset**: `olist_staging`
- **Credentials**: Service account JSON file
- **Data Directory**: `data/`

### dbt Settings (in `olist_warehouse/`)
- **Profile**: `olist_warehouse`
- **Target Database**: BigQuery
- **Models Location**: `models/`
- **Tests Location**: `tests/`

### Dagster Settings (in `workspace.yaml`)
- **Load Definition**: `dagster_pipeline/definitions.py`
- **Assets**: `staging_tables`, `dbt_warehouse`

## Key Features

✅ **Automated Orchestration**: Dagster manages dependencies and execution order  
✅ **dbt Integration**: Leverages dbt packages (dbt-utils, dbt-expectations, dbt-date)  
✅ **Version Control**: All SQL and Python code managed in Git  
✅ **Monitoring**: Built-in logging and metadata tracking  
✅ **Scalability**: Designed to run on cloud infrastructure  

## Monitoring & Logs

- **Dagster Logs**: View in Dagster UI under each asset run
- **dbt Logs**: Check `olist_warehouse/logs/` directory
- **BigQuery Logs**: Monitor in Google Cloud Console

## Troubleshooting

### Authentication Issues
- Verify service account JSON path is correct
- Ensure service account has BigQuery admin permissions
- Check GCP project ID matches configuration

### dbt Errors
- Run `dbt debug` to verify database connection
- Check `dbt_project.yml` for correct profile configuration
- View dbt logs in the `olist_warehouse/logs/` directory

### Data Loading Issues
- Verify CSV files exist in the `data/` directory
- Check file encoding (UTF-8 expected)
- Ensure BigQuery dataset exists and is accessible

## Technologies Used

- **Dagster**: Workflow orchestration
- **dbt**: Data transformation with SQL
- **Google BigQuery**: Cloud data warehouse
- **Python**: Data loading and scripting
- **Pandas**: Data manipulation

## Future Enhancements

- Add scheduling for automated daily runs
- Implement incremental dbt models for large datasets
- Add data quality monitoring and alerting
- Expand star schema with additional dimension tables

## Note

The `meltano-olist/` directory contains configuration files but is **not used in the active ELT process**. This project uses Dagster and dbt directly for orchestration and transformation.

## License

This project is part of an academic assignment.
