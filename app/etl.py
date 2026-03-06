from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


REQUIRED_CANONICAL_COLUMNS = ["date", "product", "quantity", "total"]


COLUMN_ALIASES: Dict[str, List[str]] = {
    "date": [
        "date",
        "sale_date",
        "transaction_date",
        "day",
    ],
    "product": [
        "product",
        "product_name",
        "item",
        "description",
        "name",
    ],
    "quantity": [
        "quantity",
        "qty",
        "units",
        "items_sold",
    ],
    "total": [
        "total",
        "sales",
        "sales_value",
        "revenue",
        "amount",
        "line_total",
    ],
}


def _normalise_column_name(name: str) -> str:
    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def _build_column_mapping(columns: List[str]) -> Dict[str, str]:
    normalised = {_normalise_column_name(col): col for col in columns}
    mapping: Dict[str, str] = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalised:
                mapping[normalised[alias]] = canonical
                break

    return mapping


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_CANONICAL_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns after mapping: {missing}. "
            "Expected columns matching date, product, quantity, total."
        )


def clean_sales_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Uploaded CSV is empty.")

    df = df.copy()
    df.columns = [_normalise_column_name(col) for col in df.columns]

    mapping = _build_column_mapping(list(df.columns))
    df = df.rename(columns=mapping)

    _validate_columns(df)

    df = df[REQUIRED_CANONICAL_COLUMNS].copy()

    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["product"] = df["product"].astype(str).str.strip()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["total"] = pd.to_numeric(df["total"], errors="coerce")

    df = df.dropna(subset=["date", "product", "quantity", "total"])
    df = df[df["product"] != ""]
    df = df[df["quantity"] >= 0]
    df = df[df["total"] >= 0]

    df["date"] = df["date"].dt.normalize()
    df["quantity"] = df["quantity"].astype(int)

    df = df.sort_values(["date", "product"]).reset_index(drop=True)

    if df.empty:
        raise ValueError("No valid rows remained after cleaning.")

    return df


def load_sales_data(parquet_path: Path) -> pd.DataFrame:
    if not parquet_path.exists():
        return pd.DataFrame(columns=REQUIRED_CANONICAL_COLUMNS)

    return pd.read_parquet(parquet_path)


def save_sales_data(df: pd.DataFrame, parquet_path: Path) -> None:
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, index=False)


def append_sales_data(new_df: pd.DataFrame, parquet_path: Path) -> pd.DataFrame:
    existing_df = load_sales_data(parquet_path)

    if existing_df.empty:
        combined = new_df.copy()
    else:
        combined = pd.concat([existing_df, new_df], ignore_index=True)

    combined = combined.drop_duplicates().sort_values(["date", "product"]).reset_index(drop=True)
    save_sales_data(combined, parquet_path)
    return combined


def calculate_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_revenue": 0.0,
            "total_units": 0,
            "total_rows": 0,
            "unique_products": 0,
            "date_from": None,
            "date_to": None,
        }

    return {
        "total_revenue": round(float(df["total"].sum()), 2),
        "total_units": int(df["quantity"].sum()),
        "total_rows": int(len(df)),
        "unique_products": int(df["product"].nunique()),
        "date_from": df["date"].min().date().isoformat(),
        "date_to": df["date"].max().date().isoformat(),
    }


def daily_sales(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    daily = (
        df.groupby("date", as_index=False)
        .agg(revenue=("total", "sum"), units=("quantity", "sum"))
        .sort_values("date")
    )

    daily["date"] = daily["date"].dt.date.astype(str)
    daily["revenue"] = daily["revenue"].round(2)

    return daily.to_dict(orient="records")


def top_products(df: pd.DataFrame, limit: int = 10) -> list[dict]:
    if df.empty:
        return []

    products = (
        df.groupby("product", as_index=False)
        .agg(revenue=("total", "sum"), units=("quantity", "sum"))
        .sort_values(["revenue", "units"], ascending=[False, False])
        .head(limit)
    )

    products["revenue"] = products["revenue"].round(2)
    return products.to_dict(orient="records")