# NYC Taxi ML Models - AVG FARE & SAFETY INDEX

Este proyecto entrena dos modelos de machine learning para predecir el precio promedio de viajes y el índice de seguridad en NYC usando datos de taxis y crimen.

## Modelos

- **AVG FARE**: Predice el precio promedio de un viaje entre dos zonas
- **SAFETY INDEX**: Predice el índice de seguridad (0-100%) basado en datos de crimen y patrones de viaje

## Estructura del Proyecto

```
├── README.md
├── requirements.txt
├── config.yaml
├── src/
│   ├── __init__.py
│   ├── ingest.py          # Lectura de datos parquet y CSV
│   ├── features.py        # Ingeniería de características
│   ├── labeling.py        # Generación de etiquetas de seguridad
│   ├── models.py          # Entrenamiento de modelos
│   ├── pipeline.py        # Pipeline principal
│   ├── inference.py       # Predicciones en tiempo real
│   └── evaluation.py      # Métricas y evaluación
├── notebooks/
│   └── exploration.ipynb  # Análisis exploratorio
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py
│   ├── test_features.py
│   └── test_inference.py
└── data/
    ├── parquet_data/      # Datos de taxis (parquet)
    ├── LocationID_to_pretinct.csv
    └── NYPD_Complaint_Data_Historic_20251015.csv
```

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Edita `config.yaml` para especificar rutas de datos:

```yaml
data:
  parquet_path: "solucion-las_tortugas_cosmicales/ML/parquet_data"
  location_mapping: "solucion-las_tortugas_cosmicales/ML/LocationID_to_pretinct.csv"
  crime_data: "solucion-las_tortugas_cosmicales/ML/crime_data/NYPD_Complaint_Data_Historic_20251015.csv"

models:
  test_days: 30  # Días para test temporal
  safety_weights:
    crime: 0.6
    tip: 0.2
    frequency: 0.2
```

## Uso

### Entrenar modelos

```bash
python -m src.pipeline train
```

### Hacer predicciones

```bash
python -m src.inference predict --pu 74 --do 151 --dt "2025-10-16 18:30:00"
```

### Ejecutar tests

```bash
python -m pytest tests/
```

## Datos Requeridos

- **Parquet files**: Datos de taxis NYC (yellow, green, fhv, fhvhv)
- **LocationID_to_pretinct.csv**: Mapeo de zonas a precincts
- **NYPD_Complaint_Data_Historic_20251015.csv**: Datos de crimen

## Fórmula Safety Index

```
safety_raw = 0.6*(1 - crime_norm) + 0.2*tip_pct_norm + 0.2*trip_freq_norm
```

Donde:
- `crime_norm`: Crimen normalizado por precinct y ventana temporal
- `tip_pct_norm`: Porcentaje de propina normalizado
- `trip_freq_norm`: Frecuencia de viajes normalizada

## Modelos

- **LightGBM** con early stopping
- **Split temporal**: Últimos 30 días para test
- **Features**: Hora, día, distancia, crimen histórico, patrones de viaje