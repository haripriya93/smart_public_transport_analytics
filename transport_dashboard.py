# -----------------------------
# 🚍 SMART PUBLIC TRANSPORT ANALYTICS DASHBOARD
# Works in both: Local (Live DB) and Streamlit Cloud (Demo Mode)
# -----------------------------

# -----------------------------------------------------------
# 🚍 SMART PUBLIC TRANSPORT ANALYTICS — DARK MODE (NO SIDEBAR)
# Works in LIVE DB mode (local PostgreSQL) and DEMO mode (cloud)
# -----------------------------------------------------------

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
# PAGE CONFIG + DARK THEME CSS
# -----------------------------
st.set_page_config(page_title="Smart Transport Dashboard", layout="wide")

DARK_CSS = """
<style>
/* Global dark look */
html, body, [class*="css"]  {
  background-color: #0f1115 !important;
  color: #e6e6e6 !important;
}

/* Title */
h1, h2, h3 {
  color: #f3f4f6 !important;
}

/* Section cards */
.block {
  background: #151823;
  border: 1px solid #23283b;
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 0 20px rgba(0,0,0,0.25);
}

/* KPI cards */
.kpi {
  background: linear-gradient(135deg, #171a26 0%, #11131b 100%);
  border: 1px solid #24283b;
  border-radius: 16px;
  padding: 16px;
  text-align: left;
  box-shadow: inset 0 0 12px rgba(16, 97, 255, 0.08);
}
.kpi .label { color:#9aa4b2; font-size:13px; }
.kpi .value { color:#e8eefc; font-size:26px; font-weight:700; margin-top:4px; }
.kpi .badge { font-size:12px; color:#8aa1ff; }

/* Footer */
.footer {
  color:#9aa4b2; text-align:center; margin-top:18px; font-size:13px;
}

/* Plotly charts container fix */
.stPlotlyChart { background: #151823; border-radius: 16px; padding: 8px; border:1px solid #23283b; }

/* Buttons / warnings */
.stAlert { border-radius: 12px; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    """
    <div class="block" style="padding:20px 22px; display:flex; flex-direction:column; gap:4px;">
      <div style="font-size:28px; font-weight:800;">🚍 Smart Public Transport Analytics Dashboard</div>
      <div style="color:#9aa4b2;">Real-time Monitoring • Performance Insights • Predictive Analytics</div>
    </div>
    """, unsafe_allow_html=True
)

# ----------------------------------------
# AUTO REFRESH (every 15s to feel live)
# ----------------------------------------
st_autorefresh(interval=15000, key="refresh")

# ----------------------------------------
# SAFE DB CONNECTION (falls back to demo)
# ----------------------------------------
def get_connection():
    try:
        conn = psycopg2.connect(
            dbname="transport",
            user="postgres",
            password="postgres",   # change for your local if needed
            host="localhost",
            port="5432"
        )
        return conn
    except Exception:
        return None

conn = get_connection()
if conn:
    st.success("✅ Connected to local PostgreSQL database")
else:
    st.warning("⚠️ Demo Mode: showing sample data (no DB connection)")

# ----------------------------------------
# LOAD DATA (LIVE if conn, else DEMO)
# ----------------------------------------
def load_live():
    df_delay = pd.read_sql("SELECT * FROM transit.mv_trip_punctuality", conn)
    df_load  = pd.read_sql("SELECT * FROM transit.v_route_load_factor", conn)
    df_gps   = pd.read_sql("SELECT * FROM transit.gps_pings ORDER BY ts DESC LIMIT 50", conn)
    return df_delay, df_load, df_gps

def load_demo():
    csv_delay = """trip_id,avg_delay_min
T1,4.2
T2,6.8
T3,3.1
T4,8.0
T5,5.0
"""
    csv_load = """route_name,load_factor_est
Route 1,0.82
Route 2,0.67
Route 3,0.90
Route 4,0.75
"""
    csv_gps = """trip_id,vehicle_id,ts,lat,lon,speed_kmph
T1,V101,2025-11-07 10:00:00,17.390,78.490,42
T2,V102,2025-11-07 10:05:00,17.410,78.510,36
T3,V103,2025-11-07 10:10:00,17.370,78.470,29
T4,V104,2025-11-07 10:15:00,17.430,78.520,31
T5,V105,2025-11-07 10:20:00,17.405,78.505,40
"""
    df_delay = pd.read_csv(io.StringIO(csv_delay))
    df_load  = pd.read_csv(io.StringIO(csv_load))
    df_gps   = pd.read_csv(io.StringIO(csv_gps))
    return df_delay, df_load, df_gps

if conn:
    try:
        df_delay, df_load, df_gps = load_live()
        conn.close()
    except Exception:
        st.warning("⚠️ Could not query DB — switched to Demo Mode")
        df_delay, df_load, df_gps = load_demo()
else:
    df_delay, df_load, df_gps = load_demo()

# Merge last delay onto GPS for map coloring (if possible)
delay_map = df_delay[["trip_id", "avg_delay_min"]].drop_duplicates()
df_gps = df_gps.merge(delay_map, on="trip_id", how="left")
df_gps["avg_delay_min"] = df_gps["avg_delay_min"].fillna(0)

# Ensure numeric types
for c in ["avg_delay_min"]:
    df_delay[c] = pd.to_numeric(df_delay[c], errors="coerce").fillna(0)
for c in ["load_factor_est"]:
    df_load[c] = pd.to_numeric(df_load[c], errors="coerce").fillna(0)

# -----------------------------
# KPI SECTION (top row)
# -----------------------------
avg_delay = float(df_delay["avg_delay_min"].mean()) if not df_delay.empty else 0.0
max_delay = float(df_delay["avg_delay_min"].max()) if not df_delay.empty else 0.0
avg_load_pct = float(df_load["load_factor_est"].mean() * 100) if not df_load.empty else 0.0
on_time = (len(df_delay[df_delay["avg_delay_min"] <= 5]) / len(df_delay) * 100) if len(df_delay) else 0.0
total_trips = int(df_delay["trip_id"].nunique()) if "trip_id" in df_delay.columns else len(df_delay)
delay_risk = min(100, round((avg_delay / (max(1.0, max_delay))) * 85 + (100 - on_time) * 0.15, 1)) if max_delay > 0 else 0.0

def kpi_card(label, value, badge=None):
    return f"""
    <div class="kpi">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
      <div class="badge">{badge or ""}</div>
    </div>
    """

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: st.markdown(kpi_card("⏱️ Avg Delay", f"{avg_delay:.1f} min"), unsafe_allow_html=True)
with k2: st.markdown(kpi_card("🚦 Max Delay", f"{max_delay:.1f} min"), unsafe_allow_html=True)
with k3: st.markdown(kpi_card("🧍 Load Factor", f"{avg_load_pct:.0f}%"), unsafe_allow_html=True)
with k4: st.markdown(kpi_card("✅ On-Time %", f"{on_time:.0f}%"), unsafe_allow_html=True)
with k5: st.markdown(kpi_card("🚌 Trips Today", f"{total_trips}"), unsafe_allow_html=True)
with k6:
    risk_badge = "Low" if delay_risk < 40 else ("Medium" if delay_risk < 70 else "High")
    st.markdown(kpi_card("🔮 Delay Risk", f"{delay_risk:.0f}%", badge=risk_badge), unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# -----------------------------
# CHARTS (Delay trend, Load, Prediction)
# -----------------------------
c1, c2 = st.columns((2,1))

# Delay trend / distribution (use sequence if no timestamp)
with c1:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.subheader("🕒 Delay by Trip")
    df_delay_plot = df_delay.copy()
    df_delay_plot["seq"] = np.arange(1, len(df_delay_plot) + 1)
    fig_delay = px.bar(
        df_delay_plot, x="trip_id", y="avg_delay_min",
        title="Average Delay per Trip (minutes)",
        labels={"avg_delay_min": "Delay (min)", "trip_id": "Trip"}
    )
    fig_delay.update_layout(template="plotly_dark", height=360, margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig_delay, use_container_width=True, key="delay_chart")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.subheader("👥 Load Factor by Route")
    fig_load = px.bar(
        df_load, x="route_name", y="load_factor_est",
        title="Estimated Load Factor (Higher = busier)",
        labels={"load_factor_est": "Load Factor", "route_name": "Route"},
    )
    fig_load.update_layout(template="plotly_dark", height=360, margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig_load, use_container_width=True, key="load_chart")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# Prediction
st.markdown('<div class="block">', unsafe_allow_html=True)
st.subheader("🔮 Predicted Delay (Next Trips)")
df_pred = df_delay.copy()
df_pred["seq"] = np.arange(1, len(df_pred) + 1)
# Handle tiny datasets safely
y = df_pred["avg_delay_min"].values
X = df_pred[["seq"]].values
if len(df_pred) >= 2:
    model = LinearRegression()
    model.fit(X, y)
    future_seq = np.arange(len(df_pred) + 1, len(df_pred) + 6).reshape(-1, 1)
    pred_vals = model.predict(future_seq)
    pred_df = pd.DataFrame({"seq": future_seq.flatten(), "predicted_delay": pred_vals})
else:
    # Fallback if too few points
    future_seq = np.arange(len(df_pred) + 1, len(df_pred) + 6)
    pred_df = pd.DataFrame({"seq": future_seq, "predicted_delay": [avg_delay]*5})

fig_pred = px.line(
    pred_df, x="seq", y="predicted_delay",
    title="Forecasted Delay for Upcoming Trips",
    labels={"predicted_delay": "Predicted Delay (min)", "seq": "Future Trip Index"}
)
fig_pred.update_traces(mode="lines+markers")
fig_pred.update_layout(template="plotly_dark", height=340, margin=dict(l=10,r=10,t=50,b=10))
st.plotly_chart(fig_pred, use_container_width=True, key="predict_chart")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# -----------------------------
# LIVE VEHICLE MAP (dark tiles)
# -----------------------------
st.markdown('<div class="block">', unsafe_allow_html=True)
st.subheader("🗺️ Vehicle Tracker Map")

if not df_gps.empty:
    center_lat = float(df_gps["lat"].mean())
    center_lon = float(df_gps["lon"].mean())
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB dark_matter")

    # Color by delay
    def delay_color(d):
        if d < 5: return "green"
        if d < 10: return "orange"
        return "red"

    for _, r in df_gps.iterrows():
        folium.Marker(
            [float(r["lat"]), float(r["lon"])],
            popup=(
                f"Trip: {r.get('trip_id','')}<br>"
                f"Vehicle: {r.get('vehicle_id','')}<br>"
                f"Speed: {r.get('speed_kmph','')} km/h<br>"
                f"Delay: {float(r.get('avg_delay_min',0)):.1f} min"
            ),
            icon=folium.Icon(color=delay_color(float(r.get("avg_delay_min", 0))), icon="bus", prefix="fa")
        ).add_to(m)

    st_folium(m, width=1100, height=520)
else:
    st.info("No GPS data available to plot right now.")
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# INSIGHTS (auto narrative)
# -----------------------------
st.markdown('<div class="block">', unsafe_allow_html=True)
st.subheader("🧠 Quick Insights")

# Best / worst from current data
best_route = df_load.sort_values("load_factor_est", ascending=False).head(1)["route_name"].iloc[0] if not df_load.empty else "N/A"
worst_trip_row = df_delay.sort_values("avg_delay_min", ascending=False).head(1)
worst_trip = worst_trip_row["trip_id"].iloc[0] if len(worst_trip_row) else "N/A"
worst_delay = float(worst_trip_row["avg_delay_min"].iloc[0]) if len(worst_trip_row) else 0.0

recommendation = "Add an extra bus on busiest routes during peak hours" if avg_load_pct > 80 else "Current capacity is adequate; monitor peak slots"
risk_label = "Low" if delay_risk < 40 else ("Moderate" if delay_risk < 70 else "High")

insight_md = f"""
- 🏆 **Best Performing Route (by demand)**: **{best_route}**
- ⚠️ **Most Delayed Trip**: **{worst_trip}** ({worst_delay:.1f} min)
- 🔮 **Delay Risk (AI)**: **{risk_label} — {delay_risk:.0f}%**
- 🧭 **Recommendation**: {recommendation}
"""
st.markdown(insight_md)
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown(
    """
    <div class="footer">
      📊 Smart Public Transport Analytics • Built by Kira Konjeti • Python · Streamlit · PostgreSQL · Plotly · Folium · ML
    </div>
    """, unsafe_allow_html=True
)
