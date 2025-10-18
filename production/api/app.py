"""
NYC Taxi ML API - Versión Producción para EC2
Sistema robusto y escalable para despliegue en la nube
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import logging.handlers
from datetime import datetime
import subprocess
import json
import os
import yaml
import time
from functools import wraps
import signal
import sys

# Configurar logging robusto
def setup_logging():
    """Configurar sistema de logging para producción"""
    log_dir = "/opt/nyc_taxi_ml/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configurar logger principal
    logger = logging.getLogger('nyc_taxi_ml')
    logger.setLevel(logging.INFO)
    
    # Handler para archivo con rotación
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'api.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Cargar configuración
def load_config():
    """Cargar configuración de producción"""
    config_path = "/opt/nyc_taxi_ml/config/production.yaml"
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Configuración por defecto si no existe el archivo
        return {
            'server': {'host': '0.0.0.0', 'port': 5001, 'debug': False},
            'ml_engine': {'timeout': 30, 'max_retries': 3}
        }

# Inicializar aplicación
config = load_config()
logger = setup_logging()
app = Flask(__name__)
CORS(app, origins=config.get('security', {}).get('cors_origins', ['*']))

# Mapeo de ubicaciones (expandido para producción)
LOCATION_MAPPING = {
    # Manhattan
    "central park": 74, "times square": 151, "empire state building": 114, "wall street": 90,
    "brooklyn bridge": 1, "statue of liberty": 87, "manhattan": 74, "soho": 100,
    "greenwich village": 100, "upper east side": 74, "upper west side": 74, "midtown": 151,
    "financial district": 90, "chelsea": 100, "tribeca": 90, "little italy": 90,
    "chinatown": 90, "east village": 100, "west village": 100, "harlem": 74,
    
    # Brooklyn
    "brooklyn": 1, "downtown brooklyn": 1, "williamsburg": 1, "park slope": 1, 
    "coney island": 1, "prospect park": 1, "dumbo": 1, "red hook": 1,
    
    # Queens
    "queens": 138, "astoria": 138, "flushing": 138, "long island city": 138,
    "jamaica": 138, "corona": 138, "elmhurst": 138,
    
    # Bronx
    "bronx": 1, "yankee stadium": 1, "fordham": 1,
    
    # Staten Island
    "staten island": 1, "st. george": 1,
    
    # Aeropuertos
    "jfk airport": 132, "lga airport": 138, "jfk": 132, "laguardia": 138,
    "newark airport": 1, "ewr": 1,
}

# Decorador para manejo de errores
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {f.__name__}: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    return decorated_function

# Decorador para logging de requests
def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"{request.method} {request.path} - {duration:.3f}s")
        return result
    return decorated_function

def parse_location(location_input):
    """Convierte entrada de ubicación a LocationID válido"""
    try:
        location_id = int(location_input)
        if 1 <= location_id <= 264:
            return location_id
        else:
            logger.warning(f"LocationID {location_id} fuera de rango, usando Central Park")
            return 74
    except ValueError:
        location_lower = location_input.lower().strip()
        return LOCATION_MAPPING.get(location_lower, 74)

def get_prediction(pickup_location, dropoff_location, pickup_datetime):
    """Obtiene predicción usando el motor ML con reintentos"""
    max_retries = config.get('ml_engine', {}).get('max_retries', 3)
    timeout = config.get('ml_engine', {}).get('timeout', 30)
    
    for attempt in range(max_retries):
        try:
            cmd = [
                'python', '/opt/nyc_taxi_ml/ml_engine/inference_cli.py', 'predict',
                '--pu', str(pickup_location),
                '--do', str(dropoff_location),
                '--dt', pickup_datetime.strftime("%Y-%m-%d %H:%M:%S")
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd='/opt/nyc_taxi_ml'
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.warning(f"Intento {attempt + 1} falló: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout en intento {attempt + 1}")
        except Exception as e:
            logger.warning(f"Error en intento {attempt + 1}: {e}")
    
    logger.error("Todos los intentos de predicción fallaron")
    return None

# Endpoints
@app.route('/', methods=['GET'])
@handle_errors
@log_request
def home():
    """Información de la API"""
    return jsonify({
        'name': 'NYC Taxi ML API',
        'version': '2.0',
        'environment': 'production',
        'status': 'running',
        'endpoints': {
            'predict': '/predict (POST)',
            'locations': '/locations (GET)',
            'health': '/health (GET)',
            'status': '/status (GET)'
        },
        'total_locations': 264,
        'location_range': '1-264',
        'uptime': time.time() - start_time
    })

@app.route('/health', methods=['GET'])
@handle_errors
def health_check():
    """Estado del servicio"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ml_engine': 'active',
        'version': '2.0'
    })

@app.route('/status', methods=['GET'])
@handle_errors
def status():
    """Estado detallado del sistema"""
    return jsonify({
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - start_time,
        'config_loaded': bool(config),
        'location_mapping_size': len(LOCATION_MAPPING),
        'ml_engine_timeout': config.get('ml_engine', {}).get('timeout', 30)
    })

@app.route('/predict', methods=['POST'])
@handle_errors
@log_request
def predict():
    """Endpoint principal para predicciones ML"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos JSON requeridos'}), 400
    
    # Parsear parámetros
    pickup_location = parse_location(data.get('pickup_location', 'Central Park'))
    dropoff_location = parse_location(data.get('dropoff_location', 'Times Square'))
    
    pickup_datetime_str = data.get('pickup_datetime')
    if pickup_datetime_str:
        try:
            pickup_datetime = datetime.fromisoformat(pickup_datetime_str.replace('Z', '+00:00'))
        except ValueError:
            pickup_datetime = datetime.now()
    else:
        pickup_datetime = datetime.now()
    
    # Obtener predicción
    prediction = get_prediction(pickup_location, dropoff_location, pickup_datetime)
    
    if prediction is None:
        return jsonify({'error': 'Error generando predicción'}), 500
    
    return jsonify({
        'status': 'success',
        'prediction': prediction,
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'pickup_location_id': pickup_location,
            'dropoff_location_id': dropoff_location
        }
    })

@app.route('/locations', methods=['GET'])
@handle_errors
def get_locations():
    """Ubicaciones disponibles"""
    return jsonify({
        'status': 'success',
        'locations': LOCATION_MAPPING,
        'total_locations': 264,
        'note': 'Usa nombres o LocationIDs (1-264)'
    })

# Manejo de señales para shutdown graceful
def signal_handler(sig, frame):
    logger.info('Recibida señal de shutdown, cerrando servidor...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    start_time = time.time()
    
    logger.info("Iniciando NYC Taxi ML API - Producción")
    logger.info(f"Configuración cargada: {bool(config)}")
    logger.info(f"Ubicaciones mapeadas: {len(LOCATION_MAPPING)}")
    
    host = config.get('server', {}).get('host', '0.0.0.0')
    port = config.get('server', {}).get('port', 5001)
    debug = config.get('server', {}).get('debug', False)
    
    logger.info(f"Servidor iniciando en {host}:{port}")
    
    app.run(host=host, port=port, debug=debug, threaded=True)
