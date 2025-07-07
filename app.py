from flask import Flask, render_template, request
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import time
import google.generativeai as genai
from requests.auth import HTTPBasicAuth
from collections import defaultdict

load_dotenv()

app = Flask(__name__)
OPENSKY_USERNAME = "sweathabalaji03@gmail.com"
OPENSKY_PASSWORD = "bRjBUYuK27TVBtQ6rKEkYojAm0upbnpk"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Australian cities with their bounding boxes (longitude_min, latitude_min, longitude_max, latitude_max)
AUSTRALIAN_CITIES = {
    'Sydney': {
        'bbox': [150.5, -34.5, 151.5, -33.5]
    },
    'Melbourne': {
        'bbox': [144.5, -38.5, 145.5, -37.5]
    },
    'Brisbane': {
        'bbox': [152.5, -27.7, 153.5, -26.7]
    },
    'Perth': {
        'bbox': [115.5, -32.5, 116.5, -31.5]
    },
    'Adelaide': {
        'bbox': [138.3, -35.2, 139.3, -34.2]
    },
    'Gold Coast': {
        'bbox': [153.0, -28.5, 154.0, -27.5]
    },
    'Canberra': {
        'bbox': [148.9, -35.5, 149.9, -35.1]
    },
    'Darwin': {
        'bbox': [130.8, -12.5, 131.8, -12.1]
    }
}

def fetch_flight_data():
    """Fetch real-time flight data from OpenSky Network API"""
    base_url = "https://opensky-network.org/api"
    endpoint = "/states/all"
    url = base_url + endpoint
    all_flights = []
    
    try:
        print("\nFetching real-time flight data from OpenSky Network...")
        current_time = datetime.now()
        
        # Try anonymous access first since it's more reliable
        print("Trying anonymous access...")
        response = requests.get(url)
        
        if response.status_code == 200:
            print("Anonymous access successful")
            data = response.json()
            
            # Check data timestamp
            if 'time' in data:
                data_time = datetime.fromtimestamp(data['time'])
                time_diff = (current_time - data_time).total_seconds()
                print(f"\nData timestamp: {data_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Current time:   {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Data is {time_diff:.1f} seconds old")
            
            if 'states' in data and data['states']:
                total_flights = len(data['states'])
                print(f"\nFound {total_flights} total flights")
                
                # Process each flight state
                for state in data['states']:
                    if not state or len(state) < 12:  # Basic validation
                        continue
                        
                    if state[5] is not None and state[6] is not None:  # Check if position data exists
                        try:
                            longitude = float(state[5])
                            latitude = float(state[6])
                            timestamp = datetime.fromtimestamp(state[3]) if state[3] else current_time
                            
                            # Check if flight data is recent (within last 10 minutes)
                            time_diff = (current_time - timestamp).total_seconds()
                            if time_diff > 600:  # Skip flights with old data
                                continue
                            
                            # Debug coordinates for specific cities
                            if total_flights % 100 == 0:  # Print every 100th flight for debugging
                                print(f"\nFlight at coordinates: {latitude}, {longitude}")
                                print(f"Flight time: {timestamp.strftime('%H:%M:%S')} ({time_diff:.1f} seconds ago)")
                            
                            # Check if flight is in or near Australian airspace
                            for city, info in AUSTRALIAN_CITIES.items():
                                bbox = info['bbox']
                                if (bbox[0] <= longitude <= bbox[2] and 
                                    bbox[1] <= latitude <= bbox[3]):
                                    
                                    flight_data = {
                                        'icao24': state[0],
                                        'callsign': state[1].strip() if state[1] else 'Unknown',
                                        'origin_country': state[2],
                                        'longitude': longitude,
                                        'latitude': latitude,
                                        'altitude': state[7],
                                        'on_ground': state[8],
                                        'velocity': state[9],
                                        'true_track': state[10],
                                        'vertical_rate': state[11],
                                        'city': city,
                                        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                        'age': time_diff
                                    }
                                    
                                    all_flights.append(flight_data)
                                    if total_flights % 100 == 0:  # Debug print
                                        print(f"Added flight to {city}")
                                    break  # Found a matching city, move to next flight
                        except (ValueError, TypeError) as e:
                            print(f"Error processing flight data: {e}")
                            continue
                
                # Filter out old data
                recent_flights = [f for f in all_flights if f['age'] <= 600]  # Keep flights within last 10 minutes
                
                print(f"\nFound {len(all_flights)} total flights in Australian airspace")
                print(f"Of which {len(recent_flights)} are from the last 10 minutes")
                
                print("\nFlights by city (last 10 minutes):")
                city_counts = {}
                for flight in recent_flights:
                    city = flight['city']
                    city_counts[city] = city_counts.get(city, 0) + 1
                for city, count in sorted(city_counts.items()):
                    print(f"{city}: {count} flights")
                
                if recent_flights:
                    print("\nMost recent flight data:")
                    newest = min(recent_flights, key=lambda x: x['age'])
                    print(json.dumps(newest, indent=2))
                    print(f"Data age: {newest['age']:.1f} seconds")
                
                return recent_flights
            else:
                print("No flight states found in response")
                print("Response data:", data)  # Debug the response
                return []
        else:
            print(f"API Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(f"Error details: {str(e)}")
        return []

def process_data(flight_data, selected_city=None):
    """Process flight data with focus on Australian airspace"""
    if not flight_data:
        return [], [], None
        
    print(f"\nProcessing {len(flight_data)} flights...")
    
    # Convert to DataFrame
    df = pd.DataFrame(flight_data)
    
    # Filter by selected city if specified
    if selected_city:
        print(f"Filtering for {selected_city}")
        df = df[df['city'] == selected_city]
        print(f"Found {len(df)} flights in {selected_city}")
    
    if df.empty:
        print("No flights found after filtering")
        return [], [], None
    
    # Create meaningful route categories
    df['route_category'] = df.apply(lambda row: categorize_flight(row, selected_city), axis=1)
    
    # Group flights by route category and count
    route_series = df['route_category'].value_counts()
    routes = route_series.index.tolist()
    counts = route_series.values.tolist()
    
    # Debug output
    print("\nFlight Distribution:")
    for route, count in zip(routes, counts):
        print(f"{route}: {count} flights")
    
    return routes, counts, df

def categorize_flight(row, selected_city=None):
    """Categorize flight based on its characteristics"""
    if selected_city:
        # For selected city view
        if row['on_ground']:
            return f"{row['city']} (On Ground)"
        elif row['origin_country'] != 'Australia':
            return f"International → {row['city']}"
        else:
            return f"Domestic → {row['city']}"
    else:
        # For overall view
        if row['on_ground']:
            return f"{row['city']} (Ground)"
        elif row['origin_country'] != 'Australia':
            return f"{row['city']} (Int'l)"
        else:
            return f"{row['city']} (Dom)"

def generate_market_analysis(routes, counts, df, selected_city=None):
    """Generate market analysis using basic analytics when AI is unavailable"""
    if not routes or not counts:
        return "No Australian flights found in the current data. Please try again later."
    
    try:
        # Prepare data for analysis
        total_flights = sum(counts)
        city_distribution = [f"{route}: {count} flights" for route, count in zip(routes[:3], counts[:3])]
        
        # Calculate additional metrics
        avg_altitude = df['altitude'].mean() if 'altitude' in df else 0
        flights_on_ground = df['on_ground'].sum() if 'on_ground' in df else 0
        international_flights = df[df['origin_country'] != 'Australia'].shape[0] if 'origin_country' in df else 0
        
        # Generate basic analysis
        analysis_parts = []
        
        # Location context
        if selected_city:
            analysis_parts.append(f"📍 Analyzing {selected_city} airspace:")
        else:
            analysis_parts.append("📍 Analyzing all Australian airspace:")
        
        # Traffic overview
        analysis_parts.append(f"✈️ Currently tracking {total_flights} active flights")
        
        # City distribution
        if city_distribution:
            analysis_parts.append(f"🌆 Top areas: {', '.join(city_distribution)}")
        
        # International vs Domestic
        int_percentage = (international_flights / total_flights * 100) if total_flights > 0 else 0
        analysis_parts.append(f"🌏 International traffic: {int_percentage:.1f}% of flights")
        
        # Operational insights
        if flights_on_ground > 0:
            analysis_parts.append(f"🛬 {flights_on_ground} aircraft on ground")
        
        # Time context
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_context = "morning"
        elif 12 <= current_hour < 17:
            time_context = "afternoon"
        else:
            time_context = "evening"
        
        # Recommendations
        if int_percentage > 50:
            analysis_parts.append(f"💡 High international traffic - consider focusing on international traveler amenities")
        else:
            analysis_parts.append(f"💡 Mostly domestic traffic - optimize for local traveler preferences")
        
        analysis_parts.append(f"⏰ {time_context.capitalize()} traffic pattern")
        
        return " ".join(analysis_parts)
        
    except Exception as e:
        print(f"Error generating market analysis: {e}")
        return "Unable to generate market analysis at this time. Please try again later."

def generate_market_insights(flight_data):
    """Generate market insights using Google's Generative AI"""
    try:
        # Process flight data
        total_flights = len(flight_data)
        if total_flights == 0:
            return "No flight data available for analysis."

        # Count flights by city and type
        city_counts = defaultdict(lambda: {'total': 0, 'ground': 0, 'international': 0, 'domestic': 0})
        for flight in flight_data:
            city = flight['city']
            city_counts[city]['total'] += 1
            
            if flight['on_ground']:
                city_counts[city]['ground'] += 1
            
            if flight['origin_country'] != 'Australia':
                city_counts[city]['international'] += 1
            else:
                city_counts[city]['domestic'] += 1

        # Calculate statistics
        total_international = sum(c['international'] for c in city_counts.values())
        total_ground = sum(c['ground'] for c in city_counts.values())
        int_percentage = (total_international / total_flights * 100) if total_flights > 0 else 0

        # Sort cities by total flights
        top_cities = sorted(
            [(city, counts) for city, counts in city_counts.items()],
            key=lambda x: x[1]['total'],
            reverse=True
        )[:3]

        # Format top cities string
        top_cities_str = []
        for city, counts in top_cities:
            if counts['ground'] > counts['domestic'] and counts['ground'] > counts['international']:
                top_cities_str.append(f"{city} (Ground): {counts['ground']} flights")
            elif counts['international'] > counts['domestic']:
                top_cities_str.append(f"{city} (Int'l): {counts['international']} flights")
            else:
                top_cities_str.append(f"{city} (Dom): {counts['domestic']} flights")

        # Determine traffic pattern
        current_time = datetime.now()
        time_of_day = (
            'morning' if 5 <= current_time.hour < 12
            else 'afternoon' if 12 <= current_time.hour < 17
            else 'evening' if 17 <= current_time.hour < 22
            else 'night'
        )

        # Calculate traffic type recommendation
        traffic_type = "international" if int_percentage > 50 else "domestic"
        recommendation = (
            "optimize for international traveler services"
            if traffic_type == "international"
            else "optimize for local traveler preferences"
        )

        # Create structured analysis with proper alignment
        analysis = [
            "📊  Market Analysis",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📍  Analyzing all Australian airspace",
            f"✈️  Currently tracking {total_flights} active flights",
            "🌆  Top areas:",
            "    " + "\n    ".join(top_cities_str),
            f"🌏  International traffic: {int_percentage:.1f}% of flights",
            f"🛬  {total_ground} aircraft on ground",
            f"💡  Mostly {traffic_type} traffic - {recommendation}",
            f"⏰  {time_of_day.capitalize()} traffic pattern",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        # Join with newlines
        return '\n'.join(analysis)

    except Exception as e:
        print(f"Error generating insights: {e}")
        return "Unable to generate market insights at this time."

@app.route("/", methods=["GET", "POST"])
def index():
    routes, counts, insights = [], [], ""
    selected_city = ""
    
    # Convert AUSTRALIAN_CITIES dict to list for dropdown
    available_cities = sorted(AUSTRALIAN_CITIES.keys())

    if request.method == "POST":
        selected_city = request.form.get("city")
        print(f"\nSelected city: {selected_city}")
        
        try:
            data = fetch_flight_data()
            
            if data:
                routes, counts, df = process_data(data, selected_city)
                insights = generate_market_analysis(routes, counts, df, selected_city)
            else:
                insights = "No Australian flights found in the current data. Please try again later."
                
        except Exception as e:
            print(f"Error processing request: {e}")
            insights = "An error occurred while fetching flight data. Please try again later."
    
    return render_template(
        "index.html",
        available_cities=available_cities,
        routes=routes,
        counts=counts,
        insights=insights,
        datetime=datetime  # Pass datetime module to template
    )

if __name__ == "__main__":
    app.run(debug=True)
