# -----------------------------
# 🚍 SMART PUBLIC TRANSPORT ANALYTICS DASHBOARD
# Works in both: Local (Live DB) and Streamlit Cloud (Demo Mode)
# -----------------------------

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np
import folium
from streamlit_folium import st_folium
import io
from streamlit_autorefresh import st_autorefresh

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Smart Transport Dashboard", layout="wide")
st.title("🚍 Smart Public Transport Analytics Dashboard")

# Auto-refresh every 15 seconds (useful for local live data)
st_autorefresh(interval=15000, limit=None, key="refresh")

# -----------------------------
# DATABASE CONNECTION (SAFE)
# -----------------------------
def get_connection():
    try:
        conn = psycopg2.connect(
            dbname="transport",
            user="postgres",
            password="postgres",  # change this if your local DB uses another password
            host="localhost",
            port="5432"
        )
        st.success("✅ Connected to local PostgreSQL database")
        return conn
    except Exception:
        st.warning("⚠️ No local database detected — running in Demo Mode")
        return None

conn = get_connection()

# -----------------------------
# LOAD DATA (With DEMO fallback)
# -----------------------------
if conn:
    try:
        df_delay = pd.read_sql("SELECT * FROM transit.mv_trip_punctuality", conn)
        df_load = pd.read_sql("SELECT * FROM transit.v_route_load_factor", conn)
        df_gps = pd.read_sql("SELECT * FROM transit.gps_pings ORDER BY ts DESC LIMIT 10", conn)
        conn.close()
    except Exception:
        st.warning("⚠️ Could not fetch from DB — using Demo Data instead")
        conn = None

if not conn:
    # --- DEMO CSV DATA ---
    csv_delay = """trip_id,avg_delay_min
T1,4
T2,6
T3,3
T4,8
"""
    csv_load = """route_name,load_factor_est
Route 1,0.82
Route 2,0.67
Route 3,0.90
Route 4,0.75
"""
    csv_gps = """trip_id,vehicle_id,ts,lat,lon,speed_kmph
T1,V101,2025-11-07 10:00:00,17.39,78.49,42
T2,V102,2025-11-07 10:05:00,17.41,78.51,36
T3,V103,2025-11-07 10:10:00,17.37,78.47,29
T4,V104,2025-11-07 10:15:00,17.43,78.52,31
"""
    df_delay = pd.read_csv(io.StringIO(csv_delay))
    df_load = pd.read_csv(io.StringIO(csv_load))
    df_gps = pd.read_csv(io.StringIO(csv_gps))

# -----------------------------
# KPI SECTION
# -----------------------------
st.subheader("📊 Key Performance Indicators (KPIs)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("⏱️ Avg Delay (min)", round(df_delay["avg_delay_min"].mean(), 2))
col2.metric("🚦 Max Delay (min)", round(df_delay["avg_delay_min"].max(), 2))
col3.metric("🧍 Avg Load Factor", f"{round(df_load['load_factor_est'].mean() * 100, 1)}%")
on_time = len(df_delay[df_delay["avg_delay_min"] <= 5]) / len(df_delay) * 100
col4.metric("✅ On-Time %", f"{round(on_time, 1)}%")

# -----------------------------
# CHARTS SECTION
# -----------------------------
st.subheader("🕒 Average Delay per Trip")
fig_delay = px.bar(df_delay, x="trip_id", y="avg_delay_min", color="trip_id",
                   title="Average Delay per Trip (minutes)")
st.plotly_chart(fig_delay, use_container_width=True, key="delay_chart")

st.subheader("👥 Load Factor per Route")
fig_load = px.bar(df_load, x="route_name", y="load_factor_est", color="route_name",
                  title="Estimated Load Factor per Route")
st.plotly_chart(fig_load, use_container_width=True, key="load_chart")

# -----------------------------
# PREDICTIVE ANALYTICS SECTION
# -----------------------------
st.subheader("🔮 Predict Future Delays (Simple Regression Example)")

df_delay["stop_sequence"] = np.arange(1, len(df_delay) + 1)
model = LinearRegression()
model.fit(df_delay[["stop_sequence"]], df_delay["avg_delay_min"])
future_seq = np.arange(1, len(df_delay) + 6).reshape(-1, 1)
predictions = model.predict(future_seq)

pred_df = pd.DataFrame({"stop_sequence": future_seq.flatten(), "predicted_delay": predictions})
fig_predict = px.line(pred_df, x="stop_sequence", y="predicted_delay",
                      title="Predicted Delay for Future Trips")
st.plotly_chart(fig_predict, use_container_width=True, key="predict_chart")

# -----------------------------
# LIVE MAP SECTION
# -----------------------------
st.subheader("🗺️ Vehicle Tracker Map")

m = folium.Map(location=[17.40, 78.49], zoom_start=12)
for _, row in df_gps.iterrows():
    folium.Marker(
        [row["lat"], row["lon"]],
        popup=f"Trip: {row['trip_id']} | Speed: {row['speed_kmph']} km/h"
    ).add_to(m)
st_folium(m, width=700, height=500)

st.success("✅ Dashboard loaded successfully!")






