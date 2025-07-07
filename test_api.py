import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_aviation_api():
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': api_key,
        'limit': 10,
        'flight_status': 'active'
    }
    
    try:
        print("Testing API connection...")
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'error' in data:
            print(f"API Error: {data['error']}")
            return
            
        flights = data.get('data', [])
        print(f"\nSuccessfully retrieved {len(flights)} flights")
        
        if flights:
            print("\nSample flight data:")
            flight = flights[0]
            print(f"Flight: {flight.get('airline', {}).get('name')} {flight.get('flight', {}).get('iata')}")
            print(f"From: {flight.get('departure', {}).get('airport')} ({flight.get('departure', {}).get('country')})")
            print(f"To: {flight.get('arrival', {}).get('airport')} ({flight.get('arrival', {}).get('country')})")
            
    except Exception as e:
        print(f"Error testing API: {e}")

if __name__ == "__main__":
    test_aviation_api() 