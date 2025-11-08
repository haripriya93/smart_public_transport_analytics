🧠 Overview

The Smart Public Transport Analytics System is a real-time data-driven dashboard that monitors and analyzes public transport performance.
It tracks vehicle GPS locations, evaluates trip delays and passenger load factors, and predicts future delays using machine learning.

This project demonstrates end-to-end data engineering, real-time analytics, and AI-driven insights — all in one deployable web app.

🧰 Tech Stack
Layer	Technology	Purpose
Database	PostgreSQL	Stores trip, route, and GPS data
Programming	Python (psycopg2, pandas)	Data handling and simulation
Visualization	Streamlit + Plotly	Interactive web dashboard
Mapping	Folium + streamlit-folium	Real-time vehicle tracker map
Machine Learning	Scikit-learn	Predictive delay analytics
Hosting	Streamlit Cloud	Live deployment (Demo Mode enabled)
🚦 Features

✅ KPI Dashboard — Average Delay, Load Factor, On-Time Percentage
📊 Charts — Delay per Trip, Load Factor per Route
🔮 Predictive Analytics — Forecasts future bus delays using Linear Regression
🗺️ Vehicle Tracker Map — Real-time visualization of vehicle GPS data
🌐 Cloud Deployment — Works online via Streamlit Cloud
🧩 Demo Mode — Automatically loads sample data when no database is connected

	
	
🏗️ Project Architecture
smart_public_transport_analytics/
├── live_data_feed.py            # Simulates GPS pings (optional)
├── transport_dashboard.py       # Streamlit dashboard (main app)
├── schema.sql                   # PostgreSQL tables and views
├── requirements.txt             # Dependencies for Streamlit Cloud
└── README.md                    # Project documentation

💾 Database Design
Tables:

routes — route details

trips — individual bus trips (T1, T2, T3, …)

stops — bus stop info

vehicles — vehicle master data

gps_pings — live GPS location and speed data

ridership — passenger counts

stop_times — stop-wise timing and delay data

Views:

mv_trip_punctuality — trip-level delay summary

v_route_load_factor — route-level load analytics

⚙️ Setup Instructions
🔹 Local Setup

1️⃣ Install dependencies

pip install -r requirements.txt


2️⃣ Run PostgreSQL and import schema

psql -U postgres -d transport -f schema.sql


3️⃣ Run dashboard

streamlit run transport_dashboard.py


4️⃣ (Optional) Run live GPS simulation

python live_data_feed.py

🔹 Streamlit Cloud Setup (for Hosting)

1️⃣ Push all files (transport_dashboard.py, requirements.txt, README.md) to GitHub
2️⃣ Go to https://share.streamlit.io

3️⃣ Deploy → Select your repo
4️⃣ Your app will auto-detect demo mode and load successfully online

🧮 Predictive Analytics

The dashboard uses a Linear Regression model from scikit-learn
to forecast upcoming trip delays based on current delay patterns.

model = LinearRegression()
model.fit(df_delay[["stop_sequence"]], df_delay["avg_delay_min"])
predictions = model.predict(future_seq)


✅ Helps estimate how delays might increase across future trips.

🗺️ Vehicle Tracker Map

The Vehicle Tracker Map shows the live (or simulated) position of all vehicles:

Trip ID	Vehicle ID	Latitude	Longitude	Speed (km/h)
T1	V101	17.39	78.49	42
T2	V102	17.41	78.51	36
T3	V103	17.37	78.47	29
T4	V104	17.43	78.52	31

Each pin on the map = one active bus.
Clicking a pin displays trip details and speed.

📈 KPI Definitions
Metric	Description
⏱️ Average Delay	Mean delay in minutes per trip
🚦 Max Delay	Maximum delay observed
🧍 Load Factor	Passenger occupancy percentage
✅ On-Time %	% of trips with delay ≤ 5 minutes
🤖 Demo Mode Explained

To ensure the app always runs (even without a live DB),
a “Demo Mode” automatically loads pre-defined CSV data for all tables.

if not conn:
    df_gps = pd.read_csv(io.StringIO(csv_gps))


✅ Works seamlessly on Streamlit Cloud
✅ Perfect for recruiters and demo links


🚀 Future Enhancements

Integrate Google Maps APIs for real route visualization

Add real public data feeds (Open Transit APIs)

Include alerts for major delays

Build a driver performance report

A
