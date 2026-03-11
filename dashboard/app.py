import pandas as pd
import requests
import streamlit as st

API_BASE_DEFAULT = "http://127.0.0.1:8000"

st.set_page_config(page_title="Retail Analytics Dashboard", layout="wide")
st.title("Retail Analytics Dashboard")
st.caption("Weekly sales analytics dashboard for a UK convenience store.")


@st.cache_data(ttl=30)
def fetch_json(url: str):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


def post_csv(api_base: str, uploaded_file):
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
    response = requests.post(f"{api_base}/upload/csv", files=files, timeout=60)
    response.raise_for_status()
    return response.json()


def post_reset(api_base: str):
    response = requests.post(f"{api_base}/reset-data", timeout=20)
    response.raise_for_status()
    return response.json()


with st.sidebar:
    st.header("Settings")
    api_base = st.text_input("API Base URL", API_BASE_DEFAULT)

    st.markdown("---")
    st.subheader("Upload Weekly Sales Report")
    uploaded_file = st.file_uploader(
        "Choose Daily Product Sales Report CSV",
        type=["csv"],
    )

    if uploaded_file is not None:
        if st.button("Upload Report", use_container_width=True):
            try:
                result = post_csv(api_base, uploaded_file)
                st.success("Report uploaded successfully.")
                st.json(result)
                st.cache_data.clear()
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

    st.markdown("---")
    st.subheader("Admin")
    if st.button("Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("Reset Stored Data", use_container_width=True):
        try:
            result = post_reset(api_base)
            st.warning(result["message"])
            st.cache_data.clear()
            st.rerun()
        except Exception as exc:
            st.error(f"Reset failed: {exc}")


try:
    kpis = fetch_json(f"{api_base}/kpis")
    top_products = fetch_json(f"{api_base}/top-products")
    weekly_summary = fetch_json(f"{api_base}/weekly-summary")
    daily_units = fetch_json(f"{api_base}/daily-units")
    forecast_data = fetch_json(f"{api_base}/forecast?periods=4")
    weeks_data = fetch_json(f"{api_base}/weeks")
    dataset_info = fetch_json(f"{api_base}/dataset-summary")
except Exception as exc:
    st.error(f"Could not load dashboard data from API: {exc}")
    st.info("Make sure the FastAPI backend is running on port 8000.")
    st.stop()


if dataset_info["weeks_loaded"] < 3:
    st.warning(
        "Forecasting is currently limited. At least 3 weekly reports are needed before forecasting becomes useful."
    )

st.subheader("Dataset Overview")

d1, d2, d3, d4 = st.columns(4)
d1.metric("Weeks Loaded", f"{dataset_info['weeks_loaded']:,}")
d2.metric("Rows Loaded", f"{dataset_info['rows_loaded']:,}")
d3.metric("Distinct Products", f"{dataset_info['distinct_products']:,}")
d4.metric(
    "Dataset Range",
    "N/A" if not dataset_info["date_from"] else f"{dataset_info['date_from']} to {dataset_info['date_to']}",
)

st.markdown("---")

st.subheader("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales Value", f"£{kpis['total_sales_value']:,.2f}")
col2.metric("Total Units Sold", f"{kpis['total_units']:,}")
col3.metric("Distinct Products", f"{kpis['total_products']:,}")
col4.metric("Total Profit", f"£{kpis['total_profit_value']:,.2f}")

st.caption(f"Date range: {kpis['date_from']} to {kpis['date_to']}")

st.markdown("---")

left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.subheader("Top Products by Sales Value")
    top_products_df = pd.DataFrame(top_products)

    if top_products_df.empty:
        st.info("No product data available yet.")
    else:
        top_products_df = top_products_df.rename(
            columns={
                "product": "Product",
                "total_units": "Units Sold",
                "sales_value": "Sales Value (£)",
                "profit_value": "Profit (£)",
            }
        )
        st.dataframe(top_products_df, use_container_width=True, hide_index=True)

with right_col:
    st.subheader("Uploaded Weeks")
    weeks_df = pd.DataFrame(weeks_data)

    if weeks_df.empty:
        st.info("No weekly reports uploaded yet.")
    else:
        weeks_df = weeks_df.rename(
            columns={
                "week_start": "Week Start",
                "week_end": "Week End",
                "row_count": "Rows",
                "total_units": "Units Sold",
                "sales_value": "Sales Value (£)",
                "profit_value": "Profit (£)",
                "distinct_products": "Distinct Products",
            }
        )
        st.dataframe(weeks_df, use_container_width=True, hide_index=True)

st.markdown("---")

left_col_2, right_col_2 = st.columns([1.2, 1])

with left_col_2:
    st.subheader("Weekly Summary")
    weekly_summary_df = pd.DataFrame(weekly_summary)

    if weekly_summary_df.empty:
        st.info("No weekly summary available yet.")
    else:
        weekly_summary_df = weekly_summary_df.rename(
            columns={
                "week_start": "Week Start",
                "week_end": "Week End",
                "total_units": "Units Sold",
                "sales_value": "Sales Value (£)",
                "profit_value": "Profit (£)",
                "total_products": "Distinct Products",
                "row_count": "Rows",
            }
        )
        st.dataframe(weekly_summary_df, use_container_width=True, hide_index=True)

with right_col_2:
    st.subheader("Sales Forecast")

    forecast_history_df = pd.DataFrame(forecast_data.get("history", []))
    forecast_future_df = pd.DataFrame(forecast_data.get("forecast", []))
    forecast_message = forecast_data.get("message", "")

    if forecast_message:
        st.info(forecast_message)

    if not forecast_history_df.empty:
        forecast_history_df["type"] = "Historical"

    if not forecast_future_df.empty:
        forecast_future_df["type"] = "Forecast"

    forecast_chart_df = pd.concat(
        [forecast_history_df, forecast_future_df],
        ignore_index=True,
    )

    if forecast_chart_df.empty:
        st.info("No forecast data available yet.")
    else:
        forecast_chart_df = forecast_chart_df.rename(
            columns={
                "week_end": "Week End",
                "sales_value": "Sales Value (£)",
                "type": "Series",
            }
        )

        st.line_chart(
            data=forecast_chart_df,
            x="Week End",
            y="Sales Value (£)",
            color="Series",
        )

        st.dataframe(forecast_chart_df, use_container_width=True, hide_index=True)

st.markdown("---")

st.subheader("Daily Units Breakdown")

daily_units_df = pd.DataFrame(daily_units)

if daily_units_df.empty:
    st.info("No daily units data available yet.")
else:
    chart_df = daily_units_df.copy()

    if "week_start" in chart_df.columns and "week_end" in chart_df.columns:
        chart_df["label"] = (
            chart_df["week_start"].astype(str) + " to " + chart_df["week_end"].astype(str)
        )
    else:
        chart_df["label"] = "Week"

    melted_df = chart_df.melt(
        id_vars=["label"],
        value_vars=[
            "wed_units",
            "thu_units",
            "fri_units",
            "sat_units",
            "sun_units",
            "mon_units",
            "tue_units",
        ],
        var_name="day",
        value_name="units",
    )

    day_name_map = {
        "wed_units": "Wednesday",
        "thu_units": "Thursday",
        "fri_units": "Friday",
        "sat_units": "Saturday",
        "sun_units": "Sunday",
        "mon_units": "Monday",
        "tue_units": "Tuesday",
    }

    melted_df["day"] = melted_df["day"].map(day_name_map)

    st.bar_chart(
        data=melted_df,
        x="day",
        y="units",
    )

    st.dataframe(
        daily_units_df.rename(
            columns={
                "week_start": "Week Start",
                "week_end": "Week End",
                "wed_units": "Wed",
                "thu_units": "Thu",
                "fri_units": "Fri",
                "sat_units": "Sat",
                "sun_units": "Sun",
                "mon_units": "Mon",
                "tue_units": "Tue",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )