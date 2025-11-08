import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np

# DB Connection
conn = psycopg2.connect(
    dbname="transport",
    user="postgres",
    password="123456789",
    host="localhost",
    port="5432"
)

# Load data
df_delay = pd.read_sql("SELECT * FROM transit.mv_trip_punctuality", conn)
df_load = pd.read_sql("SELECT * FROM transit.v_route_load_factor", conn)
conn.close()

# Title
st.title("🚍 Smart Public Transport Analytics Dashboard")

# --- KPI SECTION ---
st.subheader("📊 Key Performance Indicators (KPIs)")
col1, col2, col3 = st.columns(3)
col1.metric("Avg Delay (min)", round(df_delay["avg_delay_min"].mean(), 2))
col2.metric("Max Delay (min)", round(df_delay["avg_delay_min"].max(), 2))
col3.metric("Avg Load Factor", round(df_load["load_factor_est"].mean(), 2))

# --- CHARTS ---
st.subheader("🕒 Average Delay per Trip")
fig1 = px.bar(df_delay, x="trip_id", y="avg_delay_min", color="trip_id", title="Average Delay per Trip")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("👥 Estimated Load Factor per Route")
fig2 = px.bar(df_load, x="route_name", y="load_factor_est", color="route_name", title="Estimated Load Factor per Route")
st.plotly_chart(fig2, use_container_width=True)

# --- PREDICTIVE ANALYTICS (Simple Regression Example) ---
st.subheader("🔮 Predictive Analytics: Estimate Delay by Stop Sequence")

# Create fake independent variable (stop_sequence)
df_delay["stop_sequence"] = np.arange(1, len(df_delay)+1)

model = LinearRegression()
model.fit(df_delay[["stop_sequence"]], df_delay["avg_delay_min"])
future_seq = np.arange(1, len(df_delay)+5).reshape(-1, 1)
predicted_delays = model.predict(future_seq)

pred_df = pd.DataFrame({
    "stop_sequence": future_seq.flatten(),
    "predicted_delay": predicted_delays
})

fig3 = px.line(pred_df, x="stop_sequence", y="predicted_delay", title="Predicted Future Delays")
st.plotly_chart(fig3, use_container_width=True)

st.success("✅ Dashboard refreshed successfully!")


import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Smart Transport Dashboard", layout="wide")

st.title("🚍 Smart Public Transport Analytics (Live Dashboard)")

from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 15 seconds
st_autorefresh(interval=15000, limit=None, key="refresh")

# Connect to PostgreSQL
def get_conn():
    return psycopg2.connect(
        dbname="transport",
        user="postgres",
        password="123456789",
        host="localhost",
        port="5432"
    )

# Load data from your existing schema and views
conn = get_conn()
df_delay = pd.read_sql("SELECT * FROM transit.mv_trip_punctuality", conn)
df_load = pd.read_sql("SELECT * FROM transit.v_route_load_factor", conn)
df_gps = pd.read_sql("SELECT * FROM transit.gps_pings ORDER BY ts DESC LIMIT 10", conn)
conn.close()

# --- KPI Section ---
st.subheader("📊 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Delay (min)", round(df_delay["avg_delay_min"].mean(), 2))
col2.metric("Max Delay (min)", round(df_delay["avg_delay_min"].max(), 2))
col3.metric("Avg Load Factor", round(df_load["load_factor_est"].mean(), 2))
on_time = len(df_delay[df_delay["avg_delay_min"] <= 5]) / len(df_delay) * 100
col4.metric("On-Time %", f"{round(on_time, 1)}%")

# --- Charts ---
st.subheader("🕒 Average Delay per Trip")
fig1 = px.bar(df_delay, x="trip_id", y="avg_delay_min", color="trip_id", title="Average Delay per Trip")
st.plotly_chart(fig1, use_container_width=True, key="delay_chart")
st.plotly_chart(fig2, use_container_width=True, key="load_chart")
st.plotly_chart(fig3, use_container_width=True, key="predict_chart")


st.subheader("👥 Load Factor per Route")
fig2 = px.bar(df_load, x="route_name", y="load_factor_est", color="route_name", title="Load Factor per Route")
st.plotly_chart(fig2, use_container_width=True)

# --- Predictive Analytics ---
st.subheader("🔮 Predict Future Delay Trends")
df_delay["stop_sequence"] = np.arange(1, len(df_delay) + 1)
model = LinearRegression()
model.fit(df_delay[["stop_sequence"]], df_delay["avg_delay_min"])
future_seq = np.arange(1, len(df_delay) + 6).reshape(-1, 1)
predictions = model.predict(future_seq)
pred_df = pd.DataFrame({"stop_sequence": future_seq.flatten(), "predicted_delay": predictions})
fig3 = px.line(pred_df, x="stop_sequence", y="predicted_delay", title="Predicted Delay for Future Trips")
st.plotly_chart(fig3, use_container_width=True)

# --- Live Map ---
st.subheader("🗺️ Live Vehicle Tracker (updates every 15s)")
m = folium.Map(location=[17.3850, 78.4867], zoom_start=12)
for _, row in df_gps.iterrows():
    folium.Marker(
        [row["lat"], row["lon"]],
        popup=f"{row['trip_id']} | Speed: {round(row['speed_kmph'],1)} km/h"
    ).add_to(m)
st_folium(m, width=700, height=500)

st.success("✅ Dashboard refreshed successfully!")

