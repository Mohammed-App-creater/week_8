# Telegram Data Warehouse Analytical API

This FastAPI-based service provides read-only analytical endpoints for the Telegram data warehouse. It connects to the PostgreSQL database and serves aggregated metrics.

## Setup

1.  **Environment Variables**:
    Ensure the root `.env` file contains the following database credentials:
    ```
    DB_NAME=...
    DB_USER=...
    DB_PASSWORD=...
    DB_HOST=...
    DB_PORT=...
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r api/requirements.txt
    ```

## Running the API

Run the API using `uvicorn` from the project root:

```bash
uvicorn api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation

Interactive documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### Health Check
- `GET /health`: Check if the API is running.

### Analytics
- `GET /analytics/top-channels`: Returns top channels by message volume with view statistics.
- `GET /analytics/messages-over-time`: Returns daily trend of message counts.
- `GET /analytics/image-engagement`: Compares engagement (views/forwards) for image vs. non-image posts.
- `GET /analytics/top-detected-objects`: Returns top detected objects from image enrichment data.

## Example Requests

```bash
# Get Top Channels
curl http://127.0.0.1:8000/analytics/top-channels

# Get Message Trends
curl http://127.0.0.1:8000/analytics/messages-over-time
```
