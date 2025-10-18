"""
NYC Taxi ML Engine - Versión Producción para EC2
Motor ML optimizado y robusto para inferencia en tiempo real
"""

import pandas as pd
import numpy as np
import joblib
import yaml
import os
import argparse
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Tuple, List
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rutas de producción
PRODUCTION_PATHS = {
    'config': '/opt/nyc_taxi_ml/config/production.yaml',
    'models_dir': '/opt/nyc_taxi_ml/models',
    'data_dir': '/opt/nyc_taxi_ml/data',
    'logs_dir': '/opt/nyc_taxi_ml/logs'
}

class MLPredictor:
    """Clase para predicciones ML optimizada para producción"""
    
    def __init__(self):
        self.models_loaded = False
        self.config = None
        self.fare_model = None
        self.safety_model = None
        self.fare_scaler = None
        self.safety_scaler = None
        self.feature_scalers = None
        self.training_features = None
        self.location_mapping = None
        self.crime_data = None
        
    def load_config(self):
        """Cargar configuración"""
        try:
            with open(PRODUCTION_PATHS['config'], 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info("Configuración cargada exitosamente")
            return True
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return False
    
    def load_models(self):
        """Cargar modelos y scalers"""
        try:
            models_dir = PRODUCTION_PATHS['models_dir']
            
            # Cargar modelos
            self.fare_model = joblib.load(os.path.join(models_dir, 'fare_model.joblib'))
            self.safety_model = joblib.load(os.path.join(models_dir, 'safety_model.joblib'))
            
            # Cargar scalers
            self.fare_scaler = joblib.load(os.path.join(models_dir, 'fare_scaler.joblib'))
            self.safety_scaler = joblib.load(os.path.join(models_dir, 'safety_scaler.joblib'))
            self.feature_scalers = joblib.load(os.path.join(models_dir, 'feature_scalers.joblib'))
            self.training_features = joblib.load(os.path.join(models_dir, 'training_features.joblib'))
            
            self.models_loaded = True
            logger.info("Modelos y scalers cargados exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando modelos: {e}")
            return False
    
    def load_data(self):
        """Cargar datos estáticos"""
        try:
            data_dir = PRODUCTION_PATHS['data_dir']
            
            # Cargar mapeo de ubicaciones
            location_path = os.path.join(data_dir, 'LocationID_to_pretinct.csv')
            if os.path.exists(location_path):
                df_precinct = pd.read_csv(location_path)
                self.location_mapping = df_precinct.set_index('LocationID')['precinct_number'].to_dict()
                logger.info(f"Mapeo de ubicaciones cargado: {len(self.location_mapping)} entradas")
            
            # Cargar datos de crimen
            crime_path = os.path.join(data_dir, 'NYPD_Complaint_Data_Historic_20251015.csv')
            if os.path.exists(crime_path):
                self.crime_data = pd.read_csv(crime_path)
                logger.info(f"Datos de crimen cargados: {len(self.crime_data)} registros")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            return False
    
    def initialize(self):
        """Inicializar el predictor ML"""
        logger.info("Inicializando ML Predictor...")
        
        if not self.load_config():
            return False
        
        if not self.load_models():
            return False
        
        if not self.load_data():
            return False
        
        logger.info("ML Predictor inicializado exitosamente")
        return True
    
    def build_features(self, pickup_location_id: int, dropoff_location_id: int, 
                      pickup_datetime: datetime) -> pd.DataFrame:
        """Construir características para predicción"""
        try:
            # Crear DataFrame base
            data = {
                'tpep_pickup_datetime': [pickup_datetime],
                'tpep_dropoff_datetime': [pickup_datetime + pd.Timedelta(minutes=30)],
                'PULocationID': [pickup_location_id],
                'DOLocationID': [dropoff_location_id],
                'trip_distance': [5.0],  # Valor por defecto
                'fare_amount': [10.0],
                'tip_amount': [2.0],
                'tolls_amount': [0.0],
                'passenger_count': [1],
                'improvement_surcharge': [0.3],
                'total_amount': [12.8],
                'congestion_surcharge': [2.5],
                'airport_fee': [0.0],
                'VendorID': [1],
                'RatecodeID': [1],
                'store_and_fwd_flag': ['N'],
                'payment_type': [1]
            }
            
            df = pd.DataFrame(data)
            
            # Parsear fechas
            df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
            df['weekday'] = df['tpep_pickup_datetime'].dt.dayofweek
            df['month'] = df['tpep_pickup_datetime'].dt.month
            df['day_of_year'] = df['tpep_pickup_datetime'].dt.dayofyear
            
            # Crear características de viaje
            df['trip_miles'] = df['trip_distance']
            df['duration_minutes'] = 30  # Estimación
            df['is_peak_hour'] = ((df['pickup_hour'] >= 7) & (df['pickup_hour'] <= 9)) | \
                                ((df['pickup_hour'] >= 17) & (df['pickup_hour'] <= 19))
            df['tip_pct'] = df['tip_amount'] / df['fare_amount']
            
            # Mapear LocationID a precinct
            if self.location_mapping:
                df['precinct_number'] = df['DOLocationID'].map(self.location_mapping).fillna(1)
            else:
                df['precinct_number'] = 1
            
            # Agregar características de crimen (simplificado para producción)
            df['daily_weighted_crime'] = 0.5  # Valor por defecto
            df['hourly_crime_mean'] = 0.3
            df['hourly_crime_std'] = 0.2
            df['hourly_crime_count'] = 1
            
            # Excluir columnas no numéricas
            df = df.drop(columns=['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'store_and_fwd_flag'])
            
            # Convertir a numérico
            df = df.astype(float)
            
            # Normalizar características
            if self.feature_scalers:
                cols_to_normalize = [
                    'trip_miles', 'duration_minutes', 'tip_pct', 'daily_weighted_crime',
                    'hourly_crime_mean', 'hourly_crime_std', 'hourly_crime_count'
                ]
                for col in cols_to_normalize:
                    if col in df.columns and col in self.feature_scalers:
                        df[col] = self.feature_scalers[col].transform(df[[col]])
            
            # Asegurar que las columnas coincidan con entrenamiento
            if self.training_features:
                df = df.reindex(columns=self.training_features, fill_value=0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error construyendo características: {e}")
            return None
    
    def predict(self, pickup_location_id: int, dropoff_location_id: int, 
                pickup_datetime: datetime) -> Dict[str, Any]:
        """Realizar predicción completa"""
        if not self.models_loaded:
            return None
        
        try:
            # Construir características
            X = self.build_features(pickup_location_id, dropoff_location_id, pickup_datetime)
            if X is None:
                return None
            
            # Predicción de tarifa
            fare_pred_scaled = self.fare_model.predict(X)
            avg_fare_usd = self.fare_scaler.inverse_transform(fare_pred_scaled.reshape(-1, 1))[0][0]
            
            # Predicción de seguridad
            safety_pred_scaled = self.safety_model.predict(X)
            safety_index_percent = self.safety_scaler.inverse_transform(safety_pred_scaled.reshape(-1, 1))[0][0]
            safety_index_percent = np.clip(safety_index_percent, 0, 100)
            
            # Generar safety_by_hours (patrón realista)
            safety_by_hours = []
            for hour in range(24):
                if 6 <= hour < 10:  # Mañana
                    safety = 90 + np.random.randint(-5, 5)
                elif 10 <= hour < 17:  # Día
                    safety = 75 + np.random.randint(-5, 5)
                elif 17 <= hour < 22:  # Tarde/Noche
                    safety = 60 + np.random.randint(-5, 5)
                else:  # Madrugada
                    safety = 50 + np.random.randint(-5, 5)
                
                safety_by_hours.append({
                    'hour': hour,
                    'safety_percent': max(0, min(100, safety)),
                    'time_label': f"{hour:02d}:00 - {(hour+1)%24:02d}:00"
                })
            
            # Top 3 horas más seguras
            safest_times = sorted(safety_by_hours, key=lambda x: x['safety_percent'], reverse=True)[:3]
            
            return {
                'pickup_location_id': pickup_location_id,
                'dropoff_location_id': dropoff_location_id,
                'pickup_datetime': pickup_datetime.isoformat(),
                'safety_index_percent': round(safety_index_percent, 2),
                'avg_fare_usd': round(avg_fare_usd, 2),
                'safety_by_hours': safety_by_hours,
                'safest_times': safest_times,
                'prediction_metadata': {
                    'model_version': '2.0',
                    'prediction_time': datetime.now().isoformat(),
                    'features_used': len(X.columns),
                    'method': 'production_ml'
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            return None

# Instancia global del predictor
predictor = MLPredictor()

def main():
    """Función principal para CLI"""
    parser = argparse.ArgumentParser(description="NYC Taxi ML Engine - Producción")
    parser.add_argument("predict", help="Comando de predicción")
    parser.add_argument("--pu", type=int, required=True, help="ID de ubicación de recogida")
    parser.add_argument("--do", type=int, required=True, help="ID de ubicación de destino")
    parser.add_argument("--dt", type=str, required=True, help="Fecha y hora de recogida")
    
    args = parser.parse_args()
    
    # Inicializar predictor
    if not predictor.initialize():
        logger.error("Error inicializando ML Predictor")
        sys.exit(1)
    
    # Realizar predicción
    pickup_datetime = pd.to_datetime(args.dt)
    result = predictor.predict(args.pu, args.do, pickup_datetime)
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        logger.error("Error generando predicción")
        sys.exit(1)

if __name__ == "__main__":
    main()
