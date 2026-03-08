from dagster import Definitions

from dagster_pipeline.assets import dbt_warehouse, staging_tables

defs = Definitions(
    assets=[staging_tables, dbt_warehouse],
)
