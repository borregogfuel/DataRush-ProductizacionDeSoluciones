# Dockerfile para NYC Taxi ML API
FROM python:3.9-slim

# Metadatos
LABEL maintainer="NYC Taxi ML Team"
LABEL version="2.0"
LABEL description="NYC Taxi ML API para predicción de tarifas y seguridad"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_DIR=/opt/nyc_taxi_ml

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd -r -s /bin/false -d $APP_DIR nyc_taxi

# Crear directorios
RUN mkdir -p $APP_DIR/{api,ml_engine,config,data,models,logs,scripts}
RUN chown -R nyc_taxi:nyc_taxi $APP_DIR

# Cambiar al directorio de trabajo
WORKDIR $APP_DIR

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY production/api/app.py api/
COPY production/ml_engine/inference_cli.py ml_engine/
COPY production/config/production.yaml config/

# Copiar datos (si existen)
COPY --chown=nyc_taxi:nyc_taxi solucion-las_tortugas_cosmicales/ML/LocationID_to_pretinct.csv data/ 2>/dev/null || true
COPY --chown=nyc_taxi:nyc_taxi solucion-las_tortugas_cosmicales/ML/crime_data/NYPD_Complaint_Data_Historic_20251015.csv data/ 2>/dev/null || true

# Copiar modelos (si existen)
COPY --chown=nyc_taxi:nyc_taxi models/ models/ 2>/dev/null || true

# Crear script de inicio
RUN echo '#!/bin/bash\ncd $APP_DIR\npython api/app.py' > scripts/start.sh && \
    chmod +x scripts/start.sh

# Cambiar a usuario no-root
USER nyc_taxi

# Exponer puerto
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Comando por defecto
CMD ["python", "api/app.py"]
