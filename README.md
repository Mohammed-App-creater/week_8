# Ethiopian Medical Data Warehouse (ELT Pipeline)

## 1. Project Overview
This project targets the development of a production-grade end-to-end ELT (Extract, Load, Transform) data pipeline designed to consolidate medical and pharmaceutical data from various Ethiopian Telegram channels. By scraping raw messages and images, loading them into a centralized PostgreSQL data lake, and performing sophisticated transformations with dbt, the system provides an analytics-ready platform. Enrichment via YOLO (You Only Look Once) for object detection on medical images and a FastAPI interface enable comprehensive market analysis and product discovery.

## 2. High-Level Architecture
The system follows a modern Data Engineering architecture:

```text
+------------------+      +-------------+      +--------------+
| Telegram Channels | ---> |  Scraper    | ---> |  Data Lake   |
| (Raw Data)       |      | (Telethon)  |      | (JSON/Images)|
+------------------+      +-------------+      +--------------+
                                                      |
                                                      v
+--------------+      +-------------+      +------------------+
| Analytical   | <--- |     dbt     | <--- |   PostgreSQL     |
| API (FastAPI)|      | (Transforms)|      | (Raw/Staging)    |
+--------------+      +-------------+      +------------------+
        ^                                             |
        |                                             v
        +---------------------------------------+-------------+
                                                | YOLO v11    |
                                                | Enrichment  |
                                                +-------------+
```

## 3. Project Structure
```text
.
├── api/                # FastAPI analytical API (Task 4)
├── data/               # Data lake (Task 1)
│   ├── raw/            # Raw JSON messages and images
│   └── processed/      # Cleaned/Enriched data
├── logs/               # Pipeline execution logs
├── medical_warehouse/  # dbt project: models, tests, and profiles (Task 2)
│   ├── models/         # Staging and Mart (Star Schema) models
│   └── tests/          # dbt data quality tests
├── scripts/            # Database initialization and one-off utilities
├── src/                # Core pipeline logic
│   ├── scraper.py      # Telegram scraping logic (Task 1)
│   ├── load_raw_to_postgres.py # Data loading to PostgreSQL (Task 1)
│   ├── yolo_enrichment.py # YOLO image object detection (Task 3)
│   └── orchestration.py # Dagster pipeline orchestration (Task 5)
├── tests/              # Unit and integration tests
├── .env                # Environment variables (Configuration)
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## 4. Environment Variables
Ensure a `.env` file exists in the root with the following variables:

| Variable | Description |
| :--- | :--- |
| `TELEGRAM_API_ID` | API ID from my.telegram.org |
| `TELEGRAM_API_HASH` | API Hash from my.telegram.org |
| `DB_HOST` | PostgreSQL Host (default: localhost) |
| `DB_PORT` | PostgreSQL Port (default: 5432) |
| `DB_NAME` | PostgreSQL Database Name |
| `DB_USER` | PostgreSQL Username |
| `DB_PASSWORD` | PostgreSQL Password |
| `YOLO_MODEL_PATH` | Path to the YOLO weights (optional) |

## 5. How to Run (High-Level)

### Prerequisites
- Python 3.9+
- PostgreSQL
- dbt-postgres

### Step 1: Scrape Data
Extract raw data from Telegram channels:
```bash
python src/scraper.py
```

### Step 2: Load to PostgreSQL
Load the raw JSON data into the `raw` schema in PostgreSQL:
```bash
python src/load_raw_to_postgres.py
```

### Step 3: Run dbt Transformations
Apply transformations and build the star schema:
```bash
cd medical_warehouse
dbt run
dbt test
```

### Step 4: YOLO Enrichment
Enrich image data using object detection:
```bash
python src/yolo_enrichment.py
```

### Step 5: Start API
Launch the FastAPI analytical server:
```bash
uvicorn api.main:app --reload
```

## 6. Notes for Evaluators
This project directly addresses the challenge requirements as follows:
- **Task 1**: Implemented robust scraper using Telethon and a Python-based loader for PostgreSQL.
- **Task 2**: Developed a dbt project with staging/mart models and schema tests.
- **Task 3**: Integrated YOLO logic for image-based product enrichment.
- **Task 4**: Exposed analytics via a FastAPI service.
- **Task 5**: Orchestrated the entire workflow using Dagster asset-based definitions.
