from fastapi import FastAPI
from api.routers import analytics, reports

app = FastAPI(
    title="Telegram Data Warehouse Analytics API",
    description="Read-only API for accessing analytics from the Telegram data warehouse.",
    version="1.0.0"
)

app.include_router(analytics.router)
app.include_router(reports.router)

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
