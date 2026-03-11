from __future__ import annotations

import csv
import re
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd


EXPECTED_REPORT_TITLE = "Daily Product Sales Report"

COL_PRODUCT = 8
COL_WED = 19
COL_THU = 23
COL_FRI = 26
COL_SAT = 28
COL_SUN = 31
COL_MON = 33
COL_TUE = 37
COL_TOTAL_UNITS = 42
COL_VALUE = 46
COL_COST = 50
COL_PROFIT = 53
COL_IN_STOCK = 56
COL_ON_ORDER = 59
COL_MARGIN_PERCENT = 61


def _safe_get(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


def _to_int(value: str) -> int:
    value = str(value).strip().replace(",", "")
    if value == "":
        return 0
    return int(float(value))


def _to_float(value: str) -> float:
    value = str(value).strip().replace(",", "")
    if value == "":
        return 0.0
    return float(value)


def _extract_report_dates(lines: list[str]) -> tuple[str, str]:
    joined = "\n".join(lines[:12])

    match = re.search(
        r"(\d{2}-[A-Za-z]{3}-\d{4})\s+to\s+(\d{2}-[A-Za-z]{3}-\d{4})",
        joined,
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError("Could not detect report date range in uploaded file.")

    start_date = datetime.strptime(match.group(1), "%d-%b-%Y").date().isoformat()
    end_date = datetime.strptime(match.group(2), "%d-%b-%Y").date().isoformat()
    return start_date, end_date


def parse_daily_product_sales_report(content: bytes) -> pd.DataFrame:
    text = content.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()

    if EXPECTED_REPORT_TITLE.lower() not in text.lower():
        raise ValueError(
            "Uploaded file is not a recognised Daily Product Sales Report export."
        )

    week_start, week_end = _extract_report_dates(lines)

    reader = csv.reader(StringIO(text))
    rows = list(reader)

    records: list[dict[str, Any]] = []
    current_department = ""
    current_sub_department = ""

    for row in rows:
        if not row:
            continue

        product = _safe_get(row, COL_PRODUCT)

        dept_value = _safe_get(row, 5)
        dept_name = _safe_get(row, 12)

        if dept_value == "Dept:" and dept_name:
            current_department = dept_name
            continue

        if dept_value == "Sub Dept:" and dept_name:
            current_sub_department = dept_name
            continue

        if product == "":
            continue

        if product.lower() in {
            "product description",
            "daily product sales report",
        }:
            continue

        total_units_raw = _safe_get(row, COL_TOTAL_UNITS)
        value_raw = _safe_get(row, COL_VALUE)

        if total_units_raw == "" and value_raw == "":
            continue

        records.append(
            {
                "week_start": week_start,
                "week_end": week_end,
                "department": current_department,
                "sub_department": current_sub_department,
                "product": product,
                "wed_units": _to_int(_safe_get(row, COL_WED)),
                "thu_units": _to_int(_safe_get(row, COL_THU)),
                "fri_units": _to_int(_safe_get(row, COL_FRI)),
                "sat_units": _to_int(_safe_get(row, COL_SAT)),
                "sun_units": _to_int(_safe_get(row, COL_SUN)),
                "mon_units": _to_int(_safe_get(row, COL_MON)),
                "tue_units": _to_int(_safe_get(row, COL_TUE)),
                "total_units": _to_int(total_units_raw),
                "sales_value": round(_to_float(value_raw), 2),
                "cost_value": round(_to_float(_safe_get(row, COL_COST)), 3),
                "profit_value": round(_to_float(_safe_get(row, COL_PROFIT)), 2),
                "in_stock": _to_int(_safe_get(row, COL_IN_STOCK)),
                "on_order": _to_int(_safe_get(row, COL_ON_ORDER)),
                "margin_percent": round(_to_float(_safe_get(row, COL_MARGIN_PERCENT)), 2),
            }
        )

    if not records:
        raise ValueError("No product rows were found in the uploaded report.")

    df = pd.DataFrame(records)

    df = (
        df.drop_duplicates(subset=["week_start", "week_end", "product"])
        .sort_values(["week_start", "department", "sub_department", "product"])
        .reset_index(drop=True)
    )

    return df


def empty_sales_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "week_start",
            "week_end",
            "department",
            "sub_department",
            "product",
            "wed_units",
            "thu_units",
            "fri_units",
            "sat_units",
            "sun_units",
            "mon_units",
            "tue_units",
            "total_units",
            "sales_value",
            "cost_value",
            "profit_value",
            "in_stock",
            "on_order",
            "margin_percent",
        ]
    )


def load_sales_data(parquet_path: Path) -> pd.DataFrame:
    if not parquet_path.exists():
        return empty_sales_dataframe()

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

    combined = (
        combined.drop_duplicates(subset=["week_start", "week_end", "product"])
        .sort_values(["week_start", "department", "sub_department", "product"])
        .reset_index(drop=True)
    )

    save_sales_data(combined, parquet_path)
    return combined


def reset_sales_data(parquet_path: Path) -> None:
    if parquet_path.exists():
        parquet_path.unlink()


def calculate_kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_sales_value": 0.0,
            "total_units": 0,
            "total_products": 0,
            "total_profit_value": 0.0,
            "date_from": None,
            "date_to": None,
        }

    return {
        "total_sales_value": round(float(df["sales_value"].sum()), 2),
        "total_units": int(df["total_units"].sum()),
        "total_products": int(df["product"].nunique()),
        "total_profit_value": round(float(df["profit_value"].sum()), 2),
        "date_from": str(df["week_start"].min()),
        "date_to": str(df["week_end"].max()),
    }


def top_products(df: pd.DataFrame, limit: int = 10) -> list[dict]:
    if df.empty:
        return []

    result = (
        df.groupby("product", as_index=False)
        .agg(
            total_units=("total_units", "sum"),
            sales_value=("sales_value", "sum"),
            profit_value=("profit_value", "sum"),
        )
        .sort_values(["sales_value", "total_units"], ascending=[False, False])
        .head(limit)
        .reset_index(drop=True)
    )

    result["sales_value"] = result["sales_value"].round(2)
    result["profit_value"] = result["profit_value"].round(2)

    return result.to_dict(orient="records")


def weekly_summary(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    result = (
        df.groupby(["week_start", "week_end"], as_index=False)
        .agg(
            total_units=("total_units", "sum"),
            sales_value=("sales_value", "sum"),
            profit_value=("profit_value", "sum"),
            total_products=("product", "nunique"),
            row_count=("product", "count"),
        )
        .sort_values(["week_start", "week_end"])
        .reset_index(drop=True)
    )

    result["sales_value"] = result["sales_value"].round(2)
    result["profit_value"] = result["profit_value"].round(2)

    return result.to_dict(orient="records")


def daily_units_breakdown(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    rows: list[dict] = []

    for _, record in df.iterrows():
        rows.append(
            {
                "week_start": record["week_start"],
                "week_end": record["week_end"],
                "wed_units": int(record["wed_units"]),
                "thu_units": int(record["thu_units"]),
                "fri_units": int(record["fri_units"]),
                "sat_units": int(record["sat_units"]),
                "sun_units": int(record["sun_units"]),
                "mon_units": int(record["mon_units"]),
                "tue_units": int(record["tue_units"]),
            }
        )

    breakdown_df = pd.DataFrame(rows)

    result = (
        breakdown_df.groupby(["week_start", "week_end"], as_index=False)
        .sum()
        .sort_values(["week_start", "week_end"])
        .reset_index(drop=True)
    )

    return result.to_dict(orient="records")


def list_uploaded_weeks(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    weeks = (
        df.groupby(["week_start", "week_end"], as_index=False)
        .agg(
            row_count=("product", "count"),
            total_units=("total_units", "sum"),
            sales_value=("sales_value", "sum"),
            profit_value=("profit_value", "sum"),
            distinct_products=("product", "nunique"),
        )
        .sort_values(["week_start", "week_end"])
        .reset_index(drop=True)
    )

    weeks["sales_value"] = weeks["sales_value"].round(2)
    weeks["profit_value"] = weeks["profit_value"].round(2)

    return weeks.to_dict(orient="records")


def dataset_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "weeks_loaded": 0,
            "rows_loaded": 0,
            "distinct_products": 0,
            "date_from": None,
            "date_to": None,
        }

    week_count = (
        df[["week_start", "week_end"]]
        .drop_duplicates()
        .shape[0]
    )

    return {
        "weeks_loaded": int(week_count),
        "rows_loaded": int(len(df)),
        "distinct_products": int(df["product"].nunique()),
        "date_from": str(df["week_start"].min()),
        "date_to": str(df["week_end"].max()),
    }