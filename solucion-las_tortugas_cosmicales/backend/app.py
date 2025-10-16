import pandas as pd
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from threading import Lock

# Basic paths (no ML needed)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)

# ---------------- Performance: simple in-memory cache by month ----------------
CACHE_TTL_SECONDS = 60 * 30  # 30 minutes TTL; adjust as needed
_data_cache = {}  # month -> { ts: datetime, df: DataFrame, zone_stats: DataFrame }
_cache_lock = Lock()
_month_locks = {}

_lookup_df = None
ZONE_LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

def get_lookup_df():
    global _lookup_df
    if _lookup_df is None:
        try:
            lookup = pd.read_csv(ZONE_LOOKUP_URL)[["LocationID", "Borough", "Zone"]]
            lookup = lookup.rename(columns={"Zone": "zone_name", "Borough": "borough"})
            _lookup_df = lookup
        except Exception:
            _lookup_df = None
    return _lookup_df

def _get_month_lock(month: str) -> Lock:
    with _cache_lock:
        lock = _month_locks.get(month)
        if lock is None:
            lock = Lock()
            _month_locks[month] = lock
        return lock

# No ML model or prediction endpoints in the simplified backend

# Helper to load and process data for a given month
def load_and_process_data(month="2023-01"):
    """Load monthly data, or aggregate all 2023 months if month=='all'."""
    if month == "all":
        months = [f"2023-{m:02d}" for m in range(1, 13)]
        dfs = []
        for m in months:
            df, _ = load_and_process_data(m)
            dfs.append(df)
        df_night_solo = pd.concat(dfs, ignore_index=True)
        # Aggregate zone stats across all months
        zone_stats = df_night_solo.groupby("PULocationID").agg(
            total_rides=("PULocationID", "size"),
            avg_distance=("trip_distance", "mean"),
            avg_fare=("fare_amount", "mean"),
        )
        min_rides = zone_stats["total_rides"].min()
        max_rides = zone_stats["total_rides"].max()
        if pd.isna(min_rides) or pd.isna(max_rides) or max_rides == min_rides:
            zone_stats["safety_index"] = 0.5
        else:
            zone_stats["safety_index"] = (zone_stats["total_rides"] - min_rides) / (max_rides - min_rides)
        lookup = get_lookup_df()
        if lookup is not None:
            zone_stats_named = (
                zone_stats.reset_index()
                .merge(lookup, left_on="PULocationID", right_on="LocationID", how="left")
            )
            zone_stats_named = zone_stats_named[[
                "PULocationID", "zone_name", "borough", "total_rides", "avg_distance", "avg_fare", "safety_index",
            ]]
        else:
            zone_stats_named = zone_stats.reset_index()
        return df_night_solo, zone_stats_named

    now = datetime.utcnow()
    with _cache_lock:
        entry = _data_cache.get(month)
        if entry and now - entry["ts"] < timedelta(seconds=CACHE_TTL_SECONDS):
            return entry["df"], entry["zone_stats"]
    # Serialize per-month computation to avoid duplicate downloads/work under load
    month_lock = _get_month_lock(month)
    with month_lock:
        # Re-check cache inside lock to avoid duplicate work
        with _cache_lock:
            entry = _data_cache.get(month)
            if entry and now - entry["ts"] < timedelta(seconds=CACHE_TTL_SECONDS):
                return entry["df"], entry["zone_stats"]

    URL = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet"
    columns = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "PULocationID",
        "DOLocationID",
        "fare_amount",
        "payment_type",
    ]
    df = pd.read_parquet(URL, columns=columns, engine="pyarrow")
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"], errors="coerce")
    df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour
    # Use ALL hours now, not just 0-3am
    df_all_day = df.copy()

    # Compute zone-level stats (all hours combined)
    zone_stats = df_all_day.groupby("PULocationID").agg(
        total_rides=("PULocationID", "size"),
        avg_distance=("trip_distance", "mean"),
        avg_fare=("fare_amount", "mean"),
    )

    # Normalize rides to 0-1 with guard against division by zero
    min_rides = zone_stats["total_rides"].min()
    max_rides = zone_stats["total_rides"].max()
    if pd.isna(min_rides) or pd.isna(max_rides) or max_rides == min_rides:
        zone_stats["safety_index"] = 0.5
    else:
        zone_stats["safety_index"] = (zone_stats["total_rides"] - min_rides) / (max_rides - min_rides)

    # Compute zone+hour level stats for hourly safety
    zone_hour_stats = df_all_day.groupby(["PULocationID", "pickup_hour"]).agg(
        rides=("PULocationID", "size"),
        avg_distance=("trip_distance", "mean"),
        avg_fare=("fare_amount", "mean"),
    ).reset_index()
    
    # Normalize hourly rides within each zone to get hourly safety index
    zone_hour_list = []
    for zone_id in zone_hour_stats["PULocationID"].unique():
        zone_data = zone_hour_stats[zone_hour_stats["PULocationID"] == zone_id].copy()
        min_r = zone_data["rides"].min()
        max_r = zone_data["rides"].max()
        if pd.isna(min_r) or pd.isna(max_r) or max_r == min_r:
            zone_data["hourly_safety"] = 0.5
        else:
            zone_data["hourly_safety"] = (zone_data["rides"] - min_r) / (max_r - min_r)
        zone_hour_list.append(zone_data)
    
    zone_hour_stats = pd.concat(zone_hour_list, ignore_index=True) if zone_hour_list else zone_hour_stats

    # Add zone names/borough from cached lookup
    lookup = get_lookup_df()
    if lookup is not None:
        zone_stats_named = (
            zone_stats.reset_index()
            .merge(lookup, left_on="PULocationID", right_on="LocationID", how="left")
        )
        zone_stats_named = zone_stats_named[[
            "PULocationID", "zone_name", "borough", "total_rides", "avg_distance", "avg_fare", "safety_index",
        ]]
    else:
        zone_stats_named = zone_stats.reset_index()

    with _cache_lock:
        _data_cache[month] = {
            "ts": now, 
            "df": df_all_day, 
            "zone_stats": zone_stats_named,
            "zone_hour_stats": zone_hour_stats
        }

    return df_all_day, zone_stats_named


def add_cache_headers(resp, max_age=300):
    """Add basic Cache-Control headers for client/proxy caching."""
    resp.headers["Cache-Control"] = f"public, max-age={max_age}"
    return resp


@app.route("/")
def home():
    return "Funciona el backend ayyych uwu!"

@app.route("/summary")
def summary():
    month = request.args.get("month", "2023-01")
    df_all_day, _ = load_and_process_data(month)
    total_rides = int(df_all_day.shape[0])
    _avg_distance = df_all_day["trip_distance"].mean()
    _avg_fare = df_all_day["fare_amount"].mean()
    avg_distance = None if pd.isna(_avg_distance) else float(_avg_distance)
    avg_fare = None if pd.isna(_avg_fare) else float(_avg_fare)
    resp = jsonify({
        "total_rides": total_rides,
        "avg_distance": avg_distance,
        "avg_fare": avg_fare
    })
    return add_cache_headers(resp, max_age=300)

@app.route("/zone-stats")
def zone_stats_route():
    month = request.args.get("month", "2023-01")
    _, zone_stats_named = load_and_process_data(month)
    data = json.loads(zone_stats_named.to_json(orient="records"))
    resp = jsonify(data)
    return add_cache_headers(resp, max_age=300)

@app.route("/hourly-trends")
def hourly_trends():
    month = request.args.get("month", "2023-01")
    df_all_day, _ = load_and_process_data(month)
    hourly_counts = df_all_day["pickup_hour"].value_counts().sort_index()
    resp = jsonify(hourly_counts.to_dict())
    return add_cache_headers(resp, max_age=300)

@app.route("/preview")
def preview():
    month = request.args.get("month", "2023-01")
    df_all_day, _ = load_and_process_data(month)
    preview_data = json.loads(df_all_day.head(20).to_json(orient="records"))
    resp = jsonify(preview_data)
    return add_cache_headers(resp, max_age=120)

@app.route("/zone-safety/<int:zone_id>")
def zone_safety(zone_id):
    """Get detailed hourly safety data for a specific zone"""
    month = request.args.get("month", "2023-01")
    
    # Load cached data
    with _cache_lock:
        entry = _data_cache.get(month)
    
    if not entry:
        # Force load if not cached
        load_and_process_data(month)
        with _cache_lock:
            entry = _data_cache.get(month)
    
    if not entry:
        return jsonify({"error": "Data not available"}), 404
    
    zone_hour_stats = entry.get("zone_hour_stats")
    zone_stats = entry.get("zone_stats")
    
    # Get zone info
    zone_info = zone_stats[zone_stats["PULocationID"] == zone_id]
    if zone_info.empty:
        return jsonify({"error": "Zone not found"}), 404
    
    zone_info_dict = zone_info.iloc[0].to_dict()
    
    # Get hourly data for this zone
    hourly_data = zone_hour_stats[zone_hour_stats["PULocationID"] == zone_id].copy()
    hourly_data = hourly_data.sort_values("pickup_hour")
    
    # Find safest hours (top 3)
    safest_hours = hourly_data.nlargest(3, "hourly_safety")[["pickup_hour", "hourly_safety"]].to_dict(orient="records")
    
    # Format response
    result = {
        "zone_id": int(zone_id),
        "zone_name": zone_info_dict.get("zone_name", f"Zone {zone_id}"),
        "borough": zone_info_dict.get("borough", "Unknown"),
        "overall_safety_index": float(zone_info_dict.get("safety_index", 0.5)),
        "total_rides": int(zone_info_dict.get("total_rides", 0)),
        "avg_distance": float(zone_info_dict.get("avg_distance", 0)) if not pd.isna(zone_info_dict.get("avg_distance")) else None,
        "avg_fare": float(zone_info_dict.get("avg_fare", 0)) if not pd.isna(zone_info_dict.get("avg_fare")) else None,
        "hourly_safety": hourly_data[["pickup_hour", "hourly_safety", "rides"]].to_dict(orient="records"),
        "safest_hours": safest_hours
    }
    
    resp = jsonify(result)
    return add_cache_headers(resp, max_age=300)

if __name__ == "__main__":
    try:
        # Warm cache for default month in background (optional)
        import threading
        def _warm():
            try:
                load_and_process_data("2023-01")
                print("Cache warm complete for 2023-01")
            except Exception as e:
                print(f"Cache warm failed: {e}")
        threading.Thread(target=_warm, daemon=True).start()
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error starting the application: {str(e)}")
        import traceback
        traceback.print_exc()