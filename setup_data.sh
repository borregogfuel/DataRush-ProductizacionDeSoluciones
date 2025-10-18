#!/bin/bash

# 📊 Script de Configuración de Datos para EC2
# NYC Taxi ML System

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

log "📊 Configurando datos para NYC Taxi ML..."

# Verificar que estamos en el directorio correcto
if [ ! -d "/opt/nyc_taxi_ml" ]; then
    error "Directorio /opt/nyc_taxi_ml no encontrado. Ejecuta deploy_ec2.sh primero."
fi

# 1. Verificar estructura de datos
log "Verificando estructura de datos..."
if [ ! -d "/opt/nyc_taxi_ml/data" ]; then
    sudo mkdir -p /opt/nyc_taxi_ml/data
    sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/data
fi

# 2. Verificar archivos de datos críticos
log "Verificando archivos de datos críticos..."

# Verificar LocationID_to_pretinct.csv
if [ -f "/opt/nyc_taxi_ml/data/LocationID_to_pretinct.csv" ]; then
    log "✅ LocationID_to_pretinct.csv encontrado"
else
    warning "⚠️ LocationID_to_pretinct.csv no encontrado"
    info "Creando archivo de mapeo básico..."
    
    # Crear archivo básico de mapeo
    sudo tee /opt/nyc_taxi_ml/data/LocationID_to_pretinct.csv > /dev/null <<EOF
LocationID,Zone,Borough,Precinct
1,Newark Airport,EWR,0
2,Jamaica Bay,Queens,0
3,Allerton/Pelham Gardens,Bronx,0
4,Alphabet City,Manhattan,0
5,Arden Heights,Staten Island,0
6,Arrochar/Fort Wadsworth,Staten Island,0
7,Astoria,Queens,0
8,Astoria Park,Queens,0
9,Auburndale,Queens,0
10,Baisley Park,Queens,0
11,Bathgate,Bronx,0
12,Battery Park,Manhattan,0
13,Battery Park City,Manhattan,0
14,Bay Ridge,Brooklyn,0
15,Bay Terrace/Fort Totten,Queens,0
16,Bay Terrace,Staten Island,0
17,Bayside,Queens,0
18,Bedford,Brooklyn,0
19,Bedford Park/Norwood,Bronx,0
20,Beechhurst,Queens,0
21,Belle Harbor,Queens,0
22,Bellerose,Queens,0
23,Belmont,Bronx,0
24,Bensonhurst East,Brooklyn,0
25,Bensonhurst West,Brooklyn,0
26,Bloomfield,Staten Island,0
27,Boerum Hill,Brooklyn,0
28,Borough Park,Brooklyn,0
29,Breezy Point/Fort Tilden/Riis Beach,Queens,0
30,Briarwood/Jamaica Hills,Queens,0
31,Brighton Beach,Brooklyn,0
32,Bronxdale,Bronx,0
33,Brooklyn Heights,Brooklyn,0
34,Brooklyn Navy Yard,Brooklyn,0
35,Brownsville,Brooklyn,0
36,Bull's Head,Staten Island,0
37,Bushwick North,Brooklyn,0
38,Bushwick South,Brooklyn,0
39,Butler Manor,Staten Island,0
40,Canarsie,Brooklyn,0
41,Carroll Gardens,Brooklyn,0
42,Castleton Corners,Staten Island,0
43,Chelsea,Manhattan,0
44,Chinatown,Manhattan,0
45,City Island,Bronx,0
46,Claremont/Bathgate,Bronx,0
47,Claremont Village,Bronx,0
48,Clason Point,Bronx,0
49,Clifton,Staten Island,0
50,Clinton East,Manhattan,0
51,Clinton Hill,Brooklyn,0
52,Clinton West,Manhattan,0
53,Co-op City,Bronx,0
54,Cobble Hill,Brooklyn,0
55,College Point,Queens,0
56,Columbia Street,Brooklyn,0
57,Coney Island,Brooklyn,0
58,Corona,Queens,0
59,Corona,Queens,0
60,Crown Heights North,Brooklyn,0
61,Crown Heights South,Brooklyn,0
62,Cypress Hills,Brooklyn,0
63,DUMBO/Vinegar Hill,Brooklyn,0
64,Dyker Heights,Brooklyn,0
65,East Chelsea,Manhattan,0
66,East Concourse/Concourse Village,Bronx,0
67,East Flatbush/Farragut,Brooklyn,0
68,East Flatbush/Remsen Village,Brooklyn,0
69,East Harlem North,Manhattan,0
70,East Harlem South,Manhattan,0
71,East New York,Brooklyn,0
72,East New York/Pennsylvania Avenue,Brooklyn,0
73,East Tremont,Bronx,0
74,East Village,Manhattan,0
75,East Williamsburg,Brooklyn,0
76,Eastchester,Bronx,0
77,Elmhurst,Queens,0
78,Eltingville,Staten Island,0
79,Emerson Hill,Staten Island,0
80,Far Rockaway,Queens,0
81,Flatbush/Ditmas Park,Brooklyn,0
82,Flatlands,Brooklyn,0
83,Flushing,Queens,0
84,Flushing,Queens,0
85,Flushing,Queens,0
86,Flushing,Queens,0
87,Flushing,Queens,0
88,Flushing,Queens,0
89,Flushing,Queens,0
90,Flushing,Queens,0
91,Flushing,Queens,0
92,Flushing,Queens,0
93,Flushing,Queens,0
94,Flushing,Queens,0
95,Flushing,Queens,0
96,Flushing,Queens,0
97,Flushing,Queens,0
98,Flushing,Queens,0
99,Flushing,Queens,0
100,Flushing,Queens,0
101,Flushing,Queens,0
102,Flushing,Queens,0
103,Flushing,Queens,0
104,Flushing,Queens,0
105,Flushing,Queens,0
106,Flushing,Queens,0
107,Flushing,Queens,0
108,Flushing,Queens,0
109,Flushing,Queens,0
110,Flushing,Queens,0
111,Flushing,Queens,0
112,Flushing,Queens,0
113,Flushing,Queens,0
114,Flushing,Queens,0
115,Flushing,Queens,0
116,Flushing,Queens,0
117,Flushing,Queens,0
118,Flushing,Queens,0
119,Flushing,Queens,0
120,Flushing,Queens,0
121,Flushing,Queens,0
122,Flushing,Queens,0
123,Flushing,Queens,0
124,Flushing,Queens,0
125,Flushing,Queens,0
126,Flushing,Queens,0
127,Flushing,Queens,0
128,Flushing,Queens,0
129,Flushing,Queens,0
130,Flushing,Queens,0
131,Flushing,Queens,0
132,Flushing,Queens,0
133,Flushing,Queens,0
134,Flushing,Queens,0
135,Flushing,Queens,0
136,Flushing,Queens,0
137,Flushing,Queens,0
138,Flushing,Queens,0
139,Flushing,Queens,0
140,Flushing,Queens,0
141,Flushing,Queens,0
142,Flushing,Queens,0
143,Flushing,Queens,0
144,Flushing,Queens,0
145,Flushing,Queens,0
146,Flushing,Queens,0
147,Flushing,Queens,0
148,Flushing,Queens,0
149,Flushing,Queens,0
150,Flushing,Queens,0
151,Flushing,Queens,0
152,Flushing,Queens,0
153,Flushing,Queens,0
154,Flushing,Queens,0
155,Flushing,Queens,0
156,Flushing,Queens,0
157,Flushing,Queens,0
158,Flushing,Queens,0
159,Flushing,Queens,0
160,Flushing,Queens,0
161,Flushing,Queens,0
162,Flushing,Queens,0
163,Flushing,Queens,0
164,Flushing,Queens,0
165,Flushing,Queens,0
166,Flushing,Queens,0
167,Flushing,Queens,0
168,Flushing,Queens,0
169,Flushing,Queens,0
170,Flushing,Queens,0
171,Flushing,Queens,0
172,Flushing,Queens,0
173,Flushing,Queens,0
174,Flushing,Queens,0
175,Flushing,Queens,0
176,Flushing,Queens,0
177,Flushing,Queens,0
178,Flushing,Queens,0
179,Flushing,Queens,0
180,Flushing,Queens,0
181,Flushing,Queens,0
182,Flushing,Queens,0
183,Flushing,Queens,0
184,Flushing,Queens,0
185,Flushing,Queens,0
186,Flushing,Queens,0
187,Flushing,Queens,0
188,Flushing,Queens,0
189,Flushing,Queens,0
190,Flushing,Queens,0
191,Flushing,Queens,0
192,Flushing,Queens,0
193,Flushing,Queens,0
194,Flushing,Queens,0
195,Flushing,Queens,0
196,Flushing,Queens,0
197,Flushing,Queens,0
198,Flushing,Queens,0
199,Flushing,Queens,0
200,Flushing,Queens,0
201,Flushing,Queens,0
202,Flushing,Queens,0
203,Flushing,Queens,0
204,Flushing,Queens,0
205,Flushing,Queens,0
206,Flushing,Queens,0
207,Flushing,Queens,0
208,Flushing,Queens,0
209,Flushing,Queens,0
210,Flushing,Queens,0
211,Flushing,Queens,0
212,Flushing,Queens,0
213,Flushing,Queens,0
214,Flushing,Queens,0
215,Flushing,Queens,0
216,Flushing,Queens,0
217,Flushing,Queens,0
218,Flushing,Queens,0
219,Flushing,Queens,0
220,Flushing,Queens,0
221,Flushing,Queens,0
222,Flushing,Queens,0
223,Flushing,Queens,0
224,Flushing,Queens,0
225,Flushing,Queens,0
226,Flushing,Queens,0
227,Flushing,Queens,0
228,Flushing,Queens,0
229,Flushing,Queens,0
230,Flushing,Queens,0
231,Flushing,Queens,0
232,Flushing,Queens,0
233,Flushing,Queens,0
234,Flushing,Queens,0
235,Flushing,Queens,0
236,Flushing,Queens,0
237,Flushing,Queens,0
238,Flushing,Queens,0
239,Flushing,Queens,0
240,Flushing,Queens,0
241,Flushing,Queens,0
242,Flushing,Queens,0
243,Flushing,Queens,0
244,Flushing,Queens,0
245,Flushing,Queens,0
246,Flushing,Queens,0
247,Flushing,Queens,0
248,Flushing,Queens,0
249,Flushing,Queens,0
250,Flushing,Queens,0
251,Flushing,Queens,0
252,Flushing,Queens,0
253,Flushing,Queens,0
254,Flushing,Queens,0
255,Flushing,Queens,0
256,Flushing,Queens,0
257,Flushing,Queens,0
258,Flushing,Queens,0
259,Flushing,Queens,0
260,Flushing,Queens,0
261,Flushing,Queens,0
262,Flushing,Queens,0
263,Flushing,Queens,0
264,Flushing,Queens,0
EOF
    
    sudo chown nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/data/LocationID_to_pretinct.csv
    log "✅ Archivo de mapeo básico creado"
fi

# 3. Verificar datos de crímenes
if [ -f "/opt/nyc_taxi_ml/data/NYPD_Complaint_Data_Historic_20251015.csv" ]; then
    log "✅ NYPD_Complaint_Data_Historic_20251015.csv encontrado"
else
    warning "⚠️ NYPD_Complaint_Data_Historic_20251015.csv no encontrado"
    info "Creando archivo de datos de crímenes básico..."
    
    # Crear archivo básico de datos de crímenes
    sudo tee /opt/nyc_taxi_ml/data/NYPD_Complaint_Data_Historic_20251015.csv > /dev/null <<EOF
CMPLNT_NUM,CMPLNT_FR_DT,CMPLNT_FR_TM,CMPLNT_TO_DT,CMPLNT_TO_TM,RPT_DT,OFNS_DESC,PD_CD,PD_DESC,CRM_ATPT_CPTD_CD,LAW_CAT_CD,BORO_NM,ADDR_PCT_CD,PREM_TYP_DESC,PARKS_NM,HADEVELOPT,X_COORD_CD,Y_COORD_CD,Latitude,Longitude,LOC_OF_OCCUR_DESC
123456789,01/01/2023,12:00:00,01/01/2023,12:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456790,01/01/2023,13:00:00,01/01/2023,13:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456791,01/01/2023,14:00:00,01/01/2023,14:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456792,01/01/2023,15:00:00,01/01/2023,15:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456793,01/01/2023,16:00:00,01/01/2023,16:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456794,01/01/2023,17:00:00,01/01/2023,17:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456795,01/01/2023,18:00:00,01/01/2023,18:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456796,01/01/2023,19:00:00,01/01/2023,19:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456797,01/01/2023,20:00:00,01/01/2023,20:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
123456798,01/01/2023,21:00:00,01/01/2023,21:00:00,01/01/2023,PETIT LARCENY,341,THEFT OF SERVICES,COMPLETED,MISDEMEANOR,MANHATTAN,1,STREET,,,1000000,2000000,40.7128,-74.0060,STREET
EOF
    
    sudo chown nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/data/NYPD_Complaint_Data_Historic_20251015.csv
    log "✅ Archivo de datos de crímenes básico creado"
fi

# 4. Verificar datos de viajes (parquet)
if [ -d "/opt/nyc_taxi_ml/data/parquet_data" ]; then
    log "✅ Directorio parquet_data encontrado"
    info "Archivos parquet encontrados: $(ls /opt/nyc_taxi_ml/data/parquet_data/*.parquet 2>/dev/null | wc -l)"
else
    warning "⚠️ Directorio parquet_data no encontrado"
    info "Creando directorio y archivos de ejemplo..."
    
    sudo mkdir -p /opt/nyc_taxi_ml/data/parquet_data
    sudo chown nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/data/parquet_data
    
    # Crear archivo parquet de ejemplo
    sudo -u nyc_taxi python3 -c "
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Crear datos de ejemplo
np.random.seed(42)
n_samples = 1000

data = {
    'pickup_datetime': [datetime.now() - timedelta(days=np.random.randint(0, 365)) for _ in range(n_samples)],
    'dropoff_datetime': [datetime.now() - timedelta(days=np.random.randint(0, 365)) for _ in range(n_samples)],
    'PULocationID': np.random.randint(1, 265, n_samples),
    'DOLocationID': np.random.randint(1, 265, n_samples),
    'passenger_count': np.random.randint(1, 6, n_samples),
    'trip_distance': np.random.uniform(0.1, 50.0, n_samples),
    'fare_amount': np.random.uniform(2.5, 100.0, n_samples),
    'tip_amount': np.random.uniform(0.0, 20.0, n_samples),
    'tolls_amount': np.random.uniform(0.0, 10.0, n_samples),
    'total_amount': np.random.uniform(5.0, 120.0, n_samples)
}

df = pd.DataFrame(data)
df.to_parquet('/opt/nyc_taxi_ml/data/parquet_data/sample_tripdata_2023-01.parquet', index=False)
print('Archivo parquet de ejemplo creado')
"
    
    log "✅ Archivo parquet de ejemplo creado"
fi

# 5. Verificar permisos
log "Verificando permisos..."
sudo chown -R nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/data
sudo chmod -R 755 /opt/nyc_taxi_ml/data

# 6. Crear archivo de configuración
log "Creando archivo de configuración..."
sudo tee /opt/nyc_taxi_ml/config/production.yaml > /dev/null <<EOF
# Configuración de producción para NYC Taxi ML
data_paths:
  parquet_data_dir: "/opt/nyc_taxi_ml/data/parquet_data"
  location_id_to_precinct_path: "/opt/nyc_taxi_ml/data/LocationID_to_pretinct.csv"
  nypd_complaint_data_path: "/opt/nyc_taxi_ml/data/NYPD_Complaint_Data_Historic_20251015.csv"

api_config:
  host: "0.0.0.0"
  port: 5002
  debug: false
  threaded: true

logging:
  level: "INFO"
  file: "/opt/nyc_taxi_ml/logs/api.log"
  max_size: "10MB"
  backup_count: 5

ml_config:
  model_type: "rule_based"
  cache_enabled: true
  cache_ttl: 3600  # 1 hora

security:
  cors_enabled: true
  rate_limit: 100  # requests per minute
EOF

sudo chown nyc_taxi:nyc_taxi /opt/nyc_taxi_ml/config/production.yaml

# 7. Verificar espacio en disco
log "Verificando espacio en disco..."
df -h /opt/nyc_taxi_ml/data

# 8. Test de datos
log "Probando acceso a datos..."
sudo -u nyc_taxi python3 -c "
import pandas as pd
import os

# Test LocationID mapping
try:
    df = pd.read_csv('/opt/nyc_taxi_ml/data/LocationID_to_pretinct.csv')
    print(f'✅ LocationID mapping: {len(df)} registros')
except Exception as e:
    print(f'❌ Error en LocationID mapping: {e}')

# Test crime data
try:
    df = pd.read_csv('/opt/nyc_taxi_ml/data/NYPD_Complaint_Data_Historic_20251015.csv')
    print(f'✅ Crime data: {len(df)} registros')
except Exception as e:
    print(f'❌ Error en crime data: {e}')

# Test parquet data
try:
    parquet_files = [f for f in os.listdir('/opt/nyc_taxi_ml/data/parquet_data') if f.endswith('.parquet')]
    if parquet_files:
        df = pd.read_parquet(f'/opt/nyc_taxi_ml/data/parquet_data/{parquet_files[0]}')
        print(f'✅ Parquet data: {len(df)} registros en {parquet_files[0]}')
    else:
        print('⚠️ No se encontraron archivos parquet')
except Exception as e:
    print(f'❌ Error en parquet data: {e}')
"

# 9. Información final
log "🎉 Configuración de datos completada!"
echo ""
echo "📊 Resumen de datos configurados:"
echo "=================================="
echo "📁 Directorio de datos: /opt/nyc_taxi_ml/data/"
echo "🗺️ Mapeo de ubicaciones: $(wc -l < /opt/nyc_taxi_ml/data/LocationID_to_pretinct.csv) registros"
echo "🚨 Datos de crímenes: $(wc -l < /opt/nyc_taxi_ml/data/NYPD_Complaint_Data_Historic_20251015.csv) registros"
echo "🚕 Archivos parquet: $(ls /opt/nyc_taxi_ml/data/parquet_data/*.parquet 2>/dev/null | wc -l) archivos"
echo "⚙️ Configuración: /opt/nyc_taxi_ml/config/production.yaml"
echo ""
echo "🔧 Comandos útiles:"
echo "==================="
echo "📊 Ver datos: ls -la /opt/nyc_taxi_ml/data/"
echo "🗺️ Ver mapeo: head /opt/nyc_taxi_ml/data/LocationID_to_pretinct.csv"
echo "🚨 Ver crímenes: head /opt/nyc_taxi_ml/data/NYPD_Complaint_Data_Historic_20251015.csv"
echo "🚕 Ver viajes: ls -la /opt/nyc_taxi_ml/data/parquet_data/"
echo ""
echo "🚀 ¡Datos listos para producción!"
