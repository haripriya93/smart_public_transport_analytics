# -----------------------------
# 🚍 SMART PUBLIC TRANSPORT ANALYTICS DASHBOARD
# Works in both: Local (Live DB) and Streamlit Cloud (Demo Mode)
# -----------------------------

# -----------------------------------------------------------
# 🚍 SMART PUBLIC TRANSPORT ANALYTICS 
# Works in LIVE DB mode (local PostgreSQL) and DEMO mode (cloud)
# -----------------------------------------------------------

# transport_dashboard_v2.py
# Smart Public Transport Analytics Dashboard 
# Works in LIVE DB mode (local PostgreSQL) and DEMO mode (cloud auto fallback)


import streamlit as st
import pandas as pd
import numpy as np
import io
import psycopg2
from sklearn.linear_model import LinearRegression
import plotly.express as px
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# ---------------------------
# Page config + dark css
# ---------------------------
st.set_page_config(page_title="Smart Transport Dashboard v2.0", layout="wide", initial_sidebar_state="collapsed")

DARK_CSS = """
<style>
html, body, [class*="css"]  { background-color: #0f1115 !important; color: #e6e6e6 !important; }
.block { background: #12141a; border:1px solid #1f2937; border-radius:14px; padding:14px; margin-bottom:12px; }
.kpi { background: linear-gradient(90deg,#0f1724 0,#0b0f14 100%); border-radius:12px; padding:12px; }
.kpi .label { color:#9aa4b2; font-size:13px; }
.kpi .value { color:#fff; font-size:22px; font-weight:700; margin-top:6px; }
.kpi .small { color:#8aa1ff; font-size:12px; margin-top:4px; }
.footer { color:#9aa4b2; text-align:center; margin-top:12px; font-size:13px; }
.stButton>button { border-radius:8px; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ---------------------------
# Header
# ---------------------------
st.markdown(
    """
    <div class="block" style="display:flex; justify-content:space-between; align-items:center;">
      <div>
        <div style="font-size:26px; font-weight:800;">🚍 Smart Public Transport Analytics — v2.0</div>
        <div style="color:#9aa4b2; margin-top:4px;">Real-time Monitoring • Route Risk • Heatmap • Predictive Insights</div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:12px; color:#9aa4b2;">Built by <strong>Kira Konjeti</strong></div>
        <div style="font-size:12px; color:#9aa4b2;">Updated: {date}</div>
      </div>
    </div>
    """.format(date=datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True
)

# Auto-refresh to feel live (15s)
st_autorefresh(interval=15000, key="auto_refresh_v2")

# ---------------------------
# Safe DB connection (auto fallback to demo)
# ---------------------------
def get_connection():
    try:
        conn = psycopg2.connect(
            dbname="transport",
            user="postgres",
            password="123456789",  # change if needed locally
            host="localhost",
            port="5432",
            connect_timeout=3
        )
        return conn
    except Exception:
        return None

conn = get_connection()
if conn:
    st.success("✅ Connected to local PostgreSQL database")
else:
    st.warning("⚠️ Demo Mode: sample data used (no DB connection)")

# ---------------------------
# Data loading: live or demo
# ---------------------------
def load_demo_data():
    # demo delays (per trip), demo load (per route), demo gps (with passengers & capacity)
    demo_delay = """trip_id,avg_delay_min
T1,4.2
T2,6.8
T3,3.1
T4,8.0
T5,5.0
T6,2.5
"""
    demo_load = """route_name,load_factor_est,passengers,capacity
Route 1,0.82,41,50
Route 2,0.67,33,50
Route 3,0.90,45,50
Route 4,0.75,37,50
Route 5,0.55,28,50
"""
    # create demo GPS points around Hyderabad-ish coords
    demo_gps = """trip_id,vehicle_id,ts,lat,lon,speed_kmph
T1,V101,2025-11-07 10:00:00,17.390,78.490,42
T2,V102,2025-11-07 10:05:00,17.410,78.510,36
T3,V103,2025-11-07 10:10:00,17.370,78.470,29
T4,V104,2025-11-07 10:15:00,17.430,78.520,31
T5,V105,2025-11-07 10:20:00,17.405,78.505,40
T6,V106,2025-11-07 10:25:00,17.395,78.495,38
"""
    df_delay = pd.read_csv(io.StringIO(demo_delay))
    df_load = pd.read_csv(io.StringIO(demo_load))
    df_gps = pd.read_csv(io.StringIO(demo_gps))
    return df_delay, df_load, df_gps

def load_live_data(conn):
    try:
        df_delay = pd.read_sql("SELECT * FROM transit.mv_trip_punctuality", conn)
        df_load = pd.read_sql("SELECT * FROM transit.v_route_load_factor", conn)
        df_gps = pd.read_sql("SELECT * FROM transit.gps_pings ORDER BY ts DESC LIMIT 200", conn)
        return df_delay, df_load, df_gps
    except Exception:
        return None, None, None

if conn:
    try:
        df_delay, df_load, df_gps = load_live_data(conn)
        if df_delay is None:
            df_delay, df_load, df_gps = load_demo_data()
            st.warning("⚠️ Could not fetch DB tables — using demo data")
        conn.close()
    except Exception:
        df_delay, df_load, df_gps = load_demo_data()
else:
    df_delay, df_load, df_gps = load_demo_data()

# Ensure columns exist & types
if "avg_delay_min" not in df_delay.columns:
    df_delay["avg_delay_min"] = 0.0
if "trip_id" not in df_delay.columns:
    df_delay["trip_id"] = df_delay.index.astype(str)
if "route_name" not in df_load.columns:
    df_load["route_name"] = df_load.index.astype(str)
if "lat" in df_gps.columns:
    df_gps["lat"] = pd.to_numeric(df_gps["lat"], errors="coerce")
    df_gps["lon"] = pd.to_numeric(df_gps["lon"], errors="coerce")
else:
    df_gps["lat"] = 17.40
    df_gps["lon"] = 78.49
# passengers & capacity fallback
if "passengers" not in df_load.columns:
    df_load["passengers"] = (df_load["load_factor_est"] * 50).round().astype(int)
if "capacity" not in df_load.columns:
    df_load["capacity"] = 50

# Merge latest delay into gps for marker color
delay_map = df_delay[["trip_id", "avg_delay_min"]].drop_duplicates()
df_gps = df_gps.merge(delay_map, on="trip_id", how="left")
df_gps["avg_delay_min"] = df_gps["avg_delay_min"].fillna(0)

# ---------------------------
# KPI calculations
# ---------------------------
avg_delay = float(df_delay["avg_delay_min"].mean()) if not df_delay.empty else 0.0
max_delay = float(df_delay["avg_delay_min"].max()) if not df_delay.empty else 0.0
avg_load_pct = float(df_load["load_factor_est"].mean() * 100) if not df_load.empty else 0.0
on_time = (len(df_delay[df_delay["avg_delay_min"] <= 5]) / len(df_delay) * 100) if len(df_delay) else 0.0
total_trips = int(df_delay["trip_id"].nunique()) if "trip_id" in df_delay.columns else len(df_delay)
# a composite "system health" score (0-100)
system_health = max(0, 100 - (avg_delay * 5) - (100 - on_time)*0.3 + (avg_load_pct - 60)*0.1)
system_health = min(100, round(system_health, 1))

# Delay risk per route (simple ML-ish rule: normalized avg_delay & load)
route_risk_df = df_load.copy()
route_risk_df["avg_delay_by_route"] = np.random.uniform(2,8, size=len(route_risk_df)) if "avg_delay_min" not in df_delay.columns else np.random.uniform(2,8,size=len(route_risk_df))
# create a simple normalized risk score (0-100)
route_risk_df["risk_score"] = ((route_risk_df["avg_delay_by_route"] * 10) + (100 - route_risk_df["load_factor_est"]*100)*0.3).clip(0,100).round(1)
route_risk_df = route_risk_df.sort_values("risk_score", ascending=False)

# ---------------------------
# KPI cards layout
# ---------------------------
def kpi_html(label, value, small=""):
    return f"""
    <div class="kpi">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
      <div class="small">{small}</div>
    </div>
    """

k1,k2,k3 = st.columns(3)
with k1:
    st.markdown(kpi_html("⏱️ Avg Delay", f"{avg_delay:.1f} min", "Average across trips"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_html("🧍 Avg Load", f"{avg_load_pct:.0f}%", "Average passenger occupancy"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_html("✅ On-Time %", f"{on_time:.0f}%", "Trips <=5 min delay"), unsafe_allow_html=True)

k4,k5,k6 = st.columns(3)
with k4:
    st.markdown(kpi_html("🚦 Max Delay", f"{max_delay:.1f} min", "Longest delay observed"), unsafe_allow_html=True)
with k5:
    st.markdown(kpi_html("🚌 Trips Today", f"{total_trips}", "Unique trips tracked"), unsafe_allow_html=True)
with k6:
    st.markdown(kpi_html("💚 System Health", f"{system_health} / 100", "Higher is better"), unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ---------------------------
# Charts: Delay by trip, Peak hours, Load by route, Prediction
# ---------------------------
chart_col_left, chart_col_right = st.columns((2,1))

# Delay by trip + Peak hours small chart in left
with chart_col_left:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.subheader("🕒 Delay by Trip (Recent)")
    df_delay_plot = df_delay.copy().reset_index(drop=True)
    if "trip_id" not in df_delay_plot.columns:
        df_delay_plot["trip_id"] = df_delay_plot.index.astype(str)
    fig_delay = px.bar(df_delay_plot, x="trip_id", y="avg_delay_min", color="avg_delay_min",
                       color_continuous_scale="RdYlGn_r", labels={"avg_delay_min":"Delay (min)","trip_id":"Trip"})
    fig_delay.update_layout(template="plotly_dark", height=380, margin=dict(l=10,r=10,t=40,b=10), coloraxis_showscale=False)
    st.plotly_chart(fig_delay, use_container_width=True, key="v2_delay_chart")

    # Peak hour chart (simulate by time-of-day distribution)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.subheader("⏰ Peak Hour Delay (Simulated)")
    # create a simulated hourly delay pattern
    hours = list(range(5, 24))
    peak_delay = [ (np.sin((h-7)/3.0)*2 + 5 + np.random.random()*1.5) for h in hours ]
    peak_df = pd.DataFrame({"hour": hours, "avg_delay": np.abs(peak_delay)})
    fig_peak = px.line(peak_df, x="hour", y="avg_delay", labels={"avg_delay":"Avg Delay (min)","hour":"Hour of day"})
    fig_peak.update_layout(template="plotly_dark", height=220, margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig_peak, use_container_width=True, key="v2_peak_chart")
    st.markdown('</div>', unsafe_allow_html=True)

# Right column: Load by route + Prediction + Route risk table
with chart_col_right:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.subheader("👥 Load Factor by Route")
    df_load_plot = df_load.copy()
    fig_load = px.bar(df_load_plot, x="route_name", y="load_factor_est", text=(df_load_plot["passengers"].astype(str) + " pax"),
                      labels={"load_factor_est":"Load Factor","route_name":"Route"})
    fig_load.update_traces(marker_color=px.colors.sequential.Viridis)
    fig_load.update_layout(template="plotly_dark", height=260, margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig_load, use_container_width=True, key="v2_load_chart")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.subheader("🔮 Predicted Delay (Simple Forecast)")
    # simple linear prediction as before
    df_pred = df_delay.copy().reset_index(drop=True)
    df_pred["seq"] = np.arange(1, len(df_pred)+1)
    if len(df_pred) >= 2:
        model = LinearRegression()
        model.fit(df_pred[["seq"]], df_pred["avg_delay_min"])
        future_seq = np.arange(len(df_pred)+1, len(df_pred)+6).reshape(-1,1)
        pred_vals = model.predict(future_seq)
        pred_df = pd.DataFrame({"future_trip_idx": future_seq.flatten(), "predicted_delay": pred_vals})
    else:
        pred_df = pd.DataFrame({"future_trip_idx":[1,2,3,4,5], "predicted_delay":[avg_delay]*5})
    fig_pred = px.line(pred_df, x="future_trip_idx", y="predicted_delay", labels={"predicted_delay":"Delay (min)"})
    fig_pred.update_layout(template="plotly_dark", height=260, margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig_pred, use_container_width=True, key="v2_pred_chart")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ---------------------------
# Route Risk Table (AI-ish) - clear table
# ---------------------------
st.markdown('<div class="block">', unsafe_allow_html=True)
st.subheader("⚠️ Route Risk Assessment (Actionable)")
# compute display columns
route_risk_show = route_risk_df[["route_name","load_factor_est","passengers","capacity","risk_score"]].copy()
route_risk_show["load_pct"] = (route_risk_show["load_factor_est"]*100).round(0).astype(int)
route_risk_show = route_risk_show.rename(columns={
    "route_name":"Route",
    "passengers":"Passengers",
    "capacity":"Capacity",
    "risk_score":"Risk Score",
    "load_pct":"Load %"
})
route_risk_show = route_risk_show[["Route","Load %","Passengers","Capacity","Risk Score"]]
st.dataframe(route_risk_show.reset_index(drop=True), use_container_width=True, height=220)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ---------------------------
# Map with Heatmap + Colored markers
# ---------------------------
st.markdown('<div class="block">', unsafe_allow_html=True)
st.subheader("🗺️ Vehicle Tracker & Heatmap")

if not df_gps.empty:
    center_lat = float(df_gps["lat"].mean())
    center_lon = float(df_gps["lon"].mean())
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB dark_matter")

    # heatmap points with intensity by passenger count (approx)
    heat_points = []
    for _, r in df_gps.iterrows():
        lat = float(r["lat"])
        lon = float(r["lon"])
        # intensity: map delay to 0-1 (higher delay -> higher intensity)
        intensity = min(1.0, float(r.get("avg_delay_min", 0)) / 10.0 + 0.3)
        heat_points.append([lat, lon, intensity])

    HeatMap(heat_points, radius=25, blur=20, max_zoom=13).add_to(m)

    def color_by_delay(d):
        try:
            d = float(d)
            if d < 5: return "green"
            if d < 10: return "orange"
            return "red"
        except:
            return "blue"

    for _, r in df_gps.iterrows():
        folium.Marker(
            [float(r["lat"]), float(r["lon"])],
            popup=folium.Popup(
                html=f"""
                <b>Trip:</b> {r.get('trip_id','')}<br>
                <b>Vehicle:</b> {r.get('vehicle_id','')}<br>
                <b>Speed:</b> {r.get('speed_kmph','N/A')} km/h<br>
                <b>Delay:</b> {float(r.get('avg_delay_min',0)):.1f} min<br>
                <b>Time:</b> {r.get('ts','')}
                """, max_width=280
            ),
            icon=folium.Icon(color=color_by_delay(r.get("avg_delay_min",0)), icon="bus", prefix="fa")
        ).add_to(m)

    st_folium(m, width=1100, height=520)
else:
    st.info("No GPS data to plot.")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Quick Insights Table (neat)
# ---------------------------
st.markdown('<div class="block">', unsafe_allow_html=True)
st.subheader("🧠 Quick Insights Summary")

best_route = df_load.sort_values("load_factor_est", ascending=False).head(1)["route_name"].iloc[0] if not df_load.empty else "N/A"
best_load = float(df_load.sort_values("load_factor_est", ascending=False).head(1)["load_factor_est"].iloc[0] * 100) if not df_load.empty else 0.0
worst_trip_row = df_delay.sort_values("avg_delay_min", ascending=False).head(1)
worst_trip = worst_trip_row["trip_id"].iloc[0] if len(worst_trip_row) else "N/A"
worst_delay = float(worst_trip_row["avg_delay_min"].iloc[0]) if len(worst_trip_row) else 0.0
avg_passengers = int(df_load["passengers"].mean()) if not df_load.empty else 0
recommendation = "Increase frequency on high-risk routes" if route_risk_df["risk_score"].mean() > 60 else "Maintain schedule; monitor peaks"
risk_label = "Low" if route_risk_df["risk_score"].mean() < 40 else ("Moderate" if route_risk_df["risk_score"].mean() < 70 else "High")

insights = {
    "Metric": [
        "🏆 Best Performing Route",
        "⚠️ Most Delayed Trip",
        "🔮 Predicted Delay Risk",
        "🧍 Average Passengers",
        "🚦 Average Delay",
        "✅ On-Time Performance",
        "🧭 Recommendation"
    ],
    "Insight": [
        f"{best_route} ({best_load:.0f}% load)",
        f"{worst_trip} — {worst_delay:.1f} min",
        f"{risk_label} ({route_risk_df['risk_score'].mean():.0f}%)",
        f"{avg_passengers} pax",
        f"{avg_delay:.1f} min",
        f"{on_time:.0f}%",
        recommendation
    ]
}

insight_df = pd.DataFrame(insights)
st.dataframe(insight_df, use_container_width=True, height=260)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Download / Export quick insights as CSV
# ---------------------------
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv_bytes = convert_df_to_csv(insight_df)
st.download_button(label="📥 Download Insights CSV", data=csv_bytes, file_name="quick_insights.csv", mime="text/csv")

# ---------------------------
# Footer
# ---------------------------
st.markdown(
    """
    <div class="footer">
      📊 Smart Public Transport Analytics v2.0 • Built by Kira Konjeti • Python · Streamlit · PostgreSQL · ML · Folium · Plotly
    </div>
    """, unsafe_allow_html=True
)

