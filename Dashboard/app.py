import streamlit as st
import pandas as pd
import json
import numpy as np
from datetime import datetime
import plotly.express as px
from azure.storage.blob import BlobServiceClient

st.set_page_config(
    page_title="Cairo Traffic Enforcement Command Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=storagetraffic11;AccountKey=FndnvLfVm8RgEvB7S3vIPnmeM9ukN51X8F/GoDQWB6K8ZQwe1Ukm86WOVVOK4Qsd0ywelUYDtByH+ASt7EZRpA==;EndpointSuffix=core.windows.net"

def parse_azure_json(raw_text):
    records = []
    if not raw_text.strip():
        return records
    try:
        parsed = json.loads(raw_text)
        return parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        for line in raw_text.splitlines():
            line = line.strip().rstrip(",")
            if line and line not in ["[", "]"]:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records

def fetch_container_data(container_name, max_blobs=10):
    # NO cache — fresh client every call
    client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    try:
        container_client = client.get_container_client(container_name)
        blobs = list(container_client.list_blobs())
        valid_blobs = [b for b in blobs if b.size > 0]
        recent_blobs = sorted(valid_blobs, key=lambda b: b.last_modified, reverse=True)[:max_blobs]
        all_records = []
        for blob in recent_blobs:
            try:
                blob_client = container_client.get_blob_client(blob.name)
                raw_text = blob_client.download_blob().readall().decode("utf-8-sig")
                all_records.extend(parse_azure_json(raw_text))
            except Exception as e:
                st.warning(f"Blob read error ({blob.name}): {e}")
        return pd.DataFrame(all_records)
    except Exception as e:
        st.error(f"Container error '{container_name}': {e}")
        return pd.DataFrame()

# ---- NO CACHE ANYWHERE — pure live fetch ----
def load_all_data():
    # "violations" container = [violatedcars] ASA output = plate_number, ticket_type, etc.
    df_violations = fetch_container_data("violations", max_blobs=10)

    # "output" container = [generalinfo] ASA output = window_start, total_vehicles, etc.
    df_summary = fetch_container_data("output", max_blobs=2)

    return df_violations, df_summary

# ==========================================
# UI
# ==========================================
st.title("🚦 Cairo Traffic Enforcement Command Center")

if st.button("🔄 Refresh Data"):
    st.rerun()

st.markdown("---")

df_violations, df_summary = load_all_data()

# ---- DEBUG EXPANDER (delete after confirming data is correct) ----
with st.expander("🛠 Debug: Raw Container Data", expanded=True):
    st.markdown("**Container: `violations` (should have plate_number, ticket_type)**")
    st.write(f"Rows: {len(df_violations)} | Columns: {list(df_violations.columns)}")
    if not df_violations.empty:
        st.dataframe(df_violations.head(3))

    st.markdown("**Container: `output` (should have window_start, total_vehicles)**")
    st.write(f"Rows: {len(df_summary)} | Columns: {list(df_summary.columns)}")
    if not df_summary.empty:
        st.dataframe(df_summary.head(3))

st.markdown("---")

# ---- SUMMARY METRICS ----
st.header("Real-Time Traffic Summary (Last 5 Mins)")
latest_summary = {}
if not df_summary.empty:
    if "window_end" in df_summary.columns:
        df_summary["window_end"] = pd.to_datetime(df_summary["window_end"])
        df_summary = df_summary.sort_values(by="window_end", ascending=False)
    latest_summary = df_summary.iloc[0].to_dict()

if latest_summary:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Location",         latest_summary.get("location", "Unknown"))
    col2.metric("Total Vehicles",   int(latest_summary.get("total_vehicles", 0)))
    col3.metric("Avg Speed (km/h)", round(float(latest_summary.get("avg_speed", 0)), 1))
    col4.metric("Total Violations", int(latest_summary.get("total_violation_count", 0)))
else:
    st.info("No summary data yet.")

st.markdown("---")

# ---- VIOLATION TABLE ----
st.header("Violation Analytics & Records")

if not df_violations.empty:
    if "timestamp" in df_violations.columns:
        df_violations["timestamp"] = pd.to_datetime(df_violations["timestamp"], errors="coerce")
    if "speed_kmh" in df_violations.columns:
        df_violations["speed_kmh"] = pd.to_numeric(df_violations["speed_kmh"], errors="coerce")

    # Filters
    st.markdown("#### 🔍 Filter Violations")
    fc1, fc2, fc3 = st.columns(3)

    with fc1:
        search_plate = st.text_input("Search Plate Number", placeholder="e.g. أ ب ت 1234")
    with fc2:
        vt_opts = df_violations["vehicle_type"].dropna().unique().tolist() if "vehicle_type" in df_violations.columns else []
        selected_vehicles = st.multiselect("Filter by Vehicle Type", vt_opts)
    with fc3:
        tt_opts = df_violations["ticket_type"].dropna().unique().tolist() if "ticket_type" in df_violations.columns else []
        selected_tickets = st.multiselect("Filter by Ticket Type", tt_opts)

    filtered = df_violations.copy()
    if search_plate and "plate_number" in filtered.columns:
        filtered = filtered[filtered["plate_number"].str.contains(search_plate, case=False, na=False)]
    if selected_vehicles and "vehicle_type" in filtered.columns:
        filtered = filtered[filtered["vehicle_type"].isin(selected_vehicles)]
    if selected_tickets and "ticket_type" in filtered.columns:
        filtered = filtered[filtered["ticket_type"].isin(selected_tickets)]

    if not filtered.empty:
        # Charts
        cc1, cc2 = st.columns(2)
        with cc1:
            if "ticket_type" in filtered.columns:
                st.plotly_chart(px.pie(filtered, names="ticket_type", title="Violations by Type", hole=0.4), use_container_width=True)
        with cc2:
            if "speed_kmh" in filtered.columns:
                st.plotly_chart(px.histogram(filtered, x="speed_kmh", title="Speed Distribution", nbins=20), use_container_width=True)

        # Table
        st.subheader(f"Violator Records ({len(filtered)} found)")
        display_cols = [
            "timestamp", "plate_number", "vehicle_type",
            "speed_kmh", "speed_limit", "ticket_type",
            "crossed_on_red", "yellow_light_violation",
            "speed_violation", "seatbelt_violation",
            "reckless_driving_anomaly", "lane",
            "traffic_light", "location"
        ]
        available_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(
            filtered[available_cols].sort_values(by="timestamp", ascending=False) if "timestamp" in filtered.columns else filtered[available_cols],
            use_container_width=True
        )
    else:
        st.warning("No records match your filter criteria.")
else:
    st.warning("No data found in 'violations' container.")
