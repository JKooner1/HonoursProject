from fastapi import FastAPI, File, HTTPException, UploadFile

from app.etl import (
    append_sales_data,
    calculate_kpis,
    daily_units_breakdown,
    load_sales_data,
    parse_daily_product_sales_report,
    top_products,
    weekly_summary,
)
from app.forecast import forecast_weekly_sales
from app.settings import settings

app = FastAPI(title="Retail Analytics API", version="0.5.0")


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
        cleaned_df = parse_daily_product_sales_report(content)
        combined_df = append_sales_data(cleaned_df, settings.parquet_path)

        return {
            "message": "Report uploaded and processed successfully.",
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


@app.get("/top-products")
def get_top_products(limit: int = 10):
    df = load_sales_data(settings.parquet_path)
    return top_products(df, limit=limit)


@app.get("/weekly-summary")
def get_weekly_summary():
    df = load_sales_data(settings.parquet_path)
    return weekly_summary(df)


@app.get("/daily-units")
def get_daily_units():
    df = load_sales_data(settings.parquet_path)
    return daily_units_breakdown(df)


@app.get("/forecast")
def get_forecast(periods: int = 4):
    df = load_sales_data(settings.parquet_path)
    return forecast_weekly_sales(df, periods=periods)