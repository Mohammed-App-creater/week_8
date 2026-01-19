from fastapi import FastAPI
import os

app = FastAPI(title="Medical Data Analytics API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Medical Data Analytics API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# TODO: Add endpoints for Task 4
# - Get message statistics
# - Get channel comparison
# - Get YOLO enrichment results
