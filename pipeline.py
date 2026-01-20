import os
import sys
import subprocess
from dagster import (
    job,
    op,
    ScheduleDefinition,
    HookContext,
    failure_hook,
    Field,
    Nothing,
    In,
    Out,
    get_dagster_logger
)

# Logger
logger = get_dagster_logger()

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DBT_PROJECT_DIR = os.path.join(PROJECT_ROOT, "medical_warehouse")

def run_command(command, cwd=None, env=None):
    """
    Helper function to run shell commands using subprocess.
    """
    logger.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT,
            env=env or os.environ.copy(),
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Command Output:\n{result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command Failed:\n{e.stderr}")
        raise e

# Failure hook
@failure_hook
def notify_on_failure(context: HookContext):
    op_exception = context.op_exception
    logger.error(f"Op '{context.op.name}' failed!")
    if op_exception:
        logger.error(f"Exception: {op_exception}")

# Ops
@op(description="Scrape Telegram messages and images.", out=Out(Nothing))
def scrape_telegram_data(context):
    context.log.info("Starting Telegram Scraper...")
    run_command([sys.executable, os.path.join("src", "scraper.py")])
    context.log.info("Telegram Scraper finished successfully.")

@op(description="Load raw JSON data into PostgreSQL.", ins={"start": In(Nothing)}, out=Out(Nothing))
def load_raw_to_postgres(context):
    context.log.info("Starting Raw Data Loader...")
    run_command([sys.executable, os.path.join("src", "load_raw_to_postgres.py")])
    context.log.info("Raw Data Loader finished successfully.")

@op(description="Run dbt transformations.", ins={"start": In(Nothing)}, out=Out(Nothing))
def run_dbt_transformations(context):
    context.log.info("Starting dbt Transformations...")
    dbt_executable = "dbt"  # assumes dbt is installed in the venv
    run_command([dbt_executable, "run"], cwd=DBT_PROJECT_DIR)
    context.log.info("dbt Transformations finished successfully.")

@op(description="Run YOLOv8 object detection on images.", ins={"start": In(Nothing)}, out=Out(Nothing))
def run_yolo_enrichment(context):
    context.log.info("Starting YOLO Enrichment...")
    run_command([sys.executable, os.path.join("image_enrichment", "infer_images.py")])
    context.log.info("YOLO Enrichment finished successfully.")

# Pipeline
@job(hooks={notify_on_failure}, description="Orchestrates the Telegram ELT pipeline.")
def telegram_pipeline():
    loaded = load_raw_to_postgres(start=scrape_telegram_data())
    dbt_done = run_dbt_transformations(start=loaded)
    run_yolo_enrichment(start=dbt_done)

# Schedule: daily at 2:00 AM UTC
daily_2am_schedule = ScheduleDefinition(
    job=telegram_pipeline,
    cron_schedule="0 2 * * *",
    execution_timezone="UTC"
)

if __name__ == "__main__":
    print("Dagster pipeline 'telegram_pipeline' is ready. Run `dg dev -f pipeline.py` to start the UI.")
