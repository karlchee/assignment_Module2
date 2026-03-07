import csv
import io
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "academic-era-488315-j5"
DATASET_ID = "olist_staging"
CREDENTIALS_PATH = "/home/karlchee/assignment_Module2/meltano-olist/academic-era-488315-j5-52715453be94.json"
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

credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
client = bigquery.Client(project=PROJECT_ID, credentials=credentials)

# Create dataset if it doesn't exist
dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
dataset_ref.location = "US"
client.create_dataset(dataset_ref, exists_ok=True)
print(f"Dataset '{DATASET_ID}' ready.\n")

for filename, table_name in FILES:
    file_path = f"{DATA_DIR}/{filename}"
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        content = f.read().replace("\r\n", "\n").replace("\r", "\n")

    headers = next(csv.reader(io.StringIO(content)))
    schema = [bigquery.SchemaField(col.strip(), "STRING") for col in headers]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        allow_quoted_newlines=True,
    )

    # Drop existing table to avoid partitioning/schema conflicts
    client.delete_table(table_ref, not_found_ok=True)
    print(f"Loading {filename} -> {table_name} ...", end=" ", flush=True)

    data = io.BytesIO(content.encode("utf-8"))
    job = client.load_table_from_file(data, table_ref, job_config=job_config)
    job.result()  # wait for job to complete
    table = client.get_table(table_ref)
    print(f"done. {table.num_rows} rows loaded.")

print("\nAll tables loaded successfully.")
