import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "academic-era-488315-j5"
DATASET_ID = "olist_staging"
CREDENTIALS_PATH = "/home/karlchee/Keys/academic-era-488315-j5-52715453be94.json"
DATA_DIR = "/home/karlchee/assignment_Module2/data"

FILES = [
    ("olist_customers_dataset.csv",              "customers"),
    ("olist_sellers_dataset.csv",                "sellers"),
    ("olist_products_dataset.csv",               "products"),
    ("product_category_name_translation.csv",    "products_category_name_translation"),
    ("olist_geolocation_dataset.csv",            "geolocation"),
    ("olist_orders_dataset.csv",                 "orders"),
    ("olist_order_items_dataset.csv",            "order_items"),
    ("olist_order_payments_dataset.csv",         "order_payments"),
    ("olist_order_reviews_dataset.csv",          "order_reviews"),
]


def main(log=None):
    def log_info(msg):
        if log:
            log.info(msg)
        else:
            print(msg)

    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
    client = bigquery.Client(project=PROJECT_ID, credentials=credentials)

    # Create dataset if it doesn't exist
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    dataset_ref.location = "US"
    client.create_dataset(dataset_ref, exists_ok=True)
    log_info(f"Dataset '{DATASET_ID}' ready.")

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    for filename, table_name in FILES:
        file_path = f"{DATA_DIR}/{filename}"
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

        df = pd.read_csv(file_path, encoding="utf-8-sig")

        # Drop existing table to avoid partitioning/schema conflicts
        client.delete_table(table_ref, not_found_ok=True)
        log_info(f"Loading {filename} -> {table_name} ...")

        job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # wait for job to complete
        table = client.get_table(table_ref)
        log_info(f"  done. {table.num_rows} rows loaded.")

    log_info("All tables loaded successfully.")


if __name__ == "__main__":
    main()
