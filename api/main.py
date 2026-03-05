from fastapi import FastAPI
from app.settings import settings

app = FastAPI(title="Retail Analytics API", version="0.2.0")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": settings.project_name,
    }
