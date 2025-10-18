# 🚀 Guía de Deployment en AWS EC2

## 💰 Costos Estimados

### Free Tier (Primeros 12 meses)
- **t2.micro**: 750 horas/mes GRATIS
- **Almacenamiento**: 30 GB EBS GRATIS
- **Transferencia**: 15 GB/mes GRATIS

### Post-Free Tier
- **t2.micro**: ~$8.50/mes (24/7)
- **t3.micro**: ~$7.50/mes (24/7) 
- **t2.small**: ~$17/mes (recomendado)
- **Almacenamiento**: ~$3.50/mes por 100GB
- **Transferencia**: ~$0.09/GB después de 15GB

## 🎯 Paso 1: Crear Instancia EC2

### 1.1 Acceder a AWS Console
1. Ve a [AWS Console](https://console.aws.amazon.com)
2. Busca "EC2" en el buscador
3. Click en "Launch Instance"

### 1.2 Configurar Instancia
```
Name: nyc-taxi-ml-production
AMI: Ubuntu Server 22.04 LTS (Free tier eligible)
Instance Type: t2.micro (Free tier)
Key Pair: Crear nuevo o usar existente
Security Group: 
  - SSH (22) - Tu IP
  - HTTP (80) - 0.0.0.0/0
  - HTTPS (443) - 0.0.0.0/0
  - Custom (5000) - 0.0.0.0/0 (Backend)
  - Custom (5002) - 0.0.0.0/0 (ML API)
Storage: 30 GB (Free tier)
```

### 1.3 Conectar a la Instancia
```bash
# Descargar key pair (.pem file)
# Conectar via SSH
ssh -i "tu-key.pem" ubuntu@tu-instancia.amazonaws.com
```

## 🔧 Paso 2: Preparar el Servidor

### 2.1 Actualizar Sistema
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip git nginx supervisor
```

### 2.2 Configurar Python
```bash
# Crear usuario para la aplicación
sudo useradd -m -s /bin/bash nyc_taxi
sudo usermod -aG sudo nyc_taxi

# Cambiar a usuario de la aplicación
sudo su - nyc_taxi
```

### 2.3 Clonar Repositorio
```bash
# Clonar tu repositorio
git clone https://github.com/tu-usuario/DataRush-ProductizacionDeSoluciones.git
cd DataRush-ProductizacionDeSoluciones

# Instalar dependencias
pip3 install -r requirements.txt
```

## 🚀 Paso 3: Configurar Aplicación

### 3.1 Crear Estructura de Producción
```bash
# Crear directorios
sudo mkdir -p /opt/nyc_taxi_ml/{api,ml_engine,config,logs,data,models}
sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml

# Copiar archivos
cp api_rule_based.py /opt/nyc_taxi_ml/api/
cp rule_based_ml.py /opt/nyc_taxi_ml/ml_engine/
cp solucion-las_tortugas_cosmicales/backend/app.py /opt/nyc_taxi_ml/api/
```

### 3.2 Configurar Supervisor
```bash
# Crear configuración de supervisor
sudo nano /etc/supervisor/conf.d/nyc_taxi_ml.conf
```

Contenido del archivo:
```ini
[program:nyc_taxi_ml]
command=python3 /opt/nyc_taxi_ml/api/api_rule_based.py
directory=/opt/nyc_taxi_ml/api
user=nyc_taxi
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/nyc_taxi_ml/logs/api.log
environment=PATH="/usr/bin:/usr/local/bin"
```

### 3.3 Configurar Nginx
```bash
# Crear configuración de Nginx
sudo nano /etc/nginx/sites-available/nyc_taxi_ml
```

Contenido del archivo:
```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ML API
    location /ml/ {
        proxy_pass http://127.0.0.1:5002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend estático
    location / {
        root /opt/nyc_taxi_ml/frontend;
        index map.html;
        try_files $uri $uri/ /map.html;
    }
}
```

## 🔄 Paso 4: Iniciar Servicios

### 4.1 Habilitar Sitio
```bash
# Habilitar sitio en Nginx
sudo ln -s /etc/nginx/sites-available/nyc_taxi_ml /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4.2 Iniciar Aplicación
```bash
# Recargar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nyc_taxi_ml

# Verificar estado
sudo supervisorctl status nyc_taxi_ml
```

## 🔒 Paso 5: Configurar SSL (Opcional)

### 5.1 Instalar Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 5.2 Obtener Certificado
```bash
# Reemplazar con tu dominio
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

## 📊 Paso 6: Monitoreo

### 6.1 Verificar Servicios
```bash
# Estado de servicios
sudo supervisorctl status
sudo systemctl status nginx

# Logs
tail -f /opt/nyc_taxi_ml/logs/api.log
sudo tail -f /var/log/nginx/access.log
```

### 6.2 Health Checks
```bash
# Probar API
curl http://localhost:5002/health
curl http://localhost:5000/health

# Probar a través de Nginx
curl http://tu-dominio.com/ml/health
curl http://tu-dominio.com/api/health
```

## 🚨 Troubleshooting

### Problemas Comunes
1. **Puerto ocupado**: `sudo netstat -tlnp | grep :5002`
2. **Permisos**: `sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml`
3. **Logs**: `sudo supervisorctl tail -f nyc_taxi_ml`

### Comandos Útiles
```bash
# Reiniciar servicios
sudo supervisorctl restart nyc_taxi_ml
sudo systemctl restart nginx

# Ver logs en tiempo real
tail -f /opt/nyc_taxi_ml/logs/api.log

# Verificar puertos
sudo netstat -tlnp | grep -E ':(80|443|5000|5002)'
```

## 💡 Optimizaciones

### Para Producción
1. **Instancia más grande**: t2.small o t3.small
2. **Load Balancer**: Para múltiples instancias
3. **Auto Scaling**: Para manejar picos de tráfico
4. **CloudWatch**: Para monitoreo avanzado

### Seguridad
1. **Security Groups**: Solo puertos necesarios
2. **IAM Roles**: Para acceso a otros servicios AWS
3. **VPC**: Para red privada
4. **WAF**: Para protección web

## 📈 Escalabilidad

### Horizontal Scaling
```bash
# Crear AMI de la instancia configurada
# Usar Auto Scaling Group
# Configurar Load Balancer
# Usar RDS para base de datos
```

### Vertical Scaling
```bash
# Cambiar tipo de instancia
# Aumentar almacenamiento
# Optimizar código
```

## 🎯 Resultado Final

Tu aplicación estará disponible en:
- **Frontend**: `http://tu-dominio.com`
- **Backend API**: `http://tu-dominio.com/api/`
- **ML API**: `http://tu-dominio.com/ml/`

¡**Sistema listo para producción**! 🚀
