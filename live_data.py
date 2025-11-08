import psycopg2
import random
import time
from datetime import datetime

def simulate_live_data():
    conn = psycopg2.connect(
        dbname="transport",
        user="postgres",
        password="123456789",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    while True:
        trip_id = random.choice(["T1", "T2", "T3"])
        vehicle_id = random.choice(["V101", "V102", "V103"])
        latitude = 17.35 + random.random() * 0.1
        longitude = 78.45 + random.random() * 0.1
        speed = random.uniform(25, 50)

        cur.execute("""
            INSERT INTO transit.gps_pings (trip_id, vehicle_id, ts, lat, lon, speed_kmph)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (trip_id, vehicle_id, datetime.now(), latitude, longitude, speed))
        conn.commit()

        print(f"✅ Live GPS ping inserted for {trip_id} at {datetime.now()}")
        time.sleep(10)

simulate_live_data()
