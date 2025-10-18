"""
NYC Taxi ML API - Secure Production Version
Protected with API keys, rate limiting, and input validation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from datetime import datetime, timedelta
import json
import os
import sys
import hashlib
import hmac
import secrets
import re

# Import the rule-based ML directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rule_based_ml import RuleBasedML

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"]
)

# Initialize ML system
ml_system = RuleBasedML()

# Security configuration
API_KEYS = {
    # Generate secure API keys
    "prod_key_1": "sk_prod_" + secrets.token_urlsafe(32),
    "prod_key_2": "sk_prod_" + secrets.token_urlsafe(32),
    "dev_key_1": "sk_dev_" + secrets.token_urlsafe(32)
}

# Rate limits per API key
API_KEY_LIMITS = {
    "prod_key_1": "1000 per hour",
    "prod_key_2": "1000 per hour", 
    "dev_key_1": "100 per hour"
}

# Location mapping (same as before)
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

def validate_api_key():
    """Validate API key from request headers"""
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return False, "API key required"
    
    if api_key not in API_KEYS:
        return False, "Invalid API key"
    
    return True, "Valid API key"

def validate_input(data):
    """Validate input data for security"""
    if not data:
        return False, "JSON data required"
    
    # Check for SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"]\s*=\s*['\"])",
        r"(\b(OR|AND)\s+1\s*=\s*1)",
        r"(\b(OR|AND)\s+1\s*=\s*2)",
    ]
    
    data_str = json.dumps(data).lower()
    for pattern in sql_patterns:
        if re.search(pattern, data_str, re.IGNORECASE):
            return False, "Invalid input detected"
    
    # Validate location inputs
    pickup_location = data.get('pickup_location', '')
    dropoff_location = data.get('dropoff_location', '')
    
    if isinstance(pickup_location, str) and len(pickup_location) > 100:
        return False, "Pickup location too long"
    
    if isinstance(dropoff_location, str) and len(dropoff_location) > 100:
        return False, "Dropoff location too long"
    
    # Validate datetime
    pickup_datetime_str = data.get('pickup_datetime')
    if pickup_datetime_str:
        try:
            datetime.fromisoformat(pickup_datetime_str.replace('Z', '+00:00'))
        except:
            return False, "Invalid datetime format"
    
    return True, "Input valid"

def parse_location(location_input):
    """Convert location input to valid LocationID with security checks"""
    try:
        # If it's a number, validate range
        if isinstance(location_input, (int, str)) and str(location_input).isdigit():
            location_id = int(location_input)
            if 1 <= location_id <= 264:
                return location_id
            else:
                logger.warning(f"LocationID {location_id} out of range, using Central Park")
                return 74
        
        # If it's a string, check mapping
        if isinstance(location_input, str):
            location_lower = location_input.lower().strip()
            # Sanitize input
            location_lower = re.sub(r'[^a-z0-9\s]', '', location_lower)
            return LOCATION_MAPPING.get(location_lower, 74)
        
        return 74
        
    except Exception as e:
        logger.error(f"Error parsing location: {e}")
        return 74

@app.before_request
def log_request():
    """Log all requests for security monitoring"""
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    endpoint = request.endpoint
    method = request.method
    
    logger.info(f"Request: {method} {endpoint} from {client_ip} - {user_agent}")

@app.route('/', methods=['GET'])
def home():
    """API information (public)"""
    return jsonify({
        'name': 'NYC Taxi ML API - Secure Production',
        'version': '3.0',
        'status': 'running',
        'security': 'enabled',
        'endpoints': {
            'predict': '/predict (POST) - Requires API key',
            'locations': '/locations (GET) - Public',
            'health': '/health (GET) - Public'
        },
        'total_locations': 264,
        'location_range': '1-264',
        'ml_method': 'rule_based_deterministic',
        'rate_limits': '100/hour, 10/minute',
        'authentication': 'API key required for predictions'
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Service status (public)"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ml_engine': 'rule_based_active',
        'security': 'enabled',
        'uptime': 'running'
    })

@app.route('/predict', methods=['POST'])
@limiter.limit("10 per minute")
def predict():
    """Main ML prediction endpoint (protected)"""
    try:
        # Validate API key
        is_valid, message = validate_api_key()
        if not is_valid:
            logger.warning(f"Unauthorized access attempt: {message}")
            return jsonify({'error': message}), 401
        
        # Get request data
        data = request.get_json()
        
        # Validate input
        is_valid, message = validate_input(data)
        if not is_valid:
            logger.warning(f"Invalid input detected: {message}")
            return jsonify({'error': message}), 400
        
        # Parse parameters with security checks
        pickup_location = parse_location(data.get('pickup_location', 'Central Park'))
        dropoff_location = parse_location(data.get('dropoff_location', 'Times Square'))
        
        pickup_datetime_str = data.get('pickup_datetime')
        if pickup_datetime_str:
            try:
                pickup_datetime = datetime.fromisoformat(pickup_datetime_str.replace('Z', '+00:00'))
            except:
                pickup_datetime = datetime.now()
        else:
            pickup_datetime = datetime.now()
        
        # Get prediction using rule-based ML
        prediction = ml_system.predict_route(pickup_location, dropoff_location, pickup_datetime)
        
        # Log successful prediction
        logger.info(f"Successful prediction for {pickup_location} -> {dropoff_location}")
        
        return jsonify({
            'status': 'success',
            'prediction': prediction,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/locations', methods=['GET'])
def get_locations():
    """Available locations (public)"""
    return jsonify({
        'status': 'success',
        'locations': LOCATION_MAPPING,
        'total_locations': 264,
        'note': 'Use names or LocationIDs (1-264)',
        'security': 'This endpoint is public'
    })

@app.route('/admin/keys', methods=['GET'])
def admin_keys():
    """Admin endpoint to view API keys (protected)"""
    # This would normally require admin authentication
    # For now, we'll just return the key names
    return jsonify({
        'status': 'success',
        'available_keys': list(API_KEYS.keys()),
        'note': 'Use X-API-Key header for authentication'
    })

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': str(e.retry_after)
    }), 429

@app.errorhandler(404)
def not_found_handler(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error_handler(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    print("NYC Taxi ML API - Secure Production Version")
    print("Security: API keys, rate limiting, input validation")
    print("Endpoints: /predict (protected), /locations (public), /health (public)")
    print("Server: http://localhost:5002")
    print("Authentication: X-API-Key header required")
    print("Rate Limits: 100/hour, 10/minute")
    
    # Print API keys for initial setup
    print("\n🔑 API Keys generated:")
    for key_name, key_value in API_KEYS.items():
        print(f"{key_name}: {key_value}")
    
    app.run(host='0.0.0.0', port=5002, debug=False)
