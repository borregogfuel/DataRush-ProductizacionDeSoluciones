# NYC Taxi ML API - Producción EC2

Sistema de Machine Learning para predicción de precio y seguridad de viajes en taxi en NYC, optimizado para despliegue en EC2.

## 🏗️ Estructura del Proyecto

```
production/
├── api/
│   └── app.py                 # API Flask optimizada para producción
├── ml_engine/
│   └── inference_cli.py       # Motor ML optimizado
├── config/
│   └── production.yaml        # Configuración de producción
├── scripts/
│   ├── deploy.sh              # Script de despliegue en EC2
│   └── setup_data.sh          # Script de configuración de datos
├── Dockerfile                 # Contenedor Docker
├── docker-compose.yml         # Orquestación local
└── README.md                  # Este archivo
```

## 🚀 Despliegue en EC2

### 1. Preparar Instancia EC2

```bash
# Conectar a tu instancia EC2
ssh -i tu-key.pem ubuntu@tu-instancia.amazonaws.com

# Clonar el repositorio
git clone https://github.com/tu-usuario/nyc-taxi-ml.git
cd nyc-taxi-ml
```

### 2. Ejecutar Script de Despliegue

```bash
# Hacer ejecutable y correr
chmod +x production/scripts/deploy.sh
sudo ./production/scripts/deploy.sh
```

### 3. Configurar Datos y Modelos

```bash
# Entrenar modelos localmente primero
python -m src.pipeline train

# Configurar datos en EC2
chmod +x production/scripts/setup_data.sh
sudo ./production/scripts/setup_data.sh
```

### 4. Iniciar Servicio

```bash
# Iniciar la API
sudo supervisorctl start nyc_taxi_ml

# Verificar estado
sudo supervisorctl status nyc_taxi_ml

# Ver logs
tail -f /opt/nyc_taxi_ml/logs/api.log
```

## 🐳 Despliegue con Docker

### Desarrollo Local

```bash
# Construir y ejecutar
cd production
docker-compose up --build

# La API estará disponible en http://localhost:5001
```

### Producción

```bash
# Construir imagen
docker build -f production/Dockerfile -t nyc-taxi-ml:latest .

# Ejecutar contenedor
docker run -d \
  --name nyc-taxi-ml \
  -p 5001:5001 \
  -v /opt/nyc_taxi_ml/data:/opt/nyc_taxi_ml/data:ro \
  -v /opt/nyc_taxi_ml/models:/opt/nyc_taxi_ml/models:ro \
  nyc-taxi-ml:latest
```

## 🔧 Comandos de Administración

### Supervisor (Sistema de Servicios)

```bash
# Controlar servicio
sudo supervisorctl start nyc_taxi_ml
sudo supervisorctl stop nyc_taxi_ml
sudo supervisorctl restart nyc_taxi_ml
sudo supervisorctl status nyc_taxi_ml

# Ver logs
sudo supervisorctl tail -f nyc_taxi_ml
```

### Scripts Útiles

```bash
# Ver logs en tiempo real
/opt/nyc_taxi_ml/scripts/logs.sh

# Probar API
python /opt/nyc_taxi_ml/test_api.py

# Reiniciar servicio
/opt/nyc_taxi_ml/scripts/stop.sh
sudo supervisorctl start nyc_taxi_ml
```

## 📊 Monitoreo

### Health Checks

```bash
# Health check básico
curl http://localhost:5001/health

# Estado detallado
curl http://localhost:5001/status

# A través de Nginx
curl http://tu-dominio.com/health
```

### Logs

```bash
# Logs de la API
tail -f /opt/nyc_taxi_ml/logs/api.log

# Logs de Supervisor
tail -f /opt/nyc_taxi_ml/logs/supervisor.log

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🔒 Seguridad

### Firewall

```bash
# Configurar UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### SSL/HTTPS (Opcional)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com
```

## 📈 Escalabilidad

### Load Balancer

Para múltiples instancias EC2:

```bash
# Configurar Application Load Balancer en AWS
# Target Group: puerto 5001
# Health Check: /health
# Auto Scaling Group: 2-10 instancias
```

### Monitoreo Avanzado

```bash
# Instalar CloudWatch Agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configurar métricas personalizadas
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **API no responde**
   ```bash
   sudo supervisorctl status nyc_taxi_ml
   sudo supervisorctl restart nyc_taxi_ml
   ```

2. **Modelos no encontrados**
   ```bash
   ls -la /opt/nyc_taxi_ml/models/
   sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/models/
   ```

3. **Datos no encontrados**
   ```bash
   ls -la /opt/nyc_taxi_ml/data/
   sudo ./production/scripts/setup_data.sh
   ```

4. **Puerto ocupado**
   ```bash
   sudo netstat -tlnp | grep :5001
   sudo supervisorctl stop nyc_taxi_ml
   ```

### Logs de Debug

```bash
# Habilitar debug en producción.yaml
logging:
  level: "DEBUG"

# Reiniciar servicio
sudo supervisorctl restart nyc_taxi_ml
```

## 📞 Soporte

- **Documentación**: Este README
- **Logs**: `/opt/nyc_taxi_ml/logs/`
- **Configuración**: `/opt/nyc_taxi_ml/config/production.yaml`
- **Scripts**: `/opt/nyc_taxi_ml/scripts/`

## 🎯 Endpoints de la API

- `GET /` - Información de la API
- `GET /health` - Health check
- `GET /status` - Estado detallado
- `GET /locations` - Ubicaciones disponibles
- `POST /predict` - Predicción ML

### Ejemplo de Uso

```bash
curl -X POST http://tu-dominio.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_location": "Central Park",
    "dropoff_location": "Times Square",
    "pickup_datetime": "2025-10-17 18:30:00"
  }'
```

**¡Sistema listo para producción!** 🚀
