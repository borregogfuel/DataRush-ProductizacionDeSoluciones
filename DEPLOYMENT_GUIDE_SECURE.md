# 🚀 Guía Completa de Deployment en AWS EC2 - CON SEGURIDAD

## 💰 **Costos Estimados**

### **🆓 Free Tier (Primeros 12 meses)**
- **t2.micro**: 750 horas/mes GRATIS
- **Almacenamiento**: 30 GB EBS GRATIS  
- **Transferencia**: 15 GB/mes GRATIS
- **Total**: **$0/mes** por 12 meses

### **💵 Post-Free Tier**
- **t2.micro**: ~$8.50/mes (24/7)
- **t3.micro**: ~$7.50/mes (24/7)
- **t2.small**: ~$17/mes (recomendado para producción)
- **Almacenamiento**: ~$3.50/mes por 100GB
- **Total estimado**: **$12-20/mes**

## 🎯 **Pasos para Deployar en EC2 - PASO A PASO**

### **Paso 1: Crear Instancia EC2**

1. **En la consola de AWS:**
   - Busca "EC2" en el buscador superior
   - Click en "EC2" (no en "EC2 Dashboard")

2. **Launch Instance:**
   - Click en el botón azul "Launch Instance"

3. **Configurar la instancia:**
   ```
   Name: nyc-taxi-ml-production
   
   Application and OS Images (AMI):
   - Selecciona "Ubuntu Server 22.04 LTS (HVM), SSD Volume Type"
   - Asegúrate que diga "Free tier eligible"
   
   Instance type:
   - Selecciona "t2.micro" (Free tier eligible)
   
   Key pair (login):
   - Click "Create new key pair"
   - Name: nyc-taxi-ml-key
   - Key pair type: RSA
   - Private key file format: .pem
   - Click "Create key pair"
   - ⚠️ IMPORTANTE: Descarga el archivo .pem
   ```

4. **Network settings:**
   ```
   - VPC: Default
   - Subnet: Default
   - Auto-assign public IP: Enable
   - Security group: Create security group
   - Security group name: nyc-taxi-ml-sg
   
   Inbound security group rules:
   - SSH (22) - My IP (tu IP actual)
   - HTTP (80) - Anywhere (0.0.0.0/0)
   - HTTPS (443) - Anywhere (0.0.0.0/0)
   - Custom TCP (5000) - Anywhere (0.0.0.0/0)
   - Custom TCP (5002) - Anywhere (0.0.0.0/0)
   ```

5. **Storage:**
   ```
   - Volume type: gp3
   - Size: 30 GiB (Free tier)
   ```

6. **Launch:**
   - Click "Launch instance"
   - Click "View all instances"

### **Paso 2: Conectar a la Instancia**

1. **Esperar que esté "Running":**
   - Estado debe cambiar a "Running" (verde)
   - Anota la "Public IPv4 address"

2. **Conectar via SSH:**
   ```bash
   # En Windows (PowerShell o CMD)
   ssh -i "nyc-taxi-ml-key.pem" ubuntu@tu-ip-publica
   
   # Si no tienes SSH instalado, usa AWS Systems Manager Session Manager
   ```

3. **Alternativa - AWS Systems Manager:**
   - En la consola EC2, selecciona tu instancia
   - Click "Connect"
   - Selecciona "Session Manager"
   - Click "Connect"

### **Paso 3: Subir Archivos**

**Opción A - Git (Recomendado):**
```bash
# Clonar tu repositorio
git clone https://github.com/tu-usuario/DataRush-ProductizacionDeSoluciones.git
cd DataRush-ProductizacionDeSoluciones
```

**Opción B - SCP (desde tu computadora):**
```bash
# En tu computadora (PowerShell)
scp -i "nyc-taxi-ml-key.pem" -r . ubuntu@tu-ip-publica:~/nyc-taxi-ml/
```

### **Paso 4: Ejecutar Deployment Seguro**

```bash
# Hacer ejecutable y correr
chmod +x deploy_secure.sh
sudo ./deploy_secure.sh
```

### **Paso 5: Configurar Datos**

```bash
# Configurar datos y modelos
chmod +x setup_data.sh
sudo ./setup_data.sh
```

### **Paso 6: Verificar Deployment**

```bash
# Verificar servicios
sudo supervisorctl status nyc_taxi_ml
sudo systemctl status nginx

# Verificar seguridad
sudo ufw status
sudo fail2ban-client status

# Probar API
curl http://localhost:5002/health
curl http://localhost/

# Ver logs
tail -f /opt/nyc_taxi_ml/logs/api.log
```

## 🔒 **Seguridad Implementada**

### **🛡️ Protecciones Activas:**

1. **Firewall (UFW):**
   - Solo puertos necesarios abiertos
   - SSH restringido a tu IP
   - Protección contra escaneo de puertos

2. **Fail2Ban:**
   - Bloquea IPs con intentos de login fallidos
   - Protección contra ataques de fuerza bruta
   - Monitoreo de logs de autenticación

3. **Nginx Security:**
   - Rate limiting (10 requests/minuto para API)
   - Headers de seguridad
   - Bloqueo de archivos sensibles
   - Ocultación de versión del servidor

4. **API Protection:**
   - Autenticación con API keys
   - Validación de entrada
   - Protección contra SQL injection
   - Rate limiting por IP

5. **Monitoreo:**
   - Logs de seguridad
   - Alertas de ataques
   - Backup automático de configuraciones

### **🔑 API Keys:**

Las API keys se generan automáticamente. Para usar la API:

```bash
# Ejemplo de uso con API key
curl -X POST http://tu-ip-publica/ml/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_prod_tu_api_key_aqui" \
  -d '{
    "pickup_location": "Central Park",
    "dropoff_location": "Times Square",
    "pickup_datetime": "2025-10-17 18:30:00"
  }'
```

## 🌐 **Acceso a la Aplicación**

Una vez deployado, tu aplicación estará disponible en:
- **Frontend**: `http://tu-ip-publica/`
- **ML API**: `http://tu-ip-publica/ml/` (requiere API key)
- **Backend API**: `http://tu-ip-publica/api/`

## 🔧 **Comandos de Administración**

### **Supervisor (Gestión de Servicios)**
```bash
# Controlar servicio
sudo supervisorctl start nyc_taxi_ml
sudo supervisorctl stop nyc_taxi_ml
sudo supervisorctl restart nyc_taxi_ml
sudo supervisorctl status nyc_taxi_ml

# Ver logs
sudo supervisorctl tail -f nyc_taxi_ml
```

### **Scripts Útiles**
```bash
# Ver logs en tiempo real
/opt/nyc_taxi_ml/scripts/logs.sh

# Ver estado del sistema
/opt/nyc_taxi_ml/scripts/status.sh

# Reiniciar servicios
/opt/nyc_taxi_ml/scripts/restart.sh

# Ver estado de seguridad
/opt/nyc_taxi_ml/scripts/security.sh
```

### **Nginx**
```bash
# Reiniciar Nginx
sudo systemctl restart nginx

# Ver logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### **Seguridad**
```bash
# Ver estado del firewall
sudo ufw status

# Ver estado de Fail2Ban
sudo fail2ban-client status

# Ver intentos de login fallidos
sudo grep "Failed password" /var/log/auth.log
```

## 🔒 **Configuración de SSL/HTTPS (Opcional)**

### **Con Certbot:**
```bash
# Instalar Certbot (ya instalado)
sudo apt install certbot python3-certbot-nginx

# Obtener certificado (reemplazar con tu dominio)
sudo certbot --nginx -d tu-dominio.com
```

### **Con Let's Encrypt:**
```bash
# Configurar dominio en DNS
# Ejecutar certbot
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com
```

## 📊 **Monitoreo**

### **Health Checks**
```bash
# Health check básico
curl http://localhost:5002/health

# Estado detallado
curl http://localhost:5002/status

# A través de Nginx
curl http://tu-ip-publica/ml/health
```

### **Logs**
```bash
# Logs de la API
tail -f /opt/nyc_taxi_ml/logs/api.log

# Logs de seguridad
tail -f /var/log/auth.log
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Logs de Fail2Ban
sudo tail -f /var/log/fail2ban.log
```

## 🚨 **Troubleshooting**

### **Problemas Comunes**

1. **API no responde**
   ```bash
   sudo supervisorctl status nyc_taxi_ml
   sudo supervisorctl restart nyc_taxi_ml
   ```

2. **Puerto ocupado**
   ```bash
   sudo netstat -tlnp | grep :5002
   sudo supervisorctl stop nyc_taxi_ml
   ```

3. **Permisos incorrectos**
   ```bash
   sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml
   ```

4. **Nginx no funciona**
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Firewall bloqueando**
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   ```

### **Logs de Debug**
```bash
# Habilitar debug en producción.yaml
logging:
  level: "DEBUG"

# Reiniciar servicio
sudo supervisorctl restart nyc_taxi_ml
```

## 📈 **Optimizaciones para Producción**

### **Instancia más Grande**
- **t2.small**: Para mejor rendimiento
- **t3.small**: Para mejor precio/rendimiento
- **t3.medium**: Para alta carga

### **Load Balancer**
- **Application Load Balancer**: Para múltiples instancias
- **Auto Scaling Group**: Para manejar picos de tráfico
- **Target Group**: Puerto 5002 para ML API

### **Monitoreo Avanzado**
- **CloudWatch**: Métricas y logs
- **CloudWatch Agent**: Métricas personalizadas
- **SNS**: Alertas por email/SMS

## 🎯 **Resultado Final**

Tu sistema estará completamente funcional y seguro con:
- ✅ **Frontend**: Interfaz web completa
- ✅ **ML API**: Predicciones en tiempo real con autenticación
- ✅ **Backend**: API de datos históricos
- ✅ **Nginx**: Proxy reverso y servidor web con seguridad
- ✅ **Supervisor**: Gestión de servicios
- ✅ **Logs**: Monitoreo completo
- ✅ **Firewall**: Protección de red
- ✅ **Fail2Ban**: Protección contra ataques
- ✅ **Rate Limiting**: Protección contra abuso
- ✅ **SSL**: Seguridad HTTPS (opcional)

## 💡 **Próximos Pasos**

1. **Dominio**: Configurar DNS para tu dominio
2. **SSL**: Obtener certificado SSL
3. **Monitoreo**: Configurar CloudWatch
4. **Backup**: Configurar respaldos automáticos
5. **Escalabilidad**: Configurar Auto Scaling

¡**Sistema seguro listo para producción**! 🚀🔒
