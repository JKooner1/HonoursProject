import streamlit as st
import requests

st.set_page_config(page_title="Retail Analytics Dashboard", layout="wide")

st.title("Retail Analytics Dashboard (Prototype)")
st.caption("Backend-first build. Minimal dashboard to confirm API wiring.")

api_base = st.text_input("API Base URL", "http://127.0.0.1:8000")

if st.button("Check API Health"):
    try:
        r = requests.get(f"{api_base}/health", timeout=5)
        st.write(r.status_code, r.json())
    except Exception as e:
        st.error(f"API call failed: {e}")
