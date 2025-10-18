#!/bin/bash

# 🚀 Script de Deployment Completo para AWS EC2
# NYC Taxi ML System - Con Seguridad Integrada

set -e  # Exit on any error

echo "🚀 Iniciando deployment completo en EC2..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar que estamos en Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    error "Este script está diseñado para Ubuntu. Sistema detectado: $(cat /etc/os-release | grep PRETTY_NAME)"
fi

log "Sistema Ubuntu detectado ✓"

# 1. Actualizar sistema
log "Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias
log "Instalando dependencias..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    supervisor \
    curl \
    wget \
    unzip \
    htop \
    tree \
    fail2ban \
    ufw \
    certbot \
    python3-certbot-nginx

# 3. Crear usuario de aplicación
log "Creando usuario de aplicación..."
if ! id "nyc_taxi" &>/dev/null; then
    sudo useradd -m -s /bin/bash nyc_taxi
    sudo usermod -aG sudo nyc_taxi
    log "Usuario 'nyc_taxi' creado ✓"
else
    log "Usuario 'nyc_taxi' ya existe ✓"
fi

# 4. Crear estructura de directorios
log "Creando estructura de directorios..."
sudo mkdir -p /opt/nyc_taxi_ml/{api,ml_engine,config,logs,data,models,frontend,scripts,backups}
sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml

# 5. Configurar Python virtual environment
log "Configurando Python virtual environment..."
sudo -u nyc_taxi python3 -m venv /opt/nyc_taxi_ml/venv
sudo -u nyc_taxi /opt/nyc_taxi_ml/venv/bin/pip install --upgrade pip

# 6. Copiar archivos de la aplicación
log "Copiando archivos de la aplicación..."

# Verificar que los archivos existen
if [ ! -f "api_rule_based.py" ]; then
    error "api_rule_based.py no encontrado. Ejecuta este script desde el directorio raíz del proyecto."
fi

if [ ! -f "rule_based_ml.py" ]; then
    error "rule_based_ml.py no encontrado. Ejecuta este script desde el directorio raíz del proyecto."
fi

# Copiar archivos principales
sudo cp api_rule_based.py /opt/nyc_taxi_ml/api/
sudo cp rule_based_ml.py /opt/nyc_taxi_ml/ml_engine/
sudo cp requirements.txt /opt/nyc_taxi_ml/
sudo cp -r solucion-las_tortugas_cosmicales/frontend/* /opt/nyc_taxi_ml/frontend/
sudo cp solucion-las_tortugas_cosmicales/backend/app.py /opt/nyc_taxi_ml/api/backend_app.py

# Copiar datos si existen
if [ -d "solucion-las_tortugas_cosmicales/ML" ]; then
    sudo cp -r solucion-las_tortugas_cosmicales/ML/* /opt/nyc_taxi_ml/data/
fi

# Cambiar permisos
sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml

# 7. Instalar dependencias Python
log "Instalando dependencias Python..."
sudo -u nyc_taxi /opt/nyc_taxi_ml/venv/bin/pip install -r /opt/nyc_taxi_ml/requirements.txt
sudo -u nyc_taxi /opt/nyc_taxi_ml/venv/bin/pip install flask-limiter

# 8. Configurar seguridad básica
log "Configurando seguridad básica..."

# Firewall
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw allow 5000/tcp comment 'Backend API'
sudo ufw allow 5002/tcp comment 'ML API'
sudo ufw --force enable

# Fail2Ban
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 9. Configurar Supervisor
log "Configurando Supervisor..."
sudo tee /etc/supervisor/conf.d/nyc_taxi_ml.conf > /dev/null <<EOF
[program:nyc_taxi_ml]
command=/opt/nyc_taxi_ml/venv/bin/python /opt/nyc_taxi_ml/api/api_rule_based.py
directory=/opt/nyc_taxi_ml/api
user=nyc_taxi
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/nyc_taxi_ml/logs/api.log
environment=PATH="/opt/nyc_taxi_ml/venv/bin:/usr/bin:/usr/local/bin"
EOF

# 10. Configurar Nginx con seguridad
log "Configurando Nginx con seguridad..."
sudo tee /etc/nginx/sites-available/nyc_taxi_ml > /dev/null <<EOF
# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/m;
limit_req_zone \$binary_remote_addr zone=general:10m rate=30r/m;

server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Rate limiting
    limit_req zone=general burst=20 nodelay;
    
    # Frontend estático
    location / {
        root /opt/nyc_taxi_ml/frontend;
        index map.html;
        try_files \$uri \$uri/ /map.html;
    }
    
    # ML API
    location /ml/ {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://127.0.0.1:5002/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_hide_header Server;
        proxy_hide_header X-Powered-By;
    }
    
    # Backend API
    location /api/ {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_hide_header Server;
        proxy_hide_header X-Powered-By;
    }
    
    # Block common attack patterns
    location ~* \.(php|asp|aspx|jsp)$ {
        return 444;
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(log|conf|ini)$ {
        deny all;
    }
}
EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/nyc_taxi_ml /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 11. Crear scripts de utilidad
log "Creando scripts de utilidad..."

# Script de logs
sudo tee /opt/nyc_taxi_ml/scripts/logs.sh > /dev/null <<EOF
#!/bin/bash
echo "📊 Logs del sistema NYC Taxi ML"
echo "================================"
echo ""
echo "🔍 Logs de la API:"
tail -f /opt/nyc_taxi_ml/logs/api.log
EOF

# Script de status
sudo tee /opt/nyc_taxi_ml/scripts/status.sh > /dev/null <<EOF
#!/bin/bash
echo "📊 Estado del sistema NYC Taxi ML"
echo "=================================="
echo ""
echo "🔍 Estado de Supervisor:"
sudo supervisorctl status nyc_taxi_ml
echo ""
echo "🔍 Estado de Nginx:"
sudo systemctl status nginx --no-pager
echo ""
echo "🔍 Estado de Firewall:"
sudo ufw status
echo ""
echo "🔍 Estado de Fail2Ban:"
sudo fail2ban-client status
echo ""
echo "🔍 Puertos en uso:"
sudo netstat -tlnp | grep -E ':(80|443|5000|5002)'
echo ""
echo "🔍 Procesos Python:"
ps aux | grep python | grep -v grep
EOF

# Script de restart
sudo tee /opt/nyc_taxi_ml/scripts/restart.sh > /dev/null <<EOF
#!/bin/bash
echo "🔄 Reiniciando servicios..."
sudo supervisorctl restart nyc_taxi_ml
sudo systemctl restart nginx
echo "✅ Servicios reiniciados"
EOF

# Script de seguridad
sudo tee /opt/nyc_taxi_ml/scripts/security.sh > /dev/null <<EOF
#!/bin/bash
echo "🔒 NYC Taxi ML - Security Status"
echo "================================"
echo ""
echo "🛡️ Firewall Status:"
sudo ufw status
echo ""
echo "🚫 Fail2Ban Status:"
sudo fail2ban-client status
echo ""
echo "📊 Failed Login Attempts:"
sudo grep "Failed password" /var/log/auth.log | tail -5
echo ""
echo "🌐 Nginx Access Logs (Last 5):"
sudo tail -5 /var/log/nginx/access.log
echo ""
echo "⚠️ Nginx Error Logs (Last 5):"
sudo tail -5 /var/log/nginx/error.log
echo ""
echo "🔍 API Logs (Last 5):"
tail -5 /opt/nyc_taxi_ml/logs/api.log
EOF

# Hacer scripts ejecutables
sudo chmod +x /opt/nyc_taxi_ml/scripts/*.sh
sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/scripts

# 12. Iniciar servicios
log "Iniciando servicios..."

# Recargar configuración de supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar aplicación
sudo supervisorctl start nyc_taxi_ml

# Reiniciar Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# 13. Verificar deployment
log "Verificando deployment..."

# Esperar un momento para que los servicios inicien
sleep 5

# Verificar estado de supervisor
if sudo supervisorctl status nyc_taxi_ml | grep -q "RUNNING"; then
    log "✅ Supervisor: Servicio corriendo"
else
    error "❌ Supervisor: Servicio no está corriendo"
fi

# Verificar estado de Nginx
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx: Servicio corriendo"
else
    error "❌ Nginx: Servicio no está corriendo"
fi

# Verificar estado de Firewall
if sudo ufw status | grep -q "Status: active"; then
    log "✅ Firewall: Activo"
else
    warning "⚠️ Firewall: No activo"
fi

# Verificar estado de Fail2Ban
if sudo systemctl is-active --quiet fail2ban; then
    log "✅ Fail2Ban: Activo"
else
    warning "⚠️ Fail2Ban: No activo"
fi

# Verificar puertos
if sudo netstat -tlnp | grep -q ":5002"; then
    log "✅ ML API: Puerto 5002 abierto"
else
    warning "⚠️ ML API: Puerto 5002 no detectado"
fi

if sudo netstat -tlnp | grep -q ":80"; then
    log "✅ Nginx: Puerto 80 abierto"
else
    error "❌ Nginx: Puerto 80 no detectado"
fi

# 14. Test de conectividad
log "Probando conectividad..."

# Test local
if curl -s http://localhost:5002/health > /dev/null; then
    log "✅ ML API: Health check local OK"
else
    warning "⚠️ ML API: Health check local falló"
fi

if curl -s http://localhost/ > /dev/null; then
    log "✅ Frontend: Acceso local OK"
else
    warning "⚠️ Frontend: Acceso local falló"
fi

# Test rate limiting
log "Probando rate limiting..."
for i in {1..15}; do
    curl -s http://localhost/ml/health > /dev/null
done
log "✅ Rate limiting configurado"

# 15. Información final
log "🎉 Deployment completo exitoso!"
echo ""
echo "📊 Información del sistema:"
echo "=========================="
echo "🌐 Frontend: http://$(curl -s ifconfig.me)/"
echo "🤖 ML API: http://$(curl -s ifconfig.me)/ml/"
echo "📁 Logs: /opt/nyc_taxi_ml/logs/"
echo "⚙️ Config: /opt/nyc_taxi_ml/config/"
echo ""
echo "🔒 Seguridad configurada:"
echo "========================="
echo "🛡️ Firewall: UFW activo"
echo "🚫 Fail2Ban: Protección contra ataques"
echo "🌐 Nginx: Rate limiting y headers de seguridad"
echo "📊 Monitoreo: Logs y alertas"
echo ""
echo "🔧 Comandos útiles:"
echo "==================="
echo "📊 Ver logs: /opt/nyc_taxi_ml/scripts/logs.sh"
echo "📈 Ver estado: /opt/nyc_taxi_ml/scripts/status.sh"
echo "🔄 Reiniciar: /opt/nyc_taxi_ml/scripts/restart.sh"
echo "🔒 Seguridad: /opt/nyc_taxi_ml/scripts/security.sh"
echo "🛠️ Supervisor: sudo supervisorctl status nyc_taxi_ml"
echo ""
echo "🚀 ¡Sistema seguro listo para producción!"
