from flask import Flask, jsonify, render_template
from typing import Dict, List
import requests
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Global cache for stops and ETAs
stops_cache: List[Dict] = []
eta_cache: Dict[str, Dict] = {}
last_update: Dict[str, datetime] = {}

YU_CHUI_COURT_STOPS = []  # Store Yu Chui Court stops

def fetch_kmb_stops() -> List[Dict]:
    """Fetch all KMB stops"""
    try:
        response = requests.get("https://data.etabus.gov.hk/v1/transport/kmb/stop")
        response.raise_for_status()
        data = response.json()['data']
        
        # Filter for Yu Chui Court stops
        yu_chui_stops = [
            stop for stop in data
            if "YU CHUI COURT" in stop['name_en'].upper() or 
               "YU CHUI COURT" in stop.get('name_tc', '').upper()
        ]
        return yu_chui_stops
    except requests.RequestException as e:
        print(f"Error fetching KMB stops: {e}")
        return []

def fetch_stop_eta(stop_id: str) -> List[Dict]:
    """Fetch ETA information for a specific stop"""
    try:
        url = f"https://data.etabus.gov.hk/v1/transport/kmb/stop-eta/{stop_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()['data']
    except requests.RequestException as e:
        print(f"Error fetching KMB ETA for stop {stop_id}: {e}")
        return []

def update_eta_cache():
    """Update ETA cache for all Yu Chui Court stops periodically"""
    while True:
        for stop in stops_cache:
            stop_id = stop['stop']
            eta_cache[stop_id] = fetch_stop_eta(stop_id)
            last_update[stop_id] = datetime.now()
        time.sleep(15)  # Update every 15 seconds

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/stops')
def get_stops():
    """API endpoint to get Yu Chui Court stops"""
    return jsonify(stops_cache)

@app.route('/api/eta/<stop_id>')
def get_eta(stop_id):
    """API endpoint to get ETA for a specific stop"""
    if stop_id not in [stop['stop'] for stop in stops_cache]:
        return jsonify({'error': 'Invalid stop ID'}), 404
    
    etas = eta_cache.get(stop_id, [])
    update_time = last_update.get(stop_id, datetime.now()).isoformat()
    return jsonify({
        'etas': etas,
        'updated_at': update_time
    })

def init_server():
    """Initialize server data"""
    global stops_cache
    stops_cache = fetch_kmb_stops()
    print(f"Found {len(stops_cache)} Yu Chui Court stops")
    
    # Start ETA update thread
    update_thread = threading.Thread(target=update_eta_cache, daemon=True)
    update_thread.start()

if __name__ == '__main__':
    init_server()
    app.run(debug=True) 