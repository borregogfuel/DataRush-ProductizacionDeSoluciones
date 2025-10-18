"""
NYC Taxi ML - Rule-Based System
Deterministic predictions based on NYC patterns and rules
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RuleBasedML:
    """Rule-based ML system for NYC taxi predictions"""
    
    def __init__(self):
        self.location_patterns = self._load_location_patterns()
        self.hourly_patterns = self._load_hourly_patterns()
        self.borough_patterns = self._load_borough_patterns()
        
    def _load_location_patterns(self) -> Dict[int, Dict]:
        """Load specific patterns for known NYC locations"""
        return {
            # Manhattan - High safety, high fare
            74: {'safety_base': 0.94, 'fare_base': 18.50, 'borough': 'Manhattan', 'zone': 'Central Park'},
            151: {'safety_base': 0.88, 'fare_base': 22.00, 'borough': 'Manhattan', 'zone': 'Times Square'},
            114: {'safety_base': 0.82, 'fare_base': 19.50, 'borough': 'Manhattan', 'zone': 'Empire State'},
            90: {'safety_base': 0.85, 'fare_base': 21.00, 'borough': 'Manhattan', 'zone': 'Wall Street'},
            87: {'safety_base': 0.88, 'fare_base': 25.00, 'borough': 'Manhattan', 'zone': 'Statue of Liberty'},
            100: {'safety_base': 0.80, 'fare_base': 20.00, 'borough': 'Manhattan', 'zone': 'Soho'},
            
            # Brooklyn - Moderate safety, moderate fare
            1: {'safety_base': 0.70, 'fare_base': 15.00, 'borough': 'Brooklyn', 'zone': 'Brooklyn Bridge'},
            
            # Queens - Lower safety, lower fare
            138: {'safety_base': 0.65, 'fare_base': 12.00, 'borough': 'Queens', 'zone': 'Queens'},
            132: {'safety_base': 0.68, 'fare_base': 35.00, 'borough': 'Queens', 'zone': 'JFK Airport'},
            
            # Bronx - Lower safety, lower fare
            1: {'safety_base': 0.60, 'fare_base': 11.00, 'borough': 'Bronx', 'zone': 'Bronx'},
        }
    
    def _load_hourly_patterns(self) -> Dict[int, Dict]:
        """Load hourly safety and fare patterns"""
        return {
            # Hour: {safety_modifier, fare_modifier, description}
            0: {'safety_mod': -0.15, 'fare_mod': 1.5, 'desc': 'Late night'},
            1: {'safety_mod': -0.20, 'fare_mod': 1.6, 'desc': 'Late night'},
            2: {'safety_mod': -0.25, 'fare_mod': 1.7, 'desc': 'Late night'},
            3: {'safety_mod': -0.20, 'fare_mod': 1.6, 'desc': 'Late night'},
            4: {'safety_mod': -0.15, 'fare_mod': 1.5, 'desc': 'Early morning'},
            5: {'safety_mod': -0.10, 'fare_mod': 1.3, 'desc': 'Early morning'},
            6: {'safety_mod': 0.05, 'fare_mod': 1.2, 'desc': 'Morning rush'},
            7: {'safety_mod': 0.10, 'fare_mod': 1.3, 'desc': 'Morning rush'},
            8: {'safety_mod': 0.08, 'fare_mod': 1.4, 'desc': 'Morning rush'},
            9: {'safety_mod': 0.05, 'fare_mod': 1.2, 'desc': 'Morning'},
            10: {'safety_mod': 0.02, 'fare_mod': 1.0, 'desc': 'Mid morning'},
            11: {'safety_mod': 0.00, 'fare_mod': 1.0, 'desc': 'Mid morning'},
            12: {'safety_mod': 0.00, 'fare_mod': 1.0, 'desc': 'Lunch time'},
            13: {'safety_mod': 0.00, 'fare_mod': 1.0, 'desc': 'Afternoon'},
            14: {'safety_mod': 0.00, 'fare_mod': 1.0, 'desc': 'Afternoon'},
            15: {'safety_mod': 0.00, 'fare_mod': 1.0, 'desc': 'Afternoon'},
            16: {'safety_mod': 0.00, 'fare_mod': 1.0, 'desc': 'Afternoon'},
            17: {'safety_mod': -0.05, 'fare_mod': 1.3, 'desc': 'Evening rush'},
            18: {'safety_mod': -0.08, 'fare_mod': 1.4, 'desc': 'Evening rush'},
            19: {'safety_mod': -0.05, 'fare_mod': 1.3, 'desc': 'Evening rush'},
            20: {'safety_mod': -0.02, 'fare_mod': 1.1, 'desc': 'Evening'},
            21: {'safety_mod': -0.05, 'fare_mod': 1.2, 'desc': 'Evening'},
            22: {'safety_mod': -0.10, 'fare_mod': 1.3, 'desc': 'Night'},
            23: {'safety_mod': -0.12, 'fare_mod': 1.4, 'desc': 'Night'},
        }
    
    def _load_borough_patterns(self) -> Dict[str, Dict]:
        """Load borough-based patterns"""
        return {
            'Manhattan': {'safety_mod': 0.15, 'fare_mod': 1.4, 'base_fare': 15.00},
            'Brooklyn': {'safety_mod': 0.00, 'fare_mod': 1.0, 'base_fare': 12.00},
            'Queens': {'safety_mod': -0.10, 'fare_mod': 0.8, 'base_fare': 10.00},
            'Bronx': {'safety_mod': -0.15, 'fare_mod': 0.7, 'base_fare': 9.00},
            'Staten Island': {'safety_mod': -0.05, 'fare_mod': 0.9, 'base_fare': 11.00},
        }
    
    def _get_location_info(self, location_id: int) -> Dict:
        """Get location-specific information"""
        if location_id in self.location_patterns:
            return self.location_patterns[location_id]
        
        # Default patterns based on location ID ranges
        if 1 <= location_id <= 100:
            return {'safety_base': 0.80, 'fare_base': 18.00, 'borough': 'Manhattan', 'zone': f'Manhattan Zone {location_id}'}
        elif 101 <= location_id <= 200:
            return {'safety_base': 0.70, 'fare_base': 14.00, 'borough': 'Brooklyn', 'zone': f'Brooklyn Zone {location_id}'}
        elif 201 <= location_id <= 264:
            return {'safety_base': 0.65, 'fare_base': 12.00, 'borough': 'Queens', 'zone': f'Queens Zone {location_id}'}
        else:
            return {'safety_base': 0.60, 'fare_base': 10.00, 'borough': 'Unknown', 'zone': f'Zone {location_id}'}
    
    def _calculate_distance_factor(self, pickup_id: int, dropoff_id: int) -> float:
        """Calculate distance factor between locations"""
        # Simple distance calculation based on location IDs
        distance = abs(pickup_id - dropoff_id) / 10.0
        distance = max(0.5, min(20, distance))  # Between 0.5 and 20 miles
        return distance
    
    def predict_route(self, pickup_location_id: int, dropoff_location_id: int, pickup_datetime: datetime) -> Dict[str, Any]:
        """Predict safety and fare for a route"""
        logger.info(f"Predicting route: {pickup_location_id} -> {dropoff_location_id} at {pickup_datetime}")
        
        # Get location information
        pickup_info = self._get_location_info(pickup_location_id)
        dropoff_info = self._get_location_info(dropoff_location_id)
        
        # Get hourly patterns
        hour = pickup_datetime.hour
        hourly_pattern = self.hourly_patterns[hour]
        
        # Get borough patterns
        pickup_borough = pickup_info['borough']
        dropoff_borough = dropoff_info['borough']
        pickup_borough_pattern = self.borough_patterns.get(pickup_borough, self.borough_patterns['Brooklyn'])
        dropoff_borough_pattern = self.borough_patterns.get(dropoff_borough, self.borough_patterns['Brooklyn'])
        
        # Calculate base safety (average of pickup and dropoff)
        base_safety = (pickup_info['safety_base'] + dropoff_info['safety_base']) / 2
        
        # Apply hourly modifier
        safety_index = base_safety + hourly_pattern['safety_mod']
        
        # Apply borough modifier
        safety_index += (pickup_borough_pattern['safety_mod'] + dropoff_borough_pattern['safety_mod']) / 2
        
        # Ensure safety is between 0 and 1
        safety_index = max(0.0, min(1.0, safety_index))
        
        # Calculate fare
        base_fare = (pickup_info['fare_base'] + dropoff_info['fare_base']) / 2
        
        # Apply distance factor
        distance_factor = self._calculate_distance_factor(pickup_location_id, dropoff_location_id)
        fare = base_fare + (distance_factor * 2.5)
        
        # Apply hourly modifier
        fare *= hourly_pattern['fare_mod']
        
        # Apply borough modifier
        fare *= (pickup_borough_pattern['fare_mod'] + dropoff_borough_pattern['fare_mod']) / 2
        
        # Ensure minimum fare
        fare = max(2.50, fare)
        
        # Generate hourly safety pattern
        safety_by_hours = self._generate_hourly_safety_pattern(pickup_location_id, dropoff_location_id)
        
        # Find safest times
        safest_times = self._find_safest_times(safety_by_hours)
        
        return {
            'pickup_location_id': pickup_location_id,
            'dropoff_location_id': dropoff_location_id,
            'pickup_datetime': pickup_datetime.isoformat(),
            'safety_index_percent': round(safety_index * 100, 2),
            'avg_fare_usd': round(fare, 2),
            'safety_by_hours': safety_by_hours,
            'safest_times': safest_times,
            'prediction_metadata': {
                'model_version': '2.0',
                'prediction_time': datetime.now().isoformat(),
                'method': 'rule_based_deterministic',
                'pickup_zone': pickup_info['zone'],
                'dropoff_zone': dropoff_info['zone'],
                'pickup_borough': pickup_borough,
                'dropoff_borough': dropoff_borough
            }
        }
    
    def _generate_hourly_safety_pattern(self, pickup_id: int, dropoff_id: int) -> List[Dict]:
        """Generate 24-hour safety pattern"""
        pickup_info = self._get_location_info(pickup_id)
        dropoff_info = self._get_location_info(dropoff_id)
        base_safety = (pickup_info['safety_base'] + dropoff_info['safety_base']) / 2
        
        safety_by_hours = []
        for hour in range(24):
            hourly_pattern = self.hourly_patterns[hour]
            hourly_safety = base_safety + hourly_pattern['safety_mod']
            hourly_safety = max(0.0, min(1.0, hourly_safety))
            
            safety_by_hours.append({
                'hour': hour,
                'safety_percent': round(hourly_safety * 100, 1),
                'time_label': f"{hour:02d}:00 - {(hour+1)%24:02d}:00"
            })
        
        return safety_by_hours
    
    def _find_safest_times(self, safety_by_hours: List[Dict]) -> List[Dict]:
        """Find the 3 safest times"""
        sorted_times = sorted(safety_by_hours, key=lambda x: x['safety_percent'], reverse=True)
        return sorted_times[:3]

def main():
    """CLI interface for rule-based ML"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NYC Taxi Rule-Based ML CLI')
    parser.add_argument('command', choices=['predict'], help='Comando a ejecutar')
    parser.add_argument('--pu', type=int, required=True, help='Pickup Location ID (1-264)')
    parser.add_argument('--do', type=int, required=True, help='Dropoff Location ID (1-264)')
    parser.add_argument('--dt', required=True, help='Pickup datetime (YYYY-MM-DD HH:MM:SS)')
    
    args = parser.parse_args()
    
    if args.command == 'predict':
        try:
            # Validate LocationIDs
            if not (1 <= args.pu <= 264):
                print(json.dumps({'error': f'Pickup Location ID {args.pu} fuera de rango (1-264)'}))
                return
            
            if not (1 <= args.do <= 264):
                print(json.dumps({'error': f'Dropoff Location ID {args.do} fuera de rango (1-264)'}))
                return
            
            # Parse datetime
            pickup_datetime = pd.to_datetime(args.dt)
            
            # Create ML system and predict
            ml_system = RuleBasedML()
            result = ml_system.predict_route(args.pu, args.do, pickup_datetime)
            
            print(json.dumps(result, indent=2))
                
        except Exception as e:
            print(json.dumps({'error': f'Error: {str(e)}'}))

if __name__ == "__main__":
    main()
