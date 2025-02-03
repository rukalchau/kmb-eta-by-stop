from flask import Flask, jsonify, render_template
from typing import Dict, List
import requests
import threading
import time
from datetime import datetime, timedelta
from calendar_events import GoogleCalendarEvents
import json
import websocket
from threading import Lock

app = Flask(__name__)

# Global cache for stops and ETAs
stops_cache: List[Dict] = []
eta_cache: Dict[str, Dict] = {}
last_update: Dict[str, datetime] = {}

YU_CHUI_COURT_STOPS = []  # Store Yu Chui Court stops

# Global variables for real-time prices and news
real_time_prices = {
    'btc': 0,
    'aapl': 0
}
news_cache = []
news_last_update = datetime.now() - timedelta(hours=1)  # Initialize to force first update
price_lock = Lock()
news_lock = Lock()
FINNHUB_API_KEY = 'cug2b4hr01qo5mukdem0cug2b4hr01qo5mukdemg'

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

@app.route('/api/calendar-events', methods=['GET'])
def get_calendar_events():
    try:
        calendar = GoogleCalendarEvents()
        # Increase max_results to ensure we get enough events for 3 days
        events = calendar.get_upcoming_events(max_results=20)  # Increased from 5 to 20
        return jsonify({
            'status': 'success',
            'events': events
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/89x-dashboard')
def dashboard_89x():
    return render_template('89x_dashboard.html')

def update_market_prices():
    """Update market prices every 5 seconds"""
    while True:
        try:
            def get_price(symbol):
                try:
                    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 429:
                        time.sleep(1)
                        return None
                    data = response.json()
                    return float(data.get('c', 0))
                except Exception:
                    return None

            btc_price = get_price('BINANCE:BTCUSDT')
            aapl_price = get_price('AAPL')

            with price_lock:
                if btc_price is not None:
                    real_time_prices['btc'] = btc_price
                if aapl_price is not None:
                    real_time_prices['aapl'] = aapl_price

        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(5)

def update_news():
    """Update news every 5 minutes"""
    global news_last_update, news_cache
    print("Starting news update service...")  # Debug log
    
    # Initial fetch of news
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=5)
        print(f"Initial Finnhub response status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            with news_lock:
                news_data = response.json()
                processed_news = []
                for item in news_data[:10]:  # Limit to 10 news items
                    processed_news.append({
                        'headline': item.get('headline', ''),
                        'summary': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'source': item.get('source', ''),
                        'datetime': datetime.fromtimestamp(item.get('datetime', 0)).isoformat()
                    })
                news_cache = processed_news
                news_last_update = datetime.now()
                print(f"Initial news cache populated with {len(news_cache)} items")  # Debug log
    except Exception as e:
        print(f"Error in initial news fetch: {e}")

    # Continue with regular updates
    while True:
        try:
            current_time = datetime.now()
            if (current_time - news_last_update).total_seconds() >= 300:  # 5 minutes
                print("Fetching news from Finnhub...")  # Debug log
                url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
                response = requests.get(url, timeout=5)
                print(f"Finnhub response status: {response.status_code}")  # Debug log
                
                if response.status_code == 200:
                    with news_lock:
                        news_data = response.json()
                        print(f"Received {len(news_data)} news items")  # Debug log
                        processed_news = []
                        for item in news_data[:10]:  # Limit to 10 news items
                            processed_news.append({
                                'headline': item.get('headline', ''),
                                'summary': item.get('summary', ''),
                                'url': item.get('url', ''),
                                'source': item.get('source', ''),
                                'datetime': datetime.fromtimestamp(item.get('datetime', 0)).isoformat()
                            })
                        news_cache = processed_news
                        news_last_update = current_time
                        print(f"News cache updated with {len(news_cache)} items")  # Debug log

        except Exception as e:
            print(f"Error updating news: {e}")
        
        time.sleep(60)  # Check every minute

@app.route('/api/market-prices')
def get_market_prices():
    try:
        with price_lock:
            prices = {
                'btc': real_time_prices['btc'],
                'aapl': real_time_prices['aapl']
            }

        return jsonify({
            'status': 'success',
            'prices': prices,
            'timestamp': datetime.now().isoformat()
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/news')
def get_news():
    try:
        with news_lock:
            print(f"Serving {len(news_cache)} news items")  # Debug log
            return jsonify({
                'status': 'success',
                'news': news_cache,
                'timestamp': news_last_update.isoformat()
            })
    except Exception as e:
        print(f"Error serving news: {e}")  # Debug log
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def init_server():
    """Initialize server data"""
    global stops_cache
    stops_cache = fetch_kmb_stops()
    print(f"Found {len(stops_cache)} Yu Chui Court stops")
    
    # Start ETA update thread
    update_thread = threading.Thread(target=update_eta_cache, daemon=True)
    update_thread.start()
    
    # Start market price update thread
    market_thread = threading.Thread(target=update_market_prices, daemon=True)
    market_thread.start()
    
    # Start news update thread
    news_thread = threading.Thread(target=update_news, daemon=True)
    news_thread.start()

if __name__ == '__main__':
    init_server()
    app.run(debug=True) 