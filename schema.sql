CREATE SCHEMA IF NOT EXISTS transit;
SET search_path TO transit, public;

CREATE TABLE IF NOT EXISTS routes (
    route_id text PRIMARY KEY,
    route_name text NOT NULL,
    agency text NOT NULL
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id text PRIMARY KEY,
    stop_name text NOT NULL,
    lat numeric(9,6),
    lon numeric(9,6)
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id text PRIMARY KEY,
    vehicle_type text NOT NULL,
    capacity int
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id text PRIMARY KEY,
    route_id text REFERENCES routes(route_id),
    service_date date NOT NULL,
    vehicle_id text REFERENCES vehicles(vehicle_id)
);

CREATE TABLE IF NOT EXISTS stop_times (
    trip_id text REFERENCES trips(trip_id),
    stop_id text REFERENCES stops(stop_id),
    stop_sequence int NOT NULL,
    scheduled_arrival timestamp NOT NULL,
    actual_arrival timestamp,
    PRIMARY KEY (trip_id, stop_sequence)
);

CREATE TABLE IF NOT EXISTS ridership (
    tap_id text PRIMARY KEY,
    trip_id text REFERENCES trips(trip_id),
    stop_id text REFERENCES stops(stop_id),
    tap_time timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS gps_pings (
    trip_id text REFERENCES trips(trip_id),
    vehicle_id text REFERENCES vehicles(vehicle_id),
    ts timestamp NOT NULL,
    lat numeric(9,6),
    lon numeric(9,6),
    speed_kmph numeric(6,2),
    PRIMARY KEY (trip_id, ts)
);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_trip_punctuality AS
SELECT
  st.trip_id,
  min(st.scheduled_arrival) AS first_sched,
  min(st.actual_arrival) AS first_actual,
  avg(EXTRACT(EPOCH FROM (st.actual_arrival - st.scheduled_arrival))/60.0) AS avg_delay_min
FROM stop_times st
GROUP BY st.trip_id;

CREATE VIEW IF NOT EXISTS v_route_load_factor AS
SELECT
  t.trip_id, r.route_name, v.capacity,
  count(*)::numeric / NULLIF(v.capacity,0) AS load_factor_est
FROM trips t
JOIN ridership ri ON ri.trip_id = t.trip_id
JOIN routes r ON r.route_id = t.route_id
JOIN vehicles v ON v.vehicle_id = t.vehicle_id
GROUP BY t.trip_id, r.route_name, v.capacity;
