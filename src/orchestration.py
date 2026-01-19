from dagster import asset, Definitions, AssetSelection, define_asset_job

@asset
def raw_telegram_data():
    """Task 1: Scrape Telegram data."""
    # Logic to run scraper.py
    pass

@asset(deps=[raw_telegram_data])
def postgres_raw_data():
    """Task 1: Load data to PostgreSQL."""
    # Logic to run load_raw_to_postgres.py
    pass

@asset(deps=[postgres_raw_data])
def dbt_transformed_data():
    """Task 2: Run dbt transformations."""
    # Logic to run dbt run
    pass

@asset(deps=[postgres_raw_data])
def yolo_enriched_data():
    """Task 3: Run YOLO enrichment."""
    # Logic to run yolo_enrichment.py
    pass

defs = Definitions(
    assets=[raw_telegram_data, postgres_raw_data, dbt_transformed_data, yolo_enriched_data],
)
