import os
import uuid
from flask import Flask, render_template, request, jsonify, url_for
from flask_socketio import SocketIO, emit
import requests
from utils import get_ghana_meteo_alerts, create_api_formatted_alert
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import json
import logging
import re


# --- AI & Context Database Configuration ---
CONTEXT_DB_PATH = 'location_context_db.json'

def load_context_db():
    """Loads the location context database from a JSON file."""
    try:
        with open(CONTEXT_DB_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_context_db(data):
    """Saves the given data to the location context database JSON file."""
    with open(CONTEXT_DB_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def generate_specific_advice(event, context):
    """Simulates an AI generating specific, actionable advice."""
    event_lower = event.lower()
    advice = []
    if 'flood' in event_lower:
        advice.append("Move to higher ground immediately.")
        if 'commercial' in context or 'market' in context:
            advice.append("Shop owners should secure property.")
        if 'traffic' in context:
            advice.append("Expect severe road closures and travel disruptions.")
    elif 'fire' in event_lower:
        advice.append("Evacuate the area calmly and quickly.")
        if 'densely populated' in context:
            advice.append("Check on neighbors who may need assistance.")
    elif 'storm' in event_lower or 'wind' in event_lower:
        advice.append("Secure loose objects outdoors and stay indoors away from windows.")
    else:
        advice.append("Follow all instructions from emergency services.")
    return " ".join(advice)

def get_contextual_advice(event, area_desc):
    """ 
    Acts as the AI agent to generate and retrieve contextual advice.
    - Checks a simple JSON DB for existing context about a location.
    - If context exists, uses it to generate fresh advice for the current event.
    - If not, it generates new general context, saves it, and then creates advice.
    """
    db = load_context_db()
    context = db.get(area_desc)
    
    if context:
        logging.info(f"Context for '{area_desc}' found in database.")
        # AI Step: Generate advice using existing context and the new event.
        # This simulates a prompt like: f"Given that '{context}', what is the advice for a '{event}' event?"
        advice = generate_specific_advice(event, context)
    else:
        logging.info(f"No context for '{area_desc}'. Generating new context with AI.")
        # AI Step 1: Generate general context for the new location.
        # This simulates a prompt like: f"Describe the disaster-relevant context of '{area_desc}, Ghana'."
        # In this simulation, we'll create a plausible context.
        if 'osu' in area_desc.lower():
            new_context = "A densely populated commercial and residential area with significant foot traffic and some low-lying, flood-prone zones."
        elif 'accra' in area_desc.lower():
            new_context = "A major metropolitan capital with high population density and critical infrastructure."
        else:
            new_context = "A populated area in Ghana."
        
        logging.info(f"Generated new context: \"{new_context}\"")
        db[area_desc] = new_context
        save_context_db(db)
        
        # AI Step 2: Generate advice using the newly created context.
        advice = generate_specific_advice(event, new_context)

    return advice


# Attempt to import from utils.py
# try:
#     from utils import get_weather_advisory, get_agro_advisory, get_ghana_meteo_alerts, parse_cap_xml_from_string, create_api_formatted_alert
#     UTILS_AVAILABLE = True
#     print("Successfully imported from utils.py")
# except ImportError as e:
#     UTILS_AVAILABLE = False
#     print(f"Warning: Could not import from utils.py: {e}. Some functionalities might be limited.")
#     # Define dummy functions if utils.py is not available, so the app can still run with other features
#     def get_ghana_meteo_alerts(disaster_keywords: list, webdriver_path: str = None):
#         logging.warning("utils.py not found, get_ghana_meteo_alerts is a dummy function.")
#         return [{"error": "Scraping function not available.", "headline": "GMet Scraper Offline"}]
#     def parse_cap_xml_content(xml_content: str, cap_url: str): # Add this if it was in utils
#         logging.warning("utils.py not found, parse_cap_xml_content is a dummy function.")
#         return {"error": "CAP parsing function not available.", "headline": "CAP Parser Offline"}


# --- Flask App Setup ---
app = Flask(__name__) # Default 'templates' folder, 'static' folder for static files
app.config['SECRET_KEY'] = 'emergency_secret_key!'


# Production-optimized SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- Data Storage (Simple In-Memory) ---
latest_data_store = {
    "cap": None,
    "meteo": None,
    "agro": None,
    "gmet_cap": None 
}

# Simulation Data for Dashboard
responder_status_store = [
    {"id": "R001", "name": "Accra North Fire Station", "status": "Ready", "last_update": "10 mins ago"},
    {"id": "R002", "name": "Korle-Bu Ambulance Service", "status": "On Mission", "last_update": "2 mins ago"},
    {"id": "R003", "name": "NADMO Rapid Response Team A", "status": "Ready", "last_update": "Just now"},
    {"id": "R004", "name": "Tema General Hospital", "status": "Alerted", "last_update": "5 mins ago"}
]

forwarding_logs = []

# A robust set of disaster keywords for filtering GMet alerts
DISASTER_KEYWORDS = [
    "Thunderstorm", "Rain", "Flood", "Warning", "Advisory", "Squall",
    "Storm", "Heavy Rain", "Severe", "Extreme", "Emergency", "Disaster"
]

# --- Geocoding Logic ---
def geocode_location(location_name):
    """Translates plain text locations into coordinates and polygons using OpenStreetMap."""
    try:
        # Append 'Ghana' to ensure local results
        query = f"{location_name}, Ghana"
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&polygon_geojson=1&limit=1"
        headers = {'User-Agent': 'E-CoP-Emergency-System/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if data:
            res = data[0]
            # Extract center
            lat, lon = float(res['lat']), float(res['lon'])
            
            # Extract polygon coordinates if available
            polygon = []
            if 'geojson' in res and res['geojson']['type'] in ['Polygon', 'MultiPolygon']:
                raw_coords = res['geojson']['coordinates']
                # Standardize to a list of [lat, lon]
                if res['geojson']['type'] == 'Polygon':
                    polygon = [[p[1], p[0]] for p in raw_coords[0]]
                else: # MultiPolygon - take largest segment
                    polygon = [[p[1], p[0]] for p in raw_coords[0][0]]
            
            return {"latitude": lat, "longitude": lon, "polygon": polygon}
    except Exception as e:
        logging.error(f"Geocoding failed for {location_name}: {e}")
    return None

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('new_home.html')

@app.route('/get_active_alerts', methods=['GET'])
def get_active_alerts():
    """Returns all currently active alerts (Manual + GMet) for synchronization."""
    active = []
    # Add manual CAP if exists
    if latest_data_store.get('cap'):
        active.append(latest_data_store['cap'])
    
    # Add GMet alerts
    gmet = latest_data_store.get('gmet_cap_list', [])
    active.extend(gmet)
    
    return jsonify(active)

@app.route('/fetch_gmet_alerts', methods=['GET'])
def handle_fetch_gmet_alerts():
    session_id = request.args.get('session_id', 'default_session')
    try:
        socketio.emit('progress_update', {'session_id': session_id, 'step': 0, 'message': 'Initializing GMet RSS link...'}, namespace='/ui_client')
        alerts = get_ghana_meteo_alerts(disaster_keywords=DISASTER_KEYWORDS)
        
        if alerts:
            latest_data_store['gmet_cap_list'] = alerts
            api_formatted = [create_api_formatted_alert(a) for a in alerts]
            socketio.emit('alert_data', api_formatted, namespace='/live_feed')
            socketio.emit('progress_update', {'session_id': session_id, 'step': 3, 'message': 'Broadcasting JSON to operators...'}, namespace='/ui_client')
        
        socketio.emit('progress_update', {'session_id': session_id, 'step': 'complete', 'message': 'GMet Sync Complete'}, namespace='/ui_client')
        return jsonify(alerts)
    except Exception as e:
        socketio.emit('progress_update', {'session_id': session_id, 'step': 'error', 'message': str(e)}, namespace='/ui_client')
        return jsonify({"error": str(e)}), 500

@app.route('/submit_cap', methods=['POST'])
def handle_submit_cap():
    try:
        alert_data = request.json
        agency = alert_data.get('sender_agency', 'Public Safety')
        
        # Geocode plain-text location if coordinates are missing
        if not alert_data.get('latitude') and alert_data.get('areaDesc'):
            geo = geocode_location(alert_data['areaDesc'])
            if geo:
                alert_data['latitude'] = geo['latitude']
                alert_data['longitude'] = geo['longitude']
                # Create standard areas structure for the frontend
                if geo['polygon']:
                    alert_data['areas'] = [{"areaDesc": alert_data['areaDesc'], "polygon": geo['polygon']}]

        alert_data['id'] = f"ALERT-{uuid.uuid4().hex[:8].upper()}"
        alert_data['sent_at'] = datetime.now(timezone.utc).isoformat()
        
        latest_data_store["cap"] = alert_data
        socketio.emit('new_alert', alert_data, namespace='/live')
        # Broadcast immediately to public display
        socketio.emit('alert_data', [alert_data], namespace='/live_feed')
        
        socketio.emit('operator_notification', {"agency": agency, "headline": alert_data.get('headline'), "data": alert_data}, namespace='/ui_client')
        return jsonify({"status": "success", "data": alert_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/responders', methods=['GET'])
def get_responders():
    return jsonify(responder_status_store)

@app.route('/forward_alert', methods=['POST'])
def forward_alert():
    socketio.emit('forwarding_update', {"summary": "Broadcast sequence initiated"}, namespace='/ui_client')
    return jsonify({"message": "Dissemination sequence initiated"})

@app.route('/public_display')
def public_display():
    return render_template('1_oct_25_V3.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"E-CoP Server active on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)


