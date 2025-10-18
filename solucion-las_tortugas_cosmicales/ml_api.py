#!/usr/bin/env python3
"""
NYC Taxi Safety ML API Server
Sistema ML basado en reglas determinísticas
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
CORS(app)

# Load zone data
def load_zone_data():
    """Load zone information"""
    try:
        # Try to load from ML directory
        zone_file = os.path.join(os.path.dirname(__file__), 'ML', 'LocationID_to_pretinct.csv')
        if os.path.exists(zone_file):
            zones_df = pd.read_csv(zone_file)
            return zones_df
        else:
            # Fallback: create basic zone data
            return create_fallback_zones()
    except Exception as e:
        print(f"Error loading zone data: {e}")
        return create_fallback_zones()

def create_fallback_zones():
    """Create fallback zone data"""
    zones = []
    for i in range(1, 264):  # NYC has zones 1-263
        zones.append({
            'LocationID': i,
            'zone_name': f'Zone {i}',
            'borough': 'Unknown'
        })
    return pd.DataFrame(zones)

# Load zone data
zones_df = load_zone_data()

def get_zone_info(zone_id):
    """Get zone information"""
    zone_info = zones_df[zones_df['LocationID'] == zone_id]
    if not zone_info.empty:
        return zone_info.iloc[0].to_dict()
    return {
        'LocationID': zone_id,
        'zone_name': f'Zone {zone_id}',
        'borough': 'Unknown'
    }

def calculate_rule_based_safety(pickup_zone, dropoff_zone, pickup_hour):
    """Calculate safety based on rules"""
    
    # Get zone info
    pickup_info = get_zone_info(pickup_zone)
    dropoff_info = get_zone_info(dropoff_zone)
    
    # Base safety score
    base_safety = 0.5
    
    # Borough-based adjustments
    borough_safety = {
        'Manhattan': 0.8,
        'Brooklyn': 0.6,
        'Queens': 0.7,
        'Bronx': 0.4,
        'Staten Island': 0.8
    }
    
    pickup_borough = pickup_info.get('borough', 'Unknown')
    dropoff_borough = dropoff_info.get('borough', 'Unknown')
    
    # Adjust based on pickup borough
    if pickup_borough in borough_safety:
        base_safety = borough_safety[pickup_borough]
    
    # Time-based adjustments
    if 6 <= pickup_hour <= 10:  # Morning rush
        time_factor = 0.9
    elif 11 <= pickup_hour <= 16:  # Daytime
        time_factor = 0.95
    elif 17 <= pickup_hour <= 20:  # Evening rush
        time_factor = 0.85
    elif 21 <= pickup_hour <= 23:  # Evening
        time_factor = 0.7
    else:  # Late night/early morning
        time_factor = 0.6
    
    # Calculate final safety
    final_safety = base_safety * time_factor
    
    # Ensure safety is between 0.1 and 0.99
    final_safety = max(0.1, min(0.99, final_safety))
    
    return final_safety

def generate_hourly_safety_data(zone_id):
    """Generate hourly safety data for a zone"""
    zone_info = get_zone_info(zone_id)
    borough = zone_info.get('borough', 'Unknown')
    
    hourly_data = []
    for hour in range(24):
        safety = calculate_rule_based_safety(zone_id, zone_id, hour)
        hourly_data.append({
            'hour': hour,
            'safety_percent': round(safety * 100, 1),
            'time_label': f"{hour:02d}:00 - {(hour+1)%24:02d}:00"
        })
    
    return hourly_data

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'NYC Taxi ML API',
        'version': '2.0',
        'method': 'rule_based_deterministic'
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Main prediction endpoint"""
    try:
        data = request.get_json()
        
        # Extract parameters
        pickup_location_id = data.get('pickup_location_id')
        dropoff_location_id = data.get('dropoff_location_id', pickup_location_id)
        pickup_datetime = data.get('pickup_datetime', datetime.now().isoformat())
        
        # Parse datetime
        try:
            dt = datetime.fromisoformat(pickup_datetime.replace('Z', '+00:00'))
            pickup_hour = dt.hour
        except:
            pickup_hour = datetime.now().hour
        
        # Calculate safety
        safety_score = calculate_rule_based_safety(
            pickup_location_id, 
            dropoff_location_id, 
            pickup_hour
        )
        
        # Get zone info
        pickup_info = get_zone_info(pickup_location_id)
        dropoff_info = get_zone_info(dropoff_location_id)
        
        # Generate hourly safety data
        hourly_safety = generate_hourly_safety_data(pickup_location_id)
        
        # Find safest hours (top 3)
        safest_hours = sorted(hourly_safety, key=lambda x: x['safety_percent'], reverse=True)[:3]
        
        # Calculate average fare (rule-based)
        base_fare = 15.0
        if pickup_info.get('borough') == 'Manhattan':
            base_fare += 5.0
        elif pickup_info.get('borough') == 'Brooklyn':
            base_fare += 2.0
        
        # Time-based fare adjustment
        if 6 <= pickup_hour <= 10 or 17 <= pickup_hour <= 20:  # Rush hours
            base_fare *= 1.2
        
        # Distance-based fare (simplified)
        if pickup_location_id != dropoff_location_id:
            base_fare += 8.0
        
        response = {
            'prediction': {
                'pickup_location_id': pickup_location_id,
                'dropoff_location_id': dropoff_location_id,
                'pickup_datetime': pickup_datetime,
                'avg_fare_usd': round(base_fare, 2),
                'safety_index_percent': round(safety_score * 100, 1),
                'safety_by_hours': hourly_safety,
                'safest_times': safest_hours,
                'prediction_metadata': {
                    'pickup_zone': pickup_info.get('zone_name', f'Zone {pickup_location_id}'),
                    'pickup_borough': pickup_info.get('borough', 'Unknown'),
                    'dropoff_zone': dropoff_info.get('zone_name', f'Zone {dropoff_location_id}'),
                    'dropoff_borough': dropoff_info.get('borough', 'Unknown'),
                    'method': 'rule_based_deterministic',
                    'model_version': '2.0',
                    'prediction_time': datetime.now().isoformat()
                }
            },
            'status': 'success'
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/zones', methods=['GET'])
def get_zones():
    """Get available zones"""
    try:
        zones = zones_df.to_dict(orient='records')
        return jsonify({
            'zones': zones,
            'total': len(zones),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

if __name__ == '__main__':
    print("Starting NYC Taxi ML API Server...")
    print("Method: Rule-based Deterministic")
    print("Version: 2.0")
    app.run(debug=True, host='0.0.0.0', port=5002)
