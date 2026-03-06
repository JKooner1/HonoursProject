from io import BytesIO

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile

from app.etl import (
    append_sales_data,
    calculate_kpis,
    clean_sales_dataframe,
    daily_sales,
    load_sales_data,
    top_products,
)
from app.settings import settings

app = FastAPI(title="Retail Analytics API", version="0.3.0")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": settings.project_name,
        "parquet_path": str(settings.parquet_path),
    }


@app.post("/upload/csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        content = await file.read()
        raw_df = pd.read_csv(BytesIO(content))
        cleaned_df = clean_sales_dataframe(raw_df)
        combined_df = append_sales_data(cleaned_df, settings.parquet_path)

        return {
            "message": "CSV uploaded and processed successfully.",
            "uploaded_rows": int(len(cleaned_df)),
            "total_rows_stored": int(len(combined_df)),
            "kpis": calculate_kpis(combined_df),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc


@app.get("/kpis")
def get_kpis():
    df = load_sales_data(settings.parquet_path)
    return calculate_kpis(df)


@app.get("/daily")
def get_daily_sales():
    df = load_sales_data(settings.parquet_path)
    return daily_sales(df)


@app.get("/top-products")
def get_top_products(limit: int = 10):
    df = load_sales_data(settings.parquet_path)
    return top_products(df, limit=limit)