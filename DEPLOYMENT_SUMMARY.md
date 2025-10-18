# 🚀 NYC Taxi ML - Deployment en AWS EC2

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

## 🎯 **Pasos para Deployar en EC2**

### **1. Crear Instancia EC2**
1. Ve a [AWS Console](https://console.aws.amazon.com)
2. Busca "EC2" → "Launch Instance"
3. Configuración recomendada:
   ```
   AMI: Ubuntu Server 22.04 LTS
   Instance Type: t2.micro (Free tier)
   Key Pair: Crear nuevo (.pem file)
   Security Group: 
     - SSH (22) - Tu IP
     - HTTP (80) - 0.0.0.0/0
     - HTTPS (443) - 0.0.0.0/0
     - Custom (5000) - 0.0.0.0/0
     - Custom (5002) - 0.0.0.0/0
   Storage: 30 GB (Free tier)
   ```

### **2. Conectar a la Instancia**
```bash
# Descargar key pair (.pem file)
# Conectar via SSH
ssh -i "tu-key.pem" ubuntu@tu-instancia.amazonaws.com
```

### **3. Subir Archivos**
```bash
# Opción 1: Git (recomendado)
git clone https://github.com/tu-usuario/DataRush-ProductizacionDeSoluciones.git
cd DataRush-ProductizacionDeSoluciones

# Opción 2: SCP
scp -i "tu-key.pem" -r . ubuntu@tu-instancia.amazonaws.com:~/nyc-taxi-ml/
```

### **4. Ejecutar Deployment**
```bash
# Hacer ejecutable y correr
chmod +x deploy_ec2.sh
sudo ./deploy_ec2.sh
```

### **5. Configurar Datos**
```bash
# Configurar datos y modelos
chmod +x setup_data.sh
sudo ./setup_data.sh
```

### **6. Verificar Deployment**
```bash
# Verificar servicios
sudo supervisorctl status nyc_taxi_ml
sudo systemctl status nginx

# Probar API
curl http://localhost:5002/health
curl http://localhost/

# Ver logs
tail -f /opt/nyc_taxi_ml/logs/api.log
```

## 🌐 **Acceso a la Aplicación**

Una vez deployado, tu aplicación estará disponible en:
- **Frontend**: `http://tu-ip-publica/`
- **ML API**: `http://tu-ip-publica/ml/`
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
```

### **Nginx**
```bash
# Reiniciar Nginx
sudo systemctl restart nginx

# Ver logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🔒 **Configuración de Seguridad**

### **Firewall (UFW)**
```bash
# Verificar estado
sudo ufw status

# Configurar reglas
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### **SSL/HTTPS (Opcional)**
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado (reemplazar con tu dominio)
sudo certbot --nginx -d tu-dominio.com
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

# Logs de Supervisor
tail -f /opt/nyc_taxi_ml/logs/supervisor.log

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
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

Tu sistema estará completamente funcional con:
- ✅ **Frontend**: Interfaz web completa
- ✅ **ML API**: Predicciones en tiempo real
- ✅ **Backend**: API de datos históricos
- ✅ **Nginx**: Proxy reverso y servidor web
- ✅ **Supervisor**: Gestión de servicios
- ✅ **Logs**: Monitoreo completo
- ✅ **SSL**: Seguridad HTTPS (opcional)

## 💡 **Próximos Pasos**

1. **Dominio**: Configurar DNS para tu dominio
2. **SSL**: Obtener certificado SSL
3. **Monitoreo**: Configurar CloudWatch
4. **Backup**: Configurar respaldos automáticos
5. **Escalabilidad**: Configurar Auto Scaling

¡**Sistema listo para producción**! 🚀
