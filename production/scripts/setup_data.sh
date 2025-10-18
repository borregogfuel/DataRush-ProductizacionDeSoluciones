#!/bin/bash

# Script para configurar datos en EC2
# Este script ayuda a subir y configurar los datos necesarios

set -e

APP_DIR="/opt/nyc_taxi_ml"
SERVICE_USER="nyc_taxi"

log() {
    echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')] $1\033[0m"
}

warn() {
    echo -e "\033[1;33m[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1\033[0m"
}

# Función para subir archivos
upload_file() {
    local source_file="$1"
    local dest_path="$2"
    
    if [ -f "$source_file" ]; then
        sudo cp "$source_file" "$dest_path"
        sudo chown $SERVICE_USER:$SERVICE_USER "$dest_path"
        log "Subido: $source_file -> $dest_path"
    else
        warn "Archivo no encontrado: $source_file"
    fi
}

log "📁 Configurando datos en EC2..."

# Crear directorios si no existen
sudo mkdir -p $APP_DIR/{data,models,config}

# Subir archivos de configuración
log "Subiendo archivos de configuración..."
upload_file "production/config/production.yaml" "$APP_DIR/config/production.yaml"

# Subir archivos de datos
log "Subiendo archivos de datos..."
upload_file "solucion-las_tortugas_cosmicales/ML/LocationID_to_pretinct.csv" "$APP_DIR/data/LocationID_to_pretinct.csv"
upload_file "solucion-las_tortugas_cosmicales/ML/crime_data/NYPD_Complaint_Data_Historic_20251015.csv" "$APP_DIR/data/NYPD_Complaint_Data_Historic_20251015.csv"

# Subir modelos (si existen)
log "Subiendo modelos ML..."
if [ -d "models" ]; then
    sudo cp -r models/* $APP_DIR/models/
    sudo chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR/models/
    log "Modelos subidos exitosamente"
else
    warn "Directorio 'models' no encontrado. Necesitas entrenar los modelos primero."
fi

# Subir código de la aplicación
log "Subiendo código de la aplicación..."
upload_file "production/api/app.py" "$APP_DIR/api/app.py"
upload_file "production/ml_engine/inference_cli.py" "$APP_DIR/ml_engine/inference_cli.py"

# Crear archivo de requirements
log "Creando requirements.txt..."
cat > /tmp/requirements.txt <<EOF
flask==2.3.3
flask-cors==4.0.0
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
lightgbm==4.0.0
xgboost==1.7.6
joblib==1.3.2
pyarrow==12.0.1
PyYAML==6.0.1
requests==2.31.0
EOF

sudo cp /tmp/requirements.txt $APP_DIR/requirements.txt
sudo chown $SERVICE_USER:$SERVICE_USER $APP_DIR/requirements.txt

# Instalar dependencias
log "Instalando dependencias..."
sudo -u $SERVICE_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Crear archivo de prueba
log "Creando script de prueba..."
sudo tee $APP_DIR/test_api.py > /dev/null <<EOF
#!/usr/bin/env python3
import requests
import json

def test_api():
    base_url = "http://localhost:5001"
    
    print("🧪 Probando API de ML...")
    
    # Test 1: Health check
    print("\n1. Health Check:")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Prediction
    print("\n2. Prediction:")
    try:
        payload = {
            "pickup_location": "Central Park",
            "dropoff_location": "Times Square",
            "pickup_datetime": "2025-10-17 18:30:00"
        }
        response = requests.post(f"{base_url}/predict", json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            prediction = data['prediction']
            print(f"Safety Index: {prediction['safety_index_percent']}%")
            print(f"Average Fare: \${prediction['avg_fare_usd']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
EOF

sudo chmod +x $APP_DIR/test_api.py
sudo chown $SERVICE_USER:$SERVICE_USER $APP_DIR/test_api.py

# Verificar permisos
log "Verificando permisos..."
sudo chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

log "✅ Configuración de datos completada!"
log "🔧 Próximos pasos:"
log "   1. Entrenar modelos: python -m src.pipeline train"
log "   2. Copiar modelos a $APP_DIR/models/"
log "   3. Iniciar servicio: sudo supervisorctl start nyc_taxi_ml"
log "   4. Probar API: python $APP_DIR/test_api.py"

warn "⚠️  Asegúrate de que todos los modelos estén en $APP_DIR/models/"
warn "⚠️  Verifica que los datos estén en $APP_DIR/data/"
