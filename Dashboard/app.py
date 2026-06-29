import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import time
from azure.storage.blob import BlobServiceClient

# Configure the page layout
st.set_page_config(
    page_title="Cairo Traffic Enforcement Dashboard", layout="wide")
st.title("🚨 Cairo Real-Time Traffic Enforcement & Violation Pipeline")
st.write("Streaming analytics pulling 5-minute enforcement snapshots directly from Azure Cloud.")

# --- MULTI-CONTAINER CLOUD CONFIGURATION ---
AZURE_CONNECTION_STRING = "Endpoint=sb://trafficstreaming.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=HOwKuasfB324ZNIBffi4OVcgb2ae4gv/h+AEhKOwtis="
CONTAINER_SUMMARY_NAME = "generalinfo"
CONTAINER_DETAILS_NAME = "violatedcars"
ALERT_LOG_PATH = "alert_log.csv"

# Static coordinate mapping for Egyptian intersections to keep the map functional
LOCATION_COORDINATES = {
    "Maadi Corniche Intersection": {"lat": 29.9814, "lon": 31.2341}
}

# --- 1. MULTI-CONTAINER CLOUD INGESTION ENGINE ---


def fetch_enforcement_data_from_azure():
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_CONNECTION_STRING)

        # Layer A: Extract Window Summary Aggregate
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
            raw_summary = s_client.download_blob().readall().decode('utf-8')
            # Extract first valid structural line
            for line in raw_summary.splitlines():
                if line.strip():
                    summary_data = json.loads(line.strip())
                    break

        # Layer B: Extract Granular Infractions Log Stream
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
            raw_details = d_client.download_blob().readall().decode('utf-8')

            for line in raw_details.splitlines():
                if line.strip():
                    violation_records.append(json.loads(line.strip()))

        df_violations = pd.DataFrame(violation_records)

        # Robust Fallback: If Summary container pipeline hasn't caught up, calculate metrics on the fly
        if summary_data is None and not df_violations.empty:
            summary_data = {
                "location": df_violations["location"].iloc[0] if "location" in df_violations.columns else "Cairo Roadway",
                "total_vehicles": len(df_violations),
                "avg_speed": df_violations["speed_kmh"].mean() if "speed_kmh" in df_violations.columns else 60.0,
                "total_violation_count": len(df_violations)
            }

        status_tracking_message = f"Summary File: {latest_summary_file} | Details File: {latest_details_file}"
        return summary_data, df_violations, status_tracking_message

    except Exception as e:
        st.error(
            f"Error streaming from multi-container Azure Architecture: {e}")
        return None, None, None
# --- 2. LOGICAL ENFORCEMENT THRESHOLD ENGINE ---


def evaluate_traffic_thresholds(summary_dict):
    alerts = []

    # Threshold Condition 1: Check for critical slow downs / massive congestion bottlenecks
    if summary_dict["avg_speed"] < 25:
        msg = f"🛑 CRITICAL CONGESTION: Average speed at {summary_dict['location']} has dropped to {summary_dict['avg_speed']} km/h!"
        alerts.append(
            {"Location": summary_dict["location"], "Type": "Congestion Alert", "Message": msg})

    # Threshold Condition 2: Check for massive reckless driving rates
    if summary_dict["total_violation_count"] > 40:
        msg = f"⚠️ ENFORCEMENT SURGE: High violation rate detected! {summary_dict['total_violation_count']} active offenses in this window."
        alerts.append(
            {"Location": summary_dict["location"], "Type": "Safety Violation", "Message": msg})

    # Write discoveries cleanly to local text-based logs
    if alerts:
        log_df = pd.DataFrame(alerts)
        log_df['Log_Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not os.path.exists(ALERT_LOG_PATH):
            log_df.to_csv(ALERT_LOG_PATH, index=False)
        else:
            log_df.to_csv(ALERT_LOG_PATH, mode='a', header=False, index=False)

    return alerts


# --- 3. RENDERING & UI CONTROL LAYER ---
summary, df_violations, active_file = fetch_enforcement_data_from_azure()

if summary is None:
    st.warning(
        "Awaiting cloud streaming pipeline synchronization... Checking Azure container.")
else:
    st.info(
        f"Analyzing cloud deployment snapshot pipeline drop: {active_file}")

    # Process and fire notifications
    active_alerts = evaluate_traffic_thresholds(summary)
    for alert in active_alerts:
        if alert["Type"] == "Congestion Alert":
            st.error(alert["Message"])
        else:
            st.warning(alert["Message"])

    # Draw KPI cards using the summary object data directly
    st.markdown("### 📊 Current 5-Minute Window Metrics")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="Monitored Vehicle Volume",
                value=int(summary["total_vehicles"]))
    kpi2.metric(label="Average Flow Speed",
                value=f"{round(summary['avg_speed'], 1)} km/h")
    kpi3.metric(label="Logged Traffic Violations",
                value=int(summary["total_violation_count"]))

    # Visual Layout Split
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("### 🗺️ Geographic Incident Tracking")
        # Build geocoded frame for map plotting
        loc_name = summary["location"]
        coords = LOCATION_COORDINATES.get(
            loc_name, {"lat": 30.0444, "lon": 31.2357})
        map_df = pd.DataFrame(
            [{"lat": coords["lat"], "lon": coords["lon"], "Location": loc_name}])
        st.map(map_df, zoom=13)

    with right_col:
        st.markdown("### 🛑 Violation Types Breakdown")
        if not df_violations.empty and "ticket_type" in df_violations.columns:
            ticket_counts = df_violations["ticket_type"].value_counts(
            ).reset_index()
            ticket_counts.columns = ["Ticket Type", "Count"]
            fig_pie = px.pie(ticket_counts, values="Count", names="Ticket Type", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)

    # Detailed vehicle logs section
    st.markdown("### 📋 Live Infractions Log Stream")
    if not df_violations.empty:
        # Reordering column highlights for user scanning
        display_cols = ["plate_number", "vehicle_type",
                        "speed_kmh", "traffic_light", "ticket_type", "timestamp"]
        available_cols = [
            c for c in display_cols if c in df_violations.columns]

        # Add search input filter field for local security checks
        search_plate = st.text_input(
            "🔍 Search database by license plate letters/numbers:")
        filtered_df = df_violations
        if search_plate:
            filtered_df = df_violations[df_violations["plate_number"].str.contains(
                search_plate, na=False)]

        st.dataframe(filtered_df[available_cols], use_container_width=True)

# --- 4. DISPLAY THE AUDIT TRAIL LOG ---
st.markdown("---")
st.markdown("### 🚨 Historical Pipeline System Alert Log")
if os.path.exists(ALERT_LOG_PATH):
    historical_log = pd.read_csv(ALERT_LOG_PATH)
    st.dataframe(historical_log.iloc[::-1], use_container_width=True)
else:
    st.info("System operational. No critical validation limits broken yet.")

# Pipeline cycle sleep: checks your container for new file outputs every 15 seconds
time.sleep(180)
st.rerun()
