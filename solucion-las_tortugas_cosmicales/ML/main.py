import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime
import joblib

def load_and_preprocess_data(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Convert date and time columns
    df['DATETIME'] = pd.to_datetime(df['CMPLNT_FR_DT'] + ' ' + df['CMPLNT_FR_TM'])
    
    # Extract hour from datetime
    df['HOUR'] = df['DATETIME'].dt.hour
    
    # Create crime severity score
    severity_dict = {
        'VIOLATION': 1,
        'MISDEMEANOR': 2,
        'FELONY': 3
    }
    df['SEVERITY_SCORE'] = df['LAW_CAT_CD'].map(severity_dict)
    
    return df

def create_safety_index(df):
    # Group by precinct and hour to create safety index
    safety_data = df.groupby(['ADDR_PCT_CD', 'HOUR']).agg({
        'SEVERITY_SCORE': ['count', 'mean']
    }).reset_index()
    
    # Flatten column names
    safety_data.columns = ['PRECINCT', 'HOUR', 'INCIDENT_COUNT', 'AVG_SEVERITY']
    
    # Calculate safety index (inverse of weighted score)
    # Higher number of incidents and higher severity = lower safety
    safety_data['SAFETY_INDEX'] = 1 / (safety_data['INCIDENT_COUNT'] * safety_data['AVG_SEVERITY'])
    
    # Normalize safety index to 0-100 scale
    scaler = StandardScaler()
    safety_data['SAFETY_INDEX'] = scaler.fit_transform(safety_data[['SAFETY_INDEX']])
    safety_data['SAFETY_INDEX'] = (safety_data['SAFETY_INDEX'] * 20) + 50  # Scale to mean of 50
    
    # Clip values to 0-100 range
    safety_data['SAFETY_INDEX'] = safety_data['SAFETY_INDEX'].clip(0, 100)
    
    return safety_data

def train_safety_model(safety_data):
    # Prepare features and target
    X = safety_data[['PRECINCT', 'HOUR']]
    y = safety_data['SAFETY_INDEX']
    
    # Train Random Forest model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model

def predict_route_safety(model, start_precinct, end_precinct, hour):
    # Predict safety scores for start and end points
    start_safety = model.predict([[start_precinct, hour]])[0]
    end_safety = model.predict([[end_precinct, hour]])[0]
    
    # Average safety score for the route
    route_safety = (start_safety + end_safety) / 2
    
    return route_safety

def suggest_safer_hours(model, start_precinct, end_precinct, current_hour):
    safety_scores = []
    
    # Check safety scores for all hours
    for hour in range(24):
        safety = predict_route_safety(model, start_precinct, end_precinct, hour)
        safety_scores.append((hour, safety))
    
    # Sort by safety score
    safety_scores.sort(key=lambda x: x[1], reverse=True)
    
    return safety_scores[:5]  # Return top 5 safest hours

def main():
    # Load and process data
    df = load_and_preprocess_data('NYC_complaint_data.csv')
    
    # Create safety index
    safety_data = create_safety_index(df)
    
    # Train model
    model = train_safety_model(safety_data)
    
    # Save the model
    joblib.dump(model, 'safety_model.joblib')
    
    # Example usage
    print("Safety Index Model Demo")
    print("-----------------------")
    
    # Example route
    start_precinct = 1
    end_precinct = 10
    current_hour = datetime.now().hour
    
    # Get current route safety
    route_safety = predict_route_safety(model, start_precinct, end_precinct, current_hour)
    print(f"\nRoute safety score (0-100) at current hour ({current_hour}:00): {route_safety:.2f}")
    
    # Get safer hours suggestions
    safer_hours = suggest_safer_hours(model, start_precinct, end_precinct, current_hour)
    print("\nSafest hours to travel this route:")
    for hour, safety in safer_hours:
        print(f"{hour:02d}:00 - Safety Score: {safety:.2f}")

if __name__ == "__main__":
    main()
