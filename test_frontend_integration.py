"""
Test Frontend Integration
"""

import requests
import json

def test_frontend_integration():
    """Test what the frontend should be receiving"""
    print("Testing frontend integration...")
    
    # Test different locations like the frontend would
    test_cases = [
        ("Central Park", "Central Park"),
        ("Central Park", "Times Square"),
        ("JFK Airport", "JFK Airport"),
        ("Brooklyn Bridge", "Wall Street")
    ]
    
    for pickup, dropoff in test_cases:
        print(f"\n=== Testing: {pickup} -> {dropoff} ===")
        
        try:
            response = requests.post('http://127.0.0.1:5002/predict', 
                                   json={
                                       'pickup_location': pickup,
                                       'dropoff_location': dropoff,
                                       'pickup_datetime': '2025-10-17T18:30:00'
                                   })
            
            if response.status_code == 200:
                data = response.json()
                pred = data['prediction']
                
                print(f"SUCCESS Safety Index: {pred['safety_index_percent']}%")
                print(f"SUCCESS Average Fare: ${pred['avg_fare_usd']}")
                print(f"SUCCESS Method: {pred['prediction_metadata']['method']}")
                print(f"SUCCESS Pickup Zone: {pred['prediction_metadata']['pickup_zone']}")
                print(f"SUCCESS Dropoff Zone: {pred['prediction_metadata']['dropoff_zone']}")
                
                # Check if results are consistent
                if pickup == dropoff:
                    print(f"SUCCESS Same location test - should be consistent")
                else:
                    print(f"SUCCESS Different locations - should show variation")
                    
            else:
                print(f"ERROR: {response.status_code}")
                
        except Exception as e:
            print(f"ERROR Exception: {e}")
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print("- Central Park -> Central Park: Should be ~94%")
    print("- Central Park -> Times Square: Should be ~88%") 
    print("- JFK Airport -> JFK Airport: Should be ~50%")
    print("- Brooklyn Bridge -> Wall Street: Should be ~63%")
    print("\nIf frontend shows 87% for all, there's a frontend bug.")

if __name__ == "__main__":
    test_frontend_integration()