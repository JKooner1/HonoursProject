from __future__ import annotations

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def build_weekly_sales_series(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["week_end", "sales_value"])

    weekly = (
        df.groupby("week_end", as_index=False)
        .agg(sales_value=("sales_value", "sum"))
        .sort_values("week_end")
        .reset_index(drop=True)
    )

    weekly["week_end"] = pd.to_datetime(weekly["week_end"])
    return weekly


def forecast_weekly_sales(df: pd.DataFrame, periods: int = 4) -> dict:
    weekly = build_weekly_sales_series(df)

    if weekly.empty:
        return {
            "history": [],
            "forecast": [],
            "message": "No data available for forecasting.",
        }

    if len(weekly) < 3:
        return {
            "history": weekly.assign(
                week_end=weekly["week_end"].dt.date.astype(str),
                sales_value=weekly["sales_value"].round(2),
            ).to_dict(orient="records"),
            "forecast": [],
            "message": "At least 3 weekly reports are needed before forecasting is useful.",
        }

    series = weekly.set_index("week_end")["sales_value"]

    model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal=None,
        initialization_method="estimated",
    )

    fitted_model = model.fit(optimized=True)
    forecast_values = fitted_model.forecast(periods)

    forecast_df = pd.DataFrame(
        {
            "week_end": forecast_values.index,
            "sales_value": forecast_values.values,
        }
    )

    history_df = weekly.copy()
    history_df["week_end"] = history_df["week_end"].dt.date.astype(str)
    history_df["sales_value"] = history_df["sales_value"].round(2)

    forecast_df["week_end"] = forecast_df["week_end"].dt.date.astype(str)
    forecast_df["sales_value"] = forecast_df["sales_value"].round(2)

    return {
        "history": history_df.to_dict(orient="records"),
        "forecast": forecast_df.to_dict(orient="records"),
        "message": "Forecast generated successfully.",
    }