from dagster import Definitions, ScheduleDefinition, define_asset_job

from dagster_pipeline.assets import dbt_warehouse, staging_tables

# Define a job that runs both assets
elt_job = define_asset_job(
    "elt_job",
    tags={"environment": "production"},
)

# Define a schedule to run the job daily at midnight
elt_schedule = ScheduleDefinition(
    job=elt_job,
    cron_schedule="0 0 * * *",  # Daily at 00:00 (midnight)
)

defs = Definitions(
    assets=[staging_tables, dbt_warehouse],
    schedules=[elt_schedule],
    jobs=[elt_job],
)
