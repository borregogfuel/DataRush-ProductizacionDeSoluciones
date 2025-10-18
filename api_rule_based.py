"""
NYC Taxi ML API - Rule-Based Version
Direct integration without subprocess
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import json
import os
import sys

# Import the rule-based ML directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rule_based_ml import RuleBasedML

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Initialize ML system
ml_system = RuleBasedML()

# Location mapping
LOCATION_MAPPING = {
    # Manhattan
    "central park": 74, "times square": 151, "empire state building": 114, "wall street": 90,
    "brooklyn bridge": 1, "statue of liberty": 87, "manhattan": 74, "soho": 100,
    "greenwich village": 100, "upper east side": 74, "upper west side": 74, "midtown": 151,
    "financial district": 90, "chelsea": 100, "tribeca": 90,
    
    # Brooklyn
    "brooklyn": 1, "downtown brooklyn": 1, "williamsburg": 1, "park slope": 1, "coney island": 1,
    
    # Queens
    "queens": 138, "astoria": 138, "flushing": 138, "long island city": 138,
    
    # Bronx
    "bronx": 1, "yankee stadium": 1,
    
    # Staten Island
    "staten island": 1,
    
    # Airports
    "jfk airport": 132, "lga airport": 138, "jfk": 132, "laguardia": 138,
}

def parse_location(location_input):
    """Convert location input to valid LocationID"""
    try:
        location_id = int(location_input)
        if 1 <= location_id <= 264:
            return location_id
        else:
            logger.warning(f"LocationID {location_id} out of range, using Central Park")
            return 74
    except ValueError:
        location_lower = location_input.lower().strip()
        return LOCATION_MAPPING.get(location_lower, 74)

@app.route('/', methods=['GET'])
def home():
    """API information"""
    return jsonify({
        'name': 'NYC Taxi ML API - Rule-Based',
        'version': '2.0',
        'status': 'running',
        'endpoints': {
            'predict': '/predict (POST)',
            'locations': '/locations (GET)',
            'health': '/health (GET)'
        },
        'total_locations': 264,
        'location_range': '1-264',
        'ml_method': 'rule_based_deterministic'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Service status"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ml_engine': 'rule_based_active'
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Main ML prediction endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Parse parameters
        pickup_location = parse_location(data.get('pickup_location', 'Central Park'))
        dropoff_location = parse_location(data.get('dropoff_location', 'Times Square'))
        
        pickup_datetime_str = data.get('pickup_datetime')
        if pickup_datetime_str:
            pickup_datetime = datetime.fromisoformat(pickup_datetime_str.replace('Z', '+00:00'))
        else:
            pickup_datetime = datetime.now()
        
        # Get prediction using rule-based ML
        prediction = ml_system.predict_route(pickup_location, dropoff_location, pickup_datetime)
        
        return jsonify({
            'status': 'success',
            'prediction': prediction
        })
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/locations', methods=['GET'])
def get_locations():
    """Available locations"""
    return jsonify({
        'status': 'success',
        'locations': LOCATION_MAPPING,
        'total_locations': 264,
        'note': 'Use names or LocationIDs (1-264)'
    })

if __name__ == '__main__':
    print("NYC Taxi ML API - Rule-Based Version")
    print("Endpoints: /predict, /locations, /health")
    print("Server: http://localhost:5001")
    print("Support: All NYC LocationIDs (1-264)")
    print("ML Method: Rule-based deterministic")
    
    app.run(host='0.0.0.0', port=5002, debug=False)
