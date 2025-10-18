# NYC Taxi ML API

Sistema de Machine Learning para predicción de precio y seguridad de viajes en taxi en NYC.

## 🚀 Inicio Rápido

### Instalación
```bash
pip install flask flask-cors
```

### Ejecutar API
```bash
python api.py
```

### Probar API
```bash
# Health check
curl http://localhost:5000/health

# Predicción
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"pickup_location": "Central Park", "dropoff_location": "Times Square"}'
```

## 📍 Ubicaciones Soportadas

- **Nombres**: Central Park, Times Square, JFK Airport, etc.
- **LocationIDs**: Cualquier número del 1 al 264
- **Total**: 264 ubicaciones de NYC

## 🔧 Endpoints

- `POST /predict` - Predicción completa
- `GET /locations` - Ubicaciones disponibles  
- `GET /health` - Estado del servicio

## 📊 Respuesta de Predicción

```json
{
  "status": "success",
  "prediction": {
    "pickup_location_id": 74,
    "dropoff_location_id": 151,
    "safety_index_percent": 75.2,
    "avg_fare_usd": 15.50,
    "safety_by_hours": [...],
    "safest_times": [...]
  }
}
```

## 🎯 Integración Frontend

```javascript
fetch('http://localhost:5000/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        pickup_location: "Central Park",
        dropoff_location: "Times Square",
        pickup_datetime: "2025-10-17 18:30:00"
    })
})
.then(response => response.json())
.then(data => {
    console.log('Safety:', data.prediction.safety_index_percent + '%');
    console.log('Fare:', '$' + data.prediction.avg_fare_usd);
});
```

## 📁 Archivos Principales

- `api.py` - API principal
- `inference_cli.py` - Motor ML
- `config.yaml` - Configuración
- `src/` - Módulos ML (referencia)
