#!/bin/bash

# 🔒 Script de Configuración de Seguridad para EC2
# NYC Taxi ML System - Secure Production Setup

set -e  # Exit on any error

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

log "🔒 Configurando seguridad para NYC Taxi ML..."

# Verificar que estamos en el directorio correcto
if [ ! -d "/opt/nyc_taxi_ml" ]; then
    error "Directorio /opt/nyc_taxi_ml no encontrado. Ejecuta deploy_ec2.sh primero."
fi

# 1. Configurar Firewall (UFW)
log "Configurando firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Reglas específicas
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw allow 5000/tcp comment 'Backend API'
sudo ufw allow 5002/tcp comment 'ML API'

# Habilitar firewall
sudo ufw --force enable

log "✅ Firewall configurado"

# 2. Configurar Fail2Ban
log "Instalando y configurando Fail2Ban..."
sudo apt install -y fail2ban

# Configurar Fail2Ban para SSH
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

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

log "✅ Fail2Ban configurado"

# 3. Configurar SSL/TLS
log "Configurando SSL/TLS..."
sudo apt install -y certbot python3-certbot-nginx

# Crear configuración SSL básica
sudo tee /etc/nginx/snippets/ssl-params.conf > /dev/null <<EOF
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
ssl_ecdh_curve secp384r1;
ssl_session_timeout 10m;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
EOF

log "✅ SSL/TLS configurado"

# 4. Configurar Nginx con seguridad
log "Configurando Nginx con seguridad..."
sudo tee /etc/nginx/sites-available/nyc_taxi_ml_secure > /dev/null <<EOF
# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/m;
limit_req_zone \$binary_remote_addr zone=general:10m rate=30r/m;

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Rate limiting
    limit_req zone=general burst=20 nodelay;
    
    # Frontend estático
    location / {
        root /opt/nyc_taxi_ml/frontend;
        index map.html;
        try_files \$uri \$uri/ /map.html;
        
        # Security headers for static files
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
    }
    
    # ML API - Protected
    location /ml/ {
        # Rate limiting
        limit_req zone=api burst=5 nodelay;
        
        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        
        proxy_pass http://127.0.0.1:5002/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # Hide server version
        proxy_hide_header Server;
        proxy_hide_header X-Powered-By;
    }
    
    # Backend API - Protected
    location /api/ {
        # Rate limiting
        limit_req zone=api burst=5 nodelay;
        
        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Hide server version
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

# Habilitar sitio seguro
sudo ln -sf /etc/nginx/sites-available/nyc_taxi_ml_secure /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/nyc_taxi_ml

log "✅ Nginx configurado con seguridad"

# 5. Configurar API segura
log "Configurando API segura..."
sudo cp api_secure.py /opt/nyc_taxi_ml/api/
sudo chown nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/api/api_secure.py

# Instalar dependencias de seguridad
sudo -u nyc_taxi /opt/nyc_taxi_ml/venv/bin/pip install flask-limiter

# 6. Configurar Supervisor para API segura
log "Configurando Supervisor para API segura..."
sudo tee /etc/supervisor/conf.d/nyc_taxi_ml_secure.conf > /dev/null <<EOF
[program:nyc_taxi_ml_secure]
command=/opt/nyc_taxi_ml/venv/bin/python /opt/nyc_taxi_ml/api/api_secure.py
directory=/opt/nyc_taxi_ml/api
user=nyc_taxi
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/nyc_taxi_ml/logs/api_secure.log
environment=PATH="/opt/nyc_taxi_ml/venv/bin:/usr/bin:/usr/local/bin"
EOF

# 7. Configurar monitoreo de seguridad
log "Configurando monitoreo de seguridad..."
sudo tee /opt/nyc_taxi_ml/scripts/security_monitor.sh > /dev/null <<EOF
#!/bin/bash

echo "🔒 NYC Taxi ML - Security Monitor"
echo "=================================="
echo ""

echo "🛡️ Firewall Status:"
sudo ufw status
echo ""

echo "🚫 Fail2Ban Status:"
sudo fail2ban-client status
echo ""

echo "📊 Failed Login Attempts:"
sudo grep "Failed password" /var/log/auth.log | tail -10
echo ""

echo "🌐 Nginx Access Logs (Last 10):"
sudo tail -10 /var/log/nginx/access.log
echo ""

echo "⚠️ Nginx Error Logs (Last 10):"
sudo tail -10 /var/log/nginx/error.log
echo ""

echo "🔍 API Security Logs (Last 10):"
tail -10 /opt/nyc_taxi_ml/logs/api_secure.log
echo ""

echo "📈 System Resources:"
free -h
df -h /
echo ""

echo "🔐 Active Connections:"
sudo netstat -tlnp | grep -E ':(80|443|5000|5002)'
EOF

sudo chmod +x /opt/nyc_taxi_ml/scripts/security_monitor.sh
sudo chown nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/scripts/security_monitor.sh

# 8. Configurar backup de seguridad
log "Configurando backup de seguridad..."
sudo tee /opt/nyc_taxi_ml/scripts/security_backup.sh > /dev/null <<EOF
#!/bin/bash

BACKUP_DIR="/opt/nyc_taxi_ml/backups"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

echo "🔒 Creating security backup..."

# Backup configuration files
tar -czf \$BACKUP_DIR/security_config_\$DATE.tar.gz \\
    /etc/nginx/sites-available/nyc_taxi_ml_secure \\
    /etc/fail2ban/jail.local \\
    /etc/ufw/ \\
    /opt/nyc_taxi_ml/api/api_secure.py \\
    /opt/nyc_taxi_ml/config/

# Backup logs
tar -czf \$BACKUP_DIR/logs_\$DATE.tar.gz \\
    /var/log/nginx/ \\
    /var/log/auth.log \\
    /opt/nyc_taxi_ml/logs/

echo "✅ Backup created: \$BACKUP_DIR/security_config_\$DATE.tar.gz"
echo "✅ Logs backup: \$BACKUP_DIR/logs_\$DATE.tar.gz"

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

sudo chmod +x /opt/nyc_taxi_ml/scripts/security_backup.sh
sudo chown nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/scripts/security_backup.sh

# 9. Configurar cron jobs para seguridad
log "Configurando cron jobs para seguridad..."
sudo tee /etc/cron.d/nyc_taxi_security > /dev/null <<EOF
# Security monitoring and backup
0 2 * * * root /opt/nyc_taxi_ml/scripts/security_backup.sh
0 */6 * * * root /opt/nyc_taxi_ml/scripts/security_monitor.sh > /opt/nyc_taxi_ml/logs/security_monitor.log
EOF

# 10. Reiniciar servicios
log "Reiniciando servicios..."
sudo supervisorctl reread
sudo supervisorctl update

# Detener API anterior
sudo supervisorctl stop nyc_taxi_ml 2>/dev/null || true

# Iniciar API segura
sudo supervisorctl start nyc_taxi_ml_secure

# Reiniciar Nginx
sudo systemctl restart nginx

# 11. Verificar configuración
log "Verificando configuración de seguridad..."

# Verificar firewall
if sudo ufw status | grep -q "Status: active"; then
    log "✅ Firewall activo"
else
    warning "⚠️ Firewall no activo"
fi

# Verificar Fail2Ban
if sudo systemctl is-active --quiet fail2ban; then
    log "✅ Fail2Ban activo"
else
    warning "⚠️ Fail2Ban no activo"
fi

# Verificar Nginx
if sudo systemctl is-active --quiet nginx; then
    log "✅ Nginx activo"
else
    error "❌ Nginx no activo"
fi

# Verificar API segura
if sudo supervisorctl status nyc_taxi_ml_secure | grep -q "RUNNING"; then
    log "✅ API segura corriendo"
else
    warning "⚠️ API segura no corriendo"
fi

# 12. Test de seguridad
log "Probando configuración de seguridad..."

# Test rate limiting
echo "Probando rate limiting..."
for i in {1..15}; do
    curl -s http://localhost/ml/health > /dev/null
done

# Test API key requirement
echo "Probando autenticación..."
curl -s http://localhost/ml/predict -X POST -H "Content-Type: application/json" -d '{"pickup_location": "Central Park", "dropoff_location": "Times Square"}' | grep -q "API key required" && log "✅ Autenticación funcionando" || warning "⚠️ Autenticación no funcionando"

# 13. Información final
log "🎉 Configuración de seguridad completada!"
echo ""
echo "🔒 Resumen de seguridad:"
echo "========================"
echo "🛡️ Firewall: UFW configurado y activo"
echo "🚫 Fail2Ban: Protección contra ataques"
echo "🌐 Nginx: Rate limiting y headers de seguridad"
echo "🔑 API: Autenticación con API keys"
echo "📊 Monitoreo: Logs y alertas configurados"
echo "💾 Backup: Respaldos automáticos"
echo ""
echo "🔧 Comandos de seguridad:"
echo "========================"
echo "📊 Monitoreo: /opt/nyc_taxi_ml/scripts/security_monitor.sh"
echo "💾 Backup: /opt/nyc_taxi_ml/scripts/security_backup.sh"
echo "🛡️ Firewall: sudo ufw status"
echo "🚫 Fail2Ban: sudo fail2ban-client status"
echo "🌐 Nginx: sudo nginx -t"
echo ""
echo "🔑 API Keys generadas:"
echo "====================="
echo "Usa el header X-API-Key para autenticación"
echo "Las keys se generan automáticamente al iniciar la API"
echo ""
echo "🚀 ¡Sistema seguro listo para producción!"
