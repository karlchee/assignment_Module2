import subprocess
import sys
from pathlib import Path

from dagster import AssetExecutionContext, MaterializeResult, asset

PROJECT_DIR = Path(__file__).parent.parent
DBT_PROJECT_DIR = PROJECT_DIR / "olist_warehouse"

sys.path.insert(0, str(PROJECT_DIR))


@asset(group_name="ingestion", compute_kind="bigquery")
def staging_tables(context: AssetExecutionContext) -> MaterializeResult:
    """Load all CSV files into BigQuery olist_staging tables."""
    from load_to_bigquery import main

    main(context.log)
    return MaterializeResult(metadata={"tables_loaded": len([
        "customers", "sellers", "products", "products_category_name_translation",
        "geolocation", "orders", "order_items", "order_payments", "order_reviews",
    ])})


@asset(deps=[staging_tables], group_name="warehouse", compute_kind="dbt")
def dbt_warehouse(context: AssetExecutionContext) -> MaterializeResult:
    """Run dbt transformations to build olist_data_warehouse."""
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", str(DBT_PROJECT_DIR), "--project-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Exception(f"dbt run failed:\n{result.stderr}")
    return MaterializeResult(metadata={"status": "success"})
