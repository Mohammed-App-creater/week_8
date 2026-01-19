# Medical Warehouse dbt Project

This project contains the dbt models for the Medical Warehouse, transforming raw data into a star schema suitable for analytics.

## Setup

1.  **Install Dependencies**:
    ```bash
    dbt deps
    ```

2.  **Environment Variables**:
    You must set the following environment variables to connect to the PostgreSQL database:
    *   `DB_HOST`
    *   `DB_USER`
    *   `DB_PASSWORD`
    *   `DB_NAME`
    *   `DB_SCHEMA` (optional, defaults to `analytics`)

## Running the Project

*   **Run Models**:
    ```bash
    dbt run
    ```

*   **Run Tests**:
    ```bash
    dbt test
    ```

*   **Generate Documentation**:
    ```bash
    dbt docs generate && dbt docs serve
    ```

## Local Validation

To validate the project structure and SQL without a database connection (compilation only):
```bash
dbt compile
```

To fully validate, ensure your local Postgres is running and env vars are set, then run `dbt build`.
