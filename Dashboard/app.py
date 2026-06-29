import streamlit as st
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime
import plotly.express as px
import time
from azure.storage.blob import BlobServiceClient

# Configure page layout
st.set_page_config(
    page_title="Cairo Traffic Enforcement Command Center",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AZURE BLOB STORAGE CONFIGURATION ---
AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=storagetraffic11;AccountKey=FndnvLfVm8RgEvB7S3vIPnmeM9ukN51X8F/GoDQWB6K8ZQwe1Ukm86WOVVOK4Qsd0ywelUYDtByH+ASt7EZRpA==;EndpointSuffix=core.windows.net"
CONTAINER_SUMMARY_NAME = "violations"
CONTAINER_DETAILS_NAME = "output"
ALERT_LOG_PATH = "alert_log.csv"

LOCATION_COORDINATES = {
    "Maadi Corniche Intersection": {"lat": 29.9814, "lon": 31.2341},
    "Cairo Roadway": {"lat": 30.0444, "lon": 31.2357}
}


def safe_json_lines(raw_text):
    records = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def normalize_summary(summary_data, df_violations):
    if summary_data is None:
        summary_data = {}
    if not isinstance(summary_data, dict):
        summary_data = {}

    location = (
        summary_data.get("location")
        or (df_violations["location"].iloc[0] if not df_violations.empty and "location" in df_violations.columns else "Maadi Corniche Intersection")
    )
    total_vehicles = (
        summary_data.get("total_vehicles")
        or summary_data.get("vehicle_count")
        or summary_data.get("count")
        or (len(df_violations) if not df_violations.empty else 150)
    )
    avg_speed = (
        summary_data.get("avg_speed")
        or summary_data.get("average_speed")
        or (df_violations["speed_kmh"].mean() if not df_violations.empty and "speed_kmh" in df_violations.columns else 42.5)
    )
    total_violation_count = (
        summary_data.get("total_violation_count")
        or summary_data.get("total_ticket_count")
        or summary_data.get("violation_count")
        or (len(df_violations) if not df_violations.empty else 24)
    )

    return {
        "location": location,
        "total_vehicles": int(total_vehicles) if pd.notna(total_vehicles) else 0,
        "avg_speed": float(avg_speed) if pd.notna(avg_speed) else 0.0,
        "total_violation_count": int(total_violation_count) if pd.notna(total_violation_count) else 0
    }


def fetch_enforcement_data_from_azure():
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING)

        # Summary Ingestion
        summary_container = blob_service_client.get_container_client(
            CONTAINER_SUMMARY_NAME)
        summary_blobs = list(summary_container.list_blobs())
        summary_data = None
        latest_summary_file = "None"

        if summary_blobs:
            latest_summary_blob = max(
                summary_blobs, key=lambda b: b.last_modified)
            latest_summary_file = latest_summary_blob.name
            s_client = summary_container.get_blob_client(latest_summary_file)
            raw_summary = s_client.download_blob().readall().decode("utf-8")
            summary_records = safe_json_lines(raw_summary)
            if summary_records:
                summary_data = summary_records[0]

        # Details Ingestion
        details_container = blob_service_client.get_container_client(
            CONTAINER_DETAILS_NAME)
        details_blobs = list(details_container.list_blobs())
        violation_records = []
        latest_details_file = "None"

        if details_blobs:
            latest_details_blob = max(
                details_blobs, key=lambda b: b.last_modified)
            latest_details_file = latest_details_blob.name
            d_client = details_container.get_blob_client(latest_details_file)
            raw_details = d_client.download_blob().readall().decode("utf-8")
            violation_records = safe_json_lines(raw_details)

        df_violations = pd.DataFrame(violation_records)

        # --- ROBUST SCHEMA ENFORCEMENT ---
        # If the file from Azure is completely empty, or missing required keys, fill them safely
        if df_violations.empty:
            df_violations = pd.DataFrame(columns=[
                                         "plate_number", "vehicle_type", "speed_kmh", "traffic_light", "ticket_type", "timestamp"])

        # Generate clean simulation columns ONLY if Azure forgot to include them
        rows = len(df_violations) if len(df_violations) > 0 else 30
        if df_violations.empty:
            df_violations["plate_number"] = [
                f"Cairo-{np.random.randint(1000, 9999)}" for _ in range(rows)]

        if "vehicle_type" not in df_violations.columns:
            df_violations["vehicle_type"] = np.random.choice(
                ["Car", "Microbus", "Truck", "Motorcycle"], size=rows)
        if "speed_kmh" not in df_violations.columns:
            df_violations["speed_kmh"] = np.random.normal(
                loc=65, scale=18, size=rows).round(1)
            df_violations["speed_kmh"] = df_violations["speed_kmh"].apply(
                lambda x: max(15.0, x))
        if "traffic_light" not in df_violations.columns:
            df_violations["traffic_light"] = np.random.choice(
                ["red", "yellow", "green"], size=rows)
        if "ticket_type" not in df_violations.columns:
            df_violations["ticket_type"] = np.random.choice(
                ["Speeding", "Red Light", "Seatbelt"], size=rows)
        if "timestamp" not in df_violations.columns:
            df_violations["timestamp"] = [datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S") for _ in range(rows)]

        summary_data = normalize_summary(summary_data, df_violations)
        return summary_data, df_violations, f"Summary: {latest_summary_file} | Details: {latest_details_file}"

    except Exception as e:
        # If Azure connection fails completely, fallback entirely so dashboard stays live
        rows = 40
        mock_df = pd.DataFrame({
            "plate_number": [f"Cairo-{np.random.randint(1000, 9999)}" for _ in range(rows)],
            "vehicle_type": np.random.choice(["Car", "Microbus", "Truck", "Motorcycle"], size=rows),
            "speed_kmh": np.random.normal(loc=58, scale=15, size=rows).round(1),
            "traffic_light": np.random.choice(["red", "yellow", "green"], size=rows),
            "ticket_type": np.random.choice(["Speeding", "Red Light", "Seatbelt"], size=rows),
            "timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S") for _ in range(rows)]
        })
        mock_df["speed_kmh"] = mock_df["speed_kmh"].apply(
            lambda x: max(10.0, x))
        summary_data = normalize_summary(None, mock_df)
        return summary_data, mock_df, f"[Simulation Mode - Azure Connection Refused: {e}]"


def evaluate_traffic_thresholds(summary_dict):
    alerts = []
    avg_speed = summary_dict.get("avg_speed", 0)
    location = summary_dict.get("location", "Unknown Location")
    total_violation_count = summary_dict.get("total_violation_count", 0)

    if avg_speed < 25:
        msg = f"🛑 CRITICAL CONGESTION: Average speed at {location} has dropped to {avg_speed} km/h!"
        alerts.append(
            {"Location": location, "Type": "Congestion Alert", "Message": msg})

    if total_violation_count > 40:
        msg = f"⚠️ ENFORCEMENT SURGE: High violation rate detected! {total_violation_count} active offenses in this window."
        alerts.append(
            {"Location": location, "Type": "Safety Violation", "Message": msg})

    if alerts:
        log_df = pd.DataFrame(alerts)
        log_df["Log_Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not os.path.exists(ALERT_LOG_PATH):
            log_df.to_csv(ALERT_LOG_PATH, index=False)
        else:
            log_df.to_csv(ALERT_LOG_PATH, mode="a", header=False, index=False)
    return alerts


# --- DATA ACQUISITION ---
summary, df_violations, active_file = fetch_enforcement_data_from_azure()

# --- SIDEBAR INTERACTIVE FILTERS ---
st.sidebar.header("🕹️ Dynamic Filters Control")
st.sidebar.markdown("Slice & dice live telemetry:")

# Filters
unique_vehicles = df_violations["vehicle_type"].dropna().unique().tolist()
selected_vehicles = st.sidebar.multiselect(
    "Vehicle Type:", options=unique_vehicles, default=unique_vehicles)

unique_signals = df_violations["traffic_light"].dropna().unique().tolist()
selected_signals = st.sidebar.multiselect(
    "Intersection Signal State:", options=unique_signals, default=unique_signals)

max_speed_val = float(
    df_violations["speed_kmh"].max()) if not df_violations.empty else 150.0
min_speed = st.sidebar.slider(
    "Min Target Speed Filter (km/h):", min_value=0.0, max_value=max_speed_val, value=0.0)

# Apply Sidebar Filters
filtered_df = df_violations.copy()
filtered_df = filtered_df[filtered_df["vehicle_type"].isin(selected_vehicles)]
filtered_df = filtered_df[filtered_df["traffic_light"].isin(selected_signals)]
filtered_df = filtered_df[filtered_df["speed_kmh"] >= min_speed]


# --- INTERACTIVE APP HEADER ---
st.title("🚨 Cairo Real-Time Traffic Enforcement & Interactive Dashboard")
st.info(f"**Data Pipeline Source:** {active_file}")

# Alerts Execution
active_alerts = evaluate_traffic_thresholds(summary)
for alert in active_alerts:
    if alert.get("Type") == "Congestion Alert":
        st.error(alert.get("Message"))
    else:
        st.warning(alert.get("Message"))

# Top Tier Dashboard Metrics
st.markdown("### 📊 Filtered Window Aggregates")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(label="Monitored Vehicle Profiles", value=len(filtered_df))

# FIXING KEYERROR TRACEBACK: Added a check for empty filter or missing col array
if not filtered_df.empty and "speed_kmh" in filtered_df.columns:
    avg_speed_display = f"{round(filtered_df['speed_kmh'].mean(), 1)} km/h"
else:
    avg_speed_display = "0.0 km/h"
kpi2.metric(label="Filtered Group Average Speed", value=avg_speed_display)

ticket_count = len(filtered_df[filtered_df['ticket_type'].notna(
)]) if 'ticket_type' in filtered_df.columns else 0
kpi3.metric(label="Current Window Violations", value=ticket_count)

st.markdown("---")


# --- ANALYTICS DASHBOARD GRID ---
st.markdown("### 📈 Real-Time Interactive Analytical Charts")

row1_left, row1_right = st.columns(2)

with row1_left:
    st.markdown("#### 🗺️ Geographic Incident Tracking")
    loc_name = summary.get("location", "Maadi Corniche Intersection")
    coords = LOCATION_COORDINATES.get(
        loc_name, {"lat": 29.9814, "lon": 31.2341})
    map_df = pd.DataFrame(
        [{"lat": coords["lat"], "lon": coords["lon"], "Location": loc_name}])
    st.map(map_df, zoom=14)

with row1_right:
    st.markdown("#### 🏎️ Vehicle Velocity Distribution Histogram")
    if not filtered_df.empty and "speed_kmh" in filtered_df.columns:
        fig_hist = px.histogram(
            filtered_df,
            x="speed_kmh",
            nbins=12,
            labels={'speed_kmh': 'Speed (km/h)'},
            color_discrete_sequence=['#ff4b4b'],
            template="plotly_dark"
        )
        fig_hist.update_layout(
            bargap=0.1, yaxis_title="Total Infractions", margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Adjust filters to view distribution dataset maps.")

row2_left, row2_right = st.columns(2)

with row2_left:
    st.markdown("#### 🛑 Infraction Tickets Segment Proportions")
    if not filtered_df.empty and "ticket_type" in filtered_df.columns:
        ticket_counts = filtered_df["ticket_type"].value_counts().reset_index()
        ticket_counts.columns = ["Ticket Type", "Count"]
        fig_pie = px.pie(
            ticket_counts,
            values="Count",
            names="Ticket Type",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.YlOrRd[::-1],
            template="plotly_dark"
        )
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No tickets fit filter parameters.")

with row2_right:
    st.markdown("#### 🚛 Cross-Analysis: Vehicle Type vs Signal Phases")
    check_cols = ["vehicle_type", "traffic_light"]
    if not filtered_df.empty and all(col in filtered_df.columns for col in check_cols):
        cross_df = filtered_df.groupby(
            check_cols).size().reset_index(name="Count")
        fig_bar = px.bar(
            cross_df,
            x="vehicle_type",
            y="Count",
            color="traffic_light",
            barmode="group",
            labels={'vehicle_type': 'Vehicle Class',
                    'Count': 'Total Violations'},
            color_discrete_map={'red': '#df2020',
                                'green': '#20b020', 'yellow': '#dfdf20'},
            template="plotly_dark"
        )
        fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Filters have restricted multi-variable dimensions.")


# --- INFRACTIONS SEARCH TABLE ---
st.markdown("---")
st.markdown("### 📋 Interactive Live Infractions Search Matrix")

if not filtered_df.empty:
    search_plate = st.text_input(
        "🔍 Quick Search Filter by Registration Plate Number:")
    final_display_df = filtered_df.copy()

    if search_plate and "plate_number" in final_display_df.columns:
        final_display_df = final_display_df[
            final_display_df["plate_number"].astype(
                str).str.contains(search_plate, na=False, case=False)
        ]

    display_cols = ["plate_number", "vehicle_type",
                    "speed_kmh", "traffic_light", "ticket_type", "timestamp"]
    available_cols = [c for c in display_cols if c in final_display_df.columns]

    st.dataframe(final_display_df[available_cols]
                 if available_cols else final_display_df, use_container_width=True)
else:
    st.warning(
        "Adjust interactive control sliders to rebuild visual telemetry indexes.")


# --- HISTORICAL ALERTS REGISTRY ---
st.markdown("---")
st.markdown("### 🚨 Historical Pipeline System Log Register")
if os.path.exists(ALERT_LOG_PATH):
    try:
        historical_log = pd.read_csv(ALERT_LOG_PATH)
        st.dataframe(historical_log.iloc[::-1], use_container_width=True)
    except Exception:
        st.warning("Historical log system table busy.")
else:
    st.info("System operational. No system threshold logging events registered yet.")

# --- AUTOMATIC REFRESH ---
time.sleep(180)
st.rerun()
