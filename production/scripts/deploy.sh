#!/bin/bash

# Script de despliegue para EC2 - NYC Taxi ML API
# Este script prepara el servidor EC2 para ejecutar la API de ML

set -e  # Salir si hay errores

echo "🚀 Iniciando despliegue de NYC Taxi ML API en EC2..."

# Variables
APP_NAME="nyc_taxi_ml"
APP_DIR="/opt/nyc_taxi_ml"
SERVICE_USER="nyc_taxi"
PYTHON_VERSION="3.9"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verificar que estamos en Ubuntu/Debian
if ! command -v apt-get &> /dev/null; then
    error "Este script está diseñado para Ubuntu/Debian. Para otras distribuciones, ajusta los comandos de instalación."
fi

# Actualizar sistema
log "Actualizando sistema..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Instalar dependencias del sistema
log "Instalando dependencias del sistema..."
sudo apt-get install -y \
    python3.9 \
    python3.9-dev \
    python3-pip \
    python3.9-venv \
    nginx \
    supervisor \
    git \
    curl \
    wget \
    unzip \
    build-essential

# Crear usuario para la aplicación
log "Creando usuario de servicio..."
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd -r -s /bin/false -d $APP_DIR $SERVICE_USER
fi

# Crear directorios
log "Creando estructura de directorios..."
sudo mkdir -p $APP_DIR/{api,ml_engine,config,data,models,logs,scripts}
sudo chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR

# Crear entorno virtual
log "Creando entorno virtual de Python..."
sudo -u $SERVICE_USER python3.9 -m venv $APP_DIR/venv
sudo -u $SERVICE_USER $APP_DIR/venv/bin/pip install --upgrade pip

# Instalar dependencias de Python
log "Instalando dependencias de Python..."
sudo -u $SERVICE_USER $APP_DIR/venv/bin/pip install \
    flask \
    flask-cors \
    pandas \
    numpy \
    scikit-learn \
    lightgbm \
    xgboost \
    joblib \
    pyarrow \
    PyYAML \
    requests

# Configurar Nginx
log "Configurando Nginx..."
sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        access_log off;
    }
}
EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Configurar Supervisor para la API
log "Configurando Supervisor..."
sudo tee /etc/supervisor/conf.d/$APP_NAME.conf > /dev/null <<EOF
[program:$APP_NAME]
command=$APP_DIR/venv/bin/python $APP_DIR/api/app.py
directory=$APP_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$APP_DIR/logs/supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="$APP_DIR/venv/bin"
EOF

# Recargar configuración de Supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Configurar firewall
log "Configurando firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Crear script de inicio
log "Creando script de inicio..."
sudo tee $APP_DIR/scripts/start.sh > /dev/null <<EOF
#!/bin/bash
cd $APP_DIR
source venv/bin/activate
python api/app.py
EOF

sudo chmod +x $APP_DIR/scripts/start.sh
sudo chown $SERVICE_USER:$SERVICE_USER $APP_DIR/scripts/start.sh

# Crear script de parada
log "Creando script de parada..."
sudo tee $APP_DIR/scripts/stop.sh > /dev/null <<EOF
#!/bin/bash
sudo supervisorctl stop $APP_NAME
EOF

sudo chmod +x $APP_DIR/scripts/stop.sh

# Crear script de logs
log "Creando script de logs..."
sudo tee $APP_DIR/scripts/logs.sh > /dev/null <<EOF
#!/bin/bash
tail -f $APP_DIR/logs/api.log
EOF

sudo chmod +x $APP_DIR/scripts/logs.sh

log "✅ Despliegue completado!"
log "📁 Directorio de la aplicación: $APP_DIR"
log "🔧 Comandos útiles:"
log "   - Iniciar: sudo supervisorctl start $APP_NAME"
log "   - Parar: sudo supervisorctl stop $APP_NAME"
log "   - Estado: sudo supervisorctl status $APP_NAME"
log "   - Logs: $APP_DIR/scripts/logs.sh"
log "   - Reiniciar: sudo supervisorctl restart $APP_NAME"

warn "⚠️  IMPORTANTE: Necesitas subir los archivos de la aplicación y modelos ML a $APP_DIR"
warn "⚠️  IMPORTANTE: Configura los datos en $APP_DIR/data/"
warn "⚠️  IMPORTANTE: Coloca los modelos entrenados en $APP_DIR/models/"

echo ""
log "🌐 La API estará disponible en: http://$(curl -s ifconfig.me)/"
log "🔍 Health check: http://$(curl -s ifconfig.me)/health"
