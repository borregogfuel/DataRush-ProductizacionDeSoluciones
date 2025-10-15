import pandas as pd
import json
import numpy as np
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from datetime import datetime, timedelta
import joblib
from sklearn.ensemble import RandomForestRegressor
import os
import sys
from threading import Lock

try:
    from flask_compress import Compress
except ImportError:
    Compress = None  # Optional dependency; enable if installed

# Get the absolute path of the current directory and project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
ML_DIR = os.path.join(PROJECT_ROOT, 'ML')

# Add ML directory to Python path
sys.path.insert(0, ML_DIR)  # Ensure ML directory is at the start of sys.path

# Configure paths
# Prefer the improved model if available
MODEL_PATH = os.path.join(ML_DIR, 'safety_model_improved.joblib')
FALLBACK_MODEL_PATH = os.path.join(ML_DIR, 'safety_model.joblib')
DATA_PATH = os.path.join(ML_DIR, 'NYC_complaint_data.csv')

print(f"Current directory: {CURRENT_DIR}")
print(f"Project root: {PROJECT_ROOT}")
print(f"ML directory: {ML_DIR}")
print(f"Model path: {MODEL_PATH}")
print(f"Data path: {DATA_PATH}")

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)
if Compress is not None:
    Compress(app)

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

def get_safety_model():
    try:
        # Try improved model first, then fallback
        if os.path.exists(MODEL_PATH):
            print("Loading improved model...")
            return joblib.load(MODEL_PATH)
        if os.path.exists(FALLBACK_MODEL_PATH):
            print("Loading fallback model...")
            return joblib.load(FALLBACK_MODEL_PATH)
        print("No model files found — attempting to create a model from raw data...")
        try:
            # First read the CSV data
            print("Reading CSV data...")
            df = pd.read_csv(DATA_PATH)

            # Then ensure ML directory is available and import main
            if ML_DIR not in sys.path:
                sys.path.insert(0, ML_DIR)
            print(f"Python path: {sys.path}")
            print("Attempting to import main module...")
            import main
            print("Main module imported successfully")
            print("Processing data...")
            df = main.load_and_preprocess_data(DATA_PATH)
            print("Creating safety index...")
            safety_data = main.create_safety_index(df)
            print("Training model...")
            model = main.train_safety_model(safety_data)
            print("Saving model...")
            joblib.dump(model, MODEL_PATH)
            return model
        except Exception as e:
            print(f"Error importing/training model: {str(e)}")
            print(f"Full error details:")
            import traceback
            traceback.print_exc()
            # Fallback to create a simple model if import fails
            print("Creating fallback model...")
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            X = np.random.rand(100, 2)  # Sample data
            y = np.random.rand(100)
            model.fit(X, y)
            return model
    except Exception as e:
        print(f"Error in get_safety_model: {str(e)}")
        raise

def get_safety_label(score):
    """Convert numerical safety score to label"""
    if score >= 80:
        return "Very Safe"
    elif score >= 60:
        return "Safe"
    elif score >= 40:
        return "Moderate"
    elif score >= 20:
        return "Use Caution"
    else:
        return "Not Recommended"

# Helper to load and process data for a given month
def load_and_process_data(month="2023-01"):
    """Load monthly data, filter, aggregate and cache results for faster responses."""
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
    df_night_solo = df[(df["pickup_hour"] >= 0) & (df["pickup_hour"] < 4) & (df["passenger_count"] == 1)]

    zone_stats = df_night_solo.groupby("PULocationID").agg(
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
        _data_cache[month] = {"ts": now, "df": df_night_solo, "zone_stats": zone_stats_named}

    return df_night_solo, zone_stats_named


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
    df_night_solo, _ = load_and_process_data(month)
    total_rides = int(df_night_solo.shape[0])
    _avg_distance = df_night_solo["trip_distance"].mean()
    _avg_fare = df_night_solo["fare_amount"].mean()
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
    df_night_solo, _ = load_and_process_data(month)
    hourly_counts = df_night_solo["pickup_hour"].value_counts().sort_index()
    resp = jsonify(hourly_counts.to_dict())
    return add_cache_headers(resp, max_age=300)

@app.route("/preview")
def preview():
    month = request.args.get("month", "2023-01")
    df_night_solo, _ = load_and_process_data(month)
    preview_data = json.loads(df_night_solo.head(20).to_json(orient="records"))
    resp = jsonify(preview_data)
    return add_cache_headers(resp, max_age=120)

@app.route("/predict-route-safety", methods=['POST'])
def predict_route_safety():
    try:
        print("Received request for route safety prediction")
        data = request.get_json()
        print(f"Request data: {data}")
        
        start_precinct = data.get('start_precinct')
        end_precinct = data.get('end_precinct')
        time = data.get('time', datetime.now().strftime("%H:%M"))
        
        print(f"Parameters: start={start_precinct}, end={end_precinct}, time={time}")
        
        if not all([start_precinct, end_precinct]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Convert time string to hour
        hour = int(time.split(":")[0])
        
        # Get the model
        model = get_safety_model()
        
        # Predict safety for start and end points
        start_safety = float(model.predict([[start_precinct, hour]])[0])
        end_safety = float(model.predict([[end_precinct, hour]])[0])
        
        # Calculate route safety
        route_safety = (start_safety + end_safety) / 2
        
        # Get safer hours
        safety_scores = []
        for h in range(24):
            safety = float((model.predict([[start_precinct, h]])[0] + 
                          model.predict([[end_precinct, h]])[0]) / 2)
            safety_scores.append({"hour": f"{h:02d}:00", "safety_score": safety})
        
        # Sort by safety score and get top 5
        safety_scores.sort(key=lambda x: x['safety_score'], reverse=True)
        safer_times = safety_scores[:5]
        
        response = {
            "route_safety_score": route_safety,
            "safety_label": get_safety_label(route_safety),
            "safer_times": safer_times,
            "start_point_safety": start_safety,
            "end_point_safety": end_safety
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-precinct-safety", methods=['GET'])
def get_precinct_safety():
    try:
        precinct = request.args.get('precinct')
        time = request.args.get('time', datetime.now().strftime("%H:%M"))
        
        if not precinct:
            return jsonify({"error": "Missing precinct parameter"}), 400
        
        # Convert parameters
        precinct = int(precinct)
        hour = int(time.split(":")[0])
        
        # Get the model
        model = get_safety_model()
        
        # Get safety score for the precinct
        safety_score = float(model.predict([[precinct, hour]])[0])
        
        response = {
            "precinct": precinct,
            "time": f"{hour:02d}:00",
            "safety_score": safety_score,
            "safety_label": get_safety_label(safety_score)
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    try:
        print("Initializing the application...")
        # Ensure model is loaded at startup
        model = get_safety_model()
        print("Model loaded successfully")
        # Warm cache for default month in background (optional)
        import threading
        def _warm():
            try:
                load_and_process_data("2023-01")
                print("Cache warm complete for 2023-01")
            except Exception as e:
                print(f"Cache warm failed: {e}")
        threading.Thread(target=_warm, daemon=True).start()
        print("Starting the Flask server...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error starting the application: {str(e)}")
        import traceback
        traceback.print_exc()