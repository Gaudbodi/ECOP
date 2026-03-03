import os
import uuid
from flask import Flask, render_template, request, jsonify, url_for
from flask_socketio import SocketIO, emit
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import json
import logging
import re # For parsing coordinates

# Attempt to import from utils.py
try:
    from utils import get_ghana_meteo_alerts, parse_cap_xml_content # Assuming parse_cap_xml_content is also in utils
    UTILS_AVAILABLE = True
    print("Successfully imported from utils.py")
except ImportError as e:
    UTILS_AVAILABLE = False
    print(f"Warning: Could not import from utils.py: {e}. Some functionalities might be limited.")
    # Define dummy functions if utils.py is not available, so the app can still run with other features
    def get_ghana_meteo_alerts(disaster_keywords: list, webdriver_path: str = None):
        logging.warning("utils.py not found, get_ghana_meteo_alerts is a dummy function.")
        return [{"error": "Scraping function not available.", "headline": "GMet Scraper Offline"}]
    def parse_cap_xml_content(xml_content: str, cap_url: str): # Add this if it was in utils
        logging.warning("utils.py not found, parse_cap_xml_content is a dummy function.")
        return {"error": "CAP parsing function not available.", "headline": "CAP Parser Offline"}


# --- Flask App Setup ---
app = Flask(__name__) # Default 'templates' folder, 'static' folder for static files
app.config['SECRET_KEY'] = 'emergency_secret_key!'
socketio = SocketIO(app)

# --- Configuration & Constants ---
OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"
ACCRA_LATITUDE = 5.55602
ACCRA_LONGITUDE = -0.1969
DEFAULT_LOCATION_DESC = "Accra, Greater Accra Region, Ghana"

GHAAP_DEFAULT_REGION = "REG02" 
GHAAP_DEFAULT_DISTRICT = "DS031" 
GHAAP_DEFAULT_CROP = "CT0000000001" 
GHAAP_BASE_URL = "https://ghaap.com/weather-forecast/index.php"

CAP_SENDER_ID = "EmergencyPlatform@example.com"
CAP_SENDER_NAME = "Emergency Communications Platform - HQ"

# Path to ChromeDriver (if not in PATH). Set to None if it's in PATH.
# EXAMPLE: WEBDRIVER_EXECUTABLE_PATH = "/usr/local/bin/chromedriver" # For Linux/Mac
# EXAMPLE: WEBDRIVER_EXECUTABLE_PATH = "C:/path/to/chromedriver.exe" # For Windows
# WEBDRIVER_EXECUTABLE_PATH = None # Set to your path or None

# In your Flask app config

WEBDRIVER_EXECUTABLE_PATH = "C:\\chrome-win32\\chrome-win32\\chromedriver.exe"  # Windows
# "C:\chrome-win32\chrome-win32\chrome.exe"

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Data Storage (Simple In-Memory) ---
latest_data_store = {
    "cap": None,
    "meteo": None,
    "agro": None,
    "gmet_cap": None # For alerts from Ghana Meteo
}

# --- Helper Functions ---
def get_utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def interpret_weather_code(code):
    codes = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail"
    }
    return codes.get(code, f"Weather code: {code}")

def extract_cap_coordinates(info_element, ns):
    """
    Tries to extract a representative coordinate (latitude, longitude) from a CAP <info> element.
    Prioritizes <point>, then <circle> center, then first point of first <polygon>.
    Returns a dictionary {'latitude': float, 'longitude': float} or None.
    """
    if info_element is None:
        return None

    area_block = info_element.find('cap:area', ns)
    if area_block is None:
        return None

    # Try <point> first
    point_element = area_block.find('cap:point', ns)
    if point_element is not None and point_element.text:
        try:
            lat_str, lon_str = point_element.text.split()
            return {"latitude": float(lat_str), "longitude": float(lon_str)}
        except ValueError:
            logging.warning(f"Could not parse CAP <point>: {point_element.text}")

    # Try <circle> next
    circle_element = area_block.find('cap:circle', ns)
    if circle_element is not None and circle_element.text:
        try:
            # Format is "lat,lon radius" e.g., "32.9525 -95.5950 10.0"
            parts = circle_element.text.split()
            lat_str, lon_str = parts[0].split(',')
            return {"latitude": float(lat_str), "longitude": float(lon_str)}
        except (ValueError, IndexError):
            logging.warning(f"Could not parse CAP <circle>: {circle_element.text}")
    
    # Try first coordinate of the first <polygon>
    polygon_element = area_block.find('cap:polygon', ns)
    if polygon_element is not None and polygon_element.text:
        try:
            # Format is "lat1,lon1 lat2,lon2 ..."
            first_coord_pair = polygon_element.text.strip().split(' ')[0]
            lat_str, lon_str = first_coord_pair.split(',')
            return {"latitude": float(lat_str), "longitude": float(lon_str)}
        except (ValueError, IndexError):
            logging.warning(f"Could not parse first coordinate of CAP <polygon>: {polygon_element.text}")
            
    # Fallback: Try geocode if it contains parsable coordinates (less standard)
    geocode_element = area_block.find('cap:geocode/cap:value', ns) # Assuming valueName="LatLon"
    if geocode_element is not None and geocode_element.text:
        try:
            # Check if it looks like "lat,lon"
            if ',' in geocode_element.text and len(geocode_element.text.split(',')) == 2:
                lat_str, lon_str = geocode_element.text.split(',')
                return {"latitude": float(lat_str.strip()), "longitude": float(lon_str.strip())}
        except ValueError:
            logging.warning(f"Could not parse CAP <geocode> as coordinates: {geocode_element.text}")

    logging.info("No direct point, circle center, or polygon start found for coordinates in CAP area.")
    return None


def process_parsed_cap_data(cap_data: dict):
    """
    Processes a dictionary from parse_cap_xml_content (or similar from utils.py)
    to add coordinates and prepare for UI/Pi.
    """
    if not cap_data or "error" in cap_data:
        return cap_data

    # Re-parse the raw XML if needed to access the full structure for coordinate extraction
    # This assumes cap_data might come from utils.py's parse_cap_xml_content which might not have the full root.
    # If cap_data already contains the full structure or raw_xml, this can be simplified.
    # For now, let's assume we need to parse it again if raw_xml is available.
    
    # For this integration, we assume the `cap_data` from `get_ghana_meteo_alerts`
    # is already a dictionary structured by `parse_cap_xml_content` from `utils.py`.
    # We need to ensure that function provides enough info or we re-parse.
    # Let's assume `cap_data` is the direct output of `parse_cap_xml_content`.
    # We need to get the <info> block to pass to extract_cap_coordinates.
    # This is tricky without knowing the exact structure returned by utils.py's parser.
    # For now, we'll assume the `utils.parse_cap_xml_content` needs to be enhanced or we re-parse here.
    # Let's try to re-parse if we have raw_xml (which we don't get from the current utils.py)
    #
    # **Simplification for now**: We'll assume the Flask's own parse_cap_alert_xml will be used
    # for CAP messages that need coordinate extraction.
    # The `get_ghana_meteo_alerts` from `utils.py` might need modification to return raw XML or
    # perform coordinate extraction itself.
    #
    # For now, let's structure the output assuming coordinates might be missing.
    
    coordinates = None
    # If we had raw XML:
    # if cap_data.get("raw_xml_content"):
    #     temp_root = ET.fromstring(cap_data["raw_xml_content"])
    #     ns_temp = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
    #     info_block_temp = temp_root.find('cap:info', ns_temp) # Or the first one
    #     coordinates = extract_cap_coordinates(info_block_temp, ns_temp)

    # Since `utils.get_ghana_meteo_alerts` returns a list of dicts from `parse_cap_xml_content`,
    # and that parser doesn't give us the raw XML or the ElementTree objects easily to re-parse here for coordinates,
    # we'll have to rely on what's already parsed or modify `utils.py`.
    # For now, we'll set coordinates to None for GMet alerts unless we modify utils.py.
    # A better approach: `get_ghana_meteo_alerts` should also try to extract coordinates.

    processed_data = {
        "source": "gmet_cap", # Differentiate from manually submitted CAP
        "identifier": cap_data.get("identifier", str(uuid.uuid4())),
        "sender": cap_data.get("sender", CAP_SENDER_NAME),
        "sent_time_cap": cap_data.get("sent").isoformat() if cap_data.get("sent") else get_utc_timestamp(),
        "headline": cap_data.get("headline", "N/A"),
        "description": cap_data.get("description", "N/A"),
        "area_description": cap_data.get("areaDesc", "Not specified"), # Assuming areaDesc is parsed by utils
        "event": cap_data.get("event", "Weather Alert"),
        "advisory_text": f"GMet CAP: {cap_data.get('headline', '')}. {cap_data.get('description', '')}",
        "audio_text": f"Ghana Meteorological Agency Alert. {cap_data.get('event', '')}. {cap_data.get('headline', '')}",
        "timestamp": get_utc_timestamp(),
        "icon_emoji": "🇬🇭☔", # Specific for GMet
        "longitude": coordinates.get("longitude") if coordinates else None,
        "latitude": coordinates.get("latitude") if coordinates else None,
        "cap_url": cap_data.get("cap_url", "")
    }
    latest_data_store["gmet_cap"] = processed_data
    return processed_data


def fetch_open_meteo_data(lat=ACCRA_LATITUDE, lon=ACCRA_LONGITUDE, location_desc=DEFAULT_LOCATION_DESC):
    # (This function remains largely the same as your app.py, but will add lat/lon to output)
    params = {
        "latitude": lat, "longitude": lon, "current_weather": "true",
        "hourly": "temperature_2m,relativehumidity_2m,apparent_temperature,precipitation_probability,weathercode,windspeed_10m,winddirection_10m",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "timezone": "auto"
    }
    try:
        response = requests.get(OPEN_METEO_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        current_weather = data.get("current_weather", {})
        
        temp = current_weather.get('temperature', 'N/A')
        windspeed = current_weather.get('windspeed', 'N/A')
        weather_code = current_weather.get('weathercode')
        condition = interpret_weather_code(weather_code)
        humidity = data.get("hourly", {}).get("relativehumidity_2m", [None])[0] or "N/A"
        precip_prob = data.get("hourly", {}).get("precipitation_probability", [None])[0] or "N/A"

        advisory_text = (
            f"Weather for {location_desc}: {condition}. "
            f"Temp: {temp}°C. Humidity: {humidity}%. "
            f"Wind: {windspeed} km/h. Precipitation Chance: {precip_prob}%."
        )
        
        processed_data = {
            "source": "meteo", "location": location_desc, "condition": condition,
            "temperature": temp, "humidity": humidity, "windspeed": windspeed,
            "precipitation_probability": precip_prob, "weather_code": weather_code,
            "advisory_text": advisory_text, 
            "audio_text": f"Weather update for {location_desc}. Condition: {condition}. Temperature is {temp} degrees Celsius.",
            "timestamp": get_utc_timestamp(), "icon_emoji": "🌤️",
            "latitude": lat, "longitude": lon # Add coordinates
        }
        
        if weather_code is not None:
            if weather_code in [0, 1]: processed_data["icon_emoji"] = "☀️"
            elif weather_code in [2, 3]: processed_data["icon_emoji"] = "☁️"
            elif weather_code >= 51 and weather_code <= 67: processed_data["icon_emoji"] = "🌧️"
            elif weather_code >= 95 : processed_data["icon_emoji"] = "⛈️"
            
        latest_data_store["meteo"] = processed_data
        return processed_data
    except Exception as e:
        logging.error(f"Error in fetch_open_meteo_data: {e}")
        return {"error": str(e), "advisory_text": "Could not fetch/process weather data."}


def fetch_ghaap_agro_data(region=GHAAP_DEFAULT_REGION, district=GHAAP_DEFAULT_DISTRICT, crop=GHAAP_DEFAULT_CROP, year_offset=0):
    # (This function remains largely the same as your app.py)
    current_year = datetime.now().year + year_offset
    params = {"p": "crop-search-event", "regiontxt": region, "districttxt": district, "crop": crop, "yeartxt": str(current_year)}
    logging.info(f"Fetching GHAAP data with params: {params}")
    try:
        response = requests.get(GHAAP_BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        advisory_text_parts = []
        
        # Try to find element with id="wt_smssend"
        target_element = soup.find(id="wt_smssend")
        if target_element:
            # Extract text from all children, trying to get meaningful content
            for child in target_element.find_all(string=True, recursive=True):
                text = child.strip()
                if text and len(text) > 10 : # Filter out very short/irrelevant strings
                    advisory_text_parts.append(text)
        
        if not advisory_text_parts: # Fallback if specific ID not found or no content
            content_div = soup.find('div', class_='col-md-9') # A general content area
            if content_div:
                paragraphs = content_div.find_all('p')
                for p in paragraphs:
                    text = p.get_text(separator=' ', strip=True)
                    if text and len(text) > 30: advisory_text_parts.append(text)
        
        advisory_summary = " ".join(advisory_text_parts[:5]) # Join first few relevant parts
        if len(advisory_summary) > 400: advisory_summary = advisory_summary[:397] + "..."
        if not advisory_summary: advisory_summary = "No specific advisory found on GHAAP page. Please check website."

        processed_data = {
            "source": "agro", "region_code": region, "district_code": district, "crop_code": crop, "year": current_year,
            "advisory_text": advisory_summary,
            "audio_text": f"Agro-climate advisory from GHAAP. {advisory_summary[:200]}", # Shorter for audio
            "timestamp": get_utc_timestamp(), "icon_emoji": "🌾"
        }
        latest_data_store["agro"] = processed_data
        return processed_data
    except Exception as e:
        logging.error(f"Error in fetch_ghaap_agro_data: {e}")
        return {"error": str(e), "advisory_text": "Could not fetch/process GHAAP agro-advisory."}

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('Home.html')



@app.route('/fetch_gmet_alerts', methods=['GET'])
def handle_fetch_gmet_alerts():
    session_id = request.args.get('session_id', 'default_session')
    if not UTILS_AVAILABLE:
        logging.error(f"[{session_id}] GMet CAP: Utils not available.")
        # Send error to animation manager before returning
        socketio.emit('progress_update', {
            'session_id': session_id, 
            'step': 'error', 
            'message': 'GMet alert utility not available.'
        }, namespace='/ui_client')
        return jsonify({"error": "GMet alert utility not available.", "advisory_text": "Scraper offline."}), 500

    logging.info(f"[{session_id}] GMet CAP: Received request.")
    
    # Step 0: Initiating
    socketio.emit('progress_update', 
                  {'session_id': session_id, 'step': 0, 'message': 'Initiating GMet RSS feed fetch...'}, 
                  namespace='/ui_client')
    
    keywords = ["Thunderstorm", "Rain", "Flood", "Warning", "Advisory", "Squall"] 
    
    try:
        # Step 1: Fetching RSS and all linked CAPs (this is the main workhorse call)
        socketio.emit('progress_update', 
                      {'session_id': session_id, 'step': 1, 'message': 'Fetching RSS & linked CAP data... (This may take a moment)'}, 
                      namespace='/ui_client')
        
        # This function fetches RSS, then individual CAPs, parses, and filters.
        alerts_from_gmet = get_ghana_meteo_alerts(disaster_keywords=keywords) 
        
        # Step 2: Processing retrieved alerts
        socketio.emit('progress_update', 
                      {'session_id': session_id, 'step': 2, 'message': 'Processing retrieved alerts...'}, 
                      namespace='/ui_client')

        if not alerts_from_gmet:
            logging.warning(f"[{session_id}] GMet CAP: No relevant alerts returned from get_ghana_meteo_alerts.")
            socketio.emit('progress_update', {'session_id': session_id, 'step': 'error', 'message': 'No relevant GMet alerts found.'}, namespace='/ui_client')
            return jsonify({"error": "No GMet alerts found.", "advisory_text": "No current GMet alerts."}), 404

        # Assuming get_ghana_meteo_alerts returns a list, and we usually focus on the first/most relevant.
        # If it can return an error dict directly (e.g. {"error": ...}), handle that.
        first_alert_data = {}
        if isinstance(alerts_from_gmet, list) and alerts_from_gmet:
            first_alert_data = alerts_from_gmet[0]
        elif isinstance(alerts_from_gmet, dict) and "error" in alerts_from_gmet: # If utils itself returns an error dict
            first_alert_data = alerts_from_gmet
        
        if "error" in first_alert_data:
            logging.error(f"[{session_id}] GMet CAP: Error from alert processing: {first_alert_data['error']}")
            socketio.emit('progress_update', {'session_id': session_id, 'step': 'error', 'message': first_alert_data["error"]}, namespace='/ui_client')
            return jsonify(first_alert_data), 500 # Or appropriate error code
        
        # Step 3: Finalizing alert for display
        socketio.emit('progress_update', 
                      {'session_id': session_id, 'step': 3, 'message': f"Preparing alert: {first_alert_data.get('headline', 'GMet Alert')}"}, 
                      namespace='/ui_client')
        
        # Ensure the data structure matches what updateAdvisoryUI expects for 'gmet_cap'
        # The `get_ghana_meteo_alerts` should ideally return data in the expected format.
        # If `first_alert_data` is already processed correctly by `get_ghana_meteo_alerts`
        # (including keys like 'source', 'advisory_text', 'longitude', 'latitude' etc.),
        # then this direct assignment is fine.
        latest_data_store["gmet_cap"] = first_alert_data 

        socketio.emit('progress_update', {'session_id': session_id, 'step': 'complete', 'message': 'GMet CAP alert processed!'}, namespace='/ui_client')
        return jsonify(first_alert_data)

    except Exception as e:
        logging.error(f"[{session_id}] GMet CAP: Unexpected error in /fetch_gmet_alerts: {e}", exc_info=True)
        socketio.emit('progress_update', {'session_id': session_id, 'step': 'error', 'message': f'Critical server error during GMet processing.'}, namespace='/ui_client')
        return jsonify({"error": f"Critical server error: {str(e)}", "advisory_text": "Error processing GMet alerts."}), 500



@app.route('/fetch_data', methods=['GET'])
def handle_fetch_data():
    source = request.args.get('source', '').lower()
    session_id = request.args.get('session_id', 'default_session') # Get session_id
    logging.info(f"[{session_id}] Received request to fetch data for source: {source}")
    
    data = None
    if source == 'meteo':
        socketio.emit('progress_update', {'session_id': session_id, 'step': 0, 'message': 'Fetching OpenMeteo data...'}, namespace='/ui_client')
        data = fetch_open_meteo_data()
        socketio.emit('progress_update', {'session_id': session_id, 'step': 1, 'message': 'Weather data processed.'}, namespace='/ui_client')
    elif source == 'agro':
        socketio.emit('progress_update', {'session_id': session_id, 'step': 0, 'message': 'Fetching GHAAP data...'}, namespace='/ui_client')
        data = fetch_ghaap_agro_data() # Uses default region/crop for now
        socketio.emit('progress_update', {'session_id': session_id, 'step': 1, 'message': 'Agro advisory processed.'}, namespace='/ui_client')
    else:
        return jsonify({"error": "Invalid data source specified."}), 400

    if data and "error" not in data:
        socketio.emit('new_alert_data', data, namespace='/pi_client') # For Pi
        socketio.emit('progress_update', {'session_id': session_id, 'step': 'complete', 'message': f'{source.capitalize()} data ready!'}, namespace='/ui_client') # For UI
        return jsonify(data)
    else:
        error_message = data.get('advisory_text', 'Failed to fetch data.') if data else 'Unknown error.'
        socketio.emit('progress_update', {'session_id': session_id, 'step': 'error', 'message': error_message}, namespace='/ui_client')
        return jsonify(data if data else {"error": "Failed to fetch data for unknown reason."}), 500


@app.route('/submit_cap', methods=['POST'])
def handle_submit_cap():
    session_id = request.args.get('session_id', 'default_session')
    try:
        cap_xml = request.data.decode('utf-8')
        if not cap_xml:
            return jsonify({"error": "No CAP XML data received."}), 400
        
        logging.info(f"[{session_id}] Received CAP XML for processing. Length: {len(cap_xml)}")
        socketio.emit('progress_update', {'session_id': session_id, 'step': 0, 'message': 'Parsing submitted CAP XML...'}, namespace='/ui_client')
        
        # Use a refined CAP parser that also tries to get coordinates
        root = ET.fromstring(cap_xml)
        ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
        info_block = root.find('cap:info', ns) # Process first info block
        if not info_block:
             info_block = root.find('{urn:oasis:names:tc:emergency:cap:1.2}info') # Try without namespace prefix
        
        if not info_block:
             socketio.emit('progress_update', {'session_id': session_id, 'step': 'error', 'message': 'No <info> block in CAP.'}, namespace='/ui_client')
             return jsonify({"error": "No <info> block found in CAP XML.", "advisory_text": "Invalid CAP format."}), 400

        headline = info_block.findtext('cap:headline', default='N/A', namespaces=ns)
        description = info_block.findtext('cap:description', default='N/A', namespaces=ns)
        area_desc = info_block.findtext('cap:area/cap:areaDesc', default='Not specified', namespaces=ns)
        event = info_block.findtext('cap:event', default='Alert', namespaces=ns)
        sender_name = info_block.findtext('cap:senderName', default=CAP_SENDER_NAME, namespaces=ns)
        sent_time_str = root.findtext('cap:sent', default=get_utc_timestamp(), namespaces=ns)

        coordinates = extract_cap_coordinates(info_block, ns)

        advisory_text = f"Manual CAP: {headline}. Desc: {description}. Area: {area_desc}."
        audio_text = f"Manual Alert from {sender_name}. {event}. {headline}. {description}. Area: {area_desc}."

        processed_data = {
            "source": "cap", "identifier": root.findtext('cap:identifier', default=str(uuid.uuid4()), namespaces=ns),
            "sender": sender_name, "sent_time_cap": sent_time_str,
            "headline": headline, "description": description, "area_description": area_desc, "event": event,
            "advisory_text": advisory_text, "audio_text": audio_text,
            "timestamp": get_utc_timestamp(), "icon_emoji": "📝",
            "longitude": coordinates.get("longitude") if coordinates else None,
            "latitude": coordinates.get("latitude") if coordinates else None,
        }
        latest_data_store["cap"] = processed_data
        
        socketio.emit('progress_update', {'session_id': session_id, 'step': 'complete', 'message': 'Manual CAP processed!'}, namespace='/ui_client')
        return jsonify(processed_data)

    except ET.ParseError as e:
        logging.error(f"Error parsing submitted CAP XML: {e}")
        socketio.emit('progress_update', {'session_id': session_id, 'step': 'error', 'message': f'Invalid CAP XML: {e}'}, namespace='/ui_client')
        return jsonify({"error": f"Invalid CAP XML format: {e}", "advisory_text": "Invalid CAP XML."}), 400
    except Exception as e:
        logging.error(f"Error in /submit_cap endpoint: {e}")
        socketio.emit('progress_update', {'session_id': session_id, 'step': 'error', 'message': f'Server error: {str(e)}'}, namespace='/ui_client')
        return jsonify({"error": f"Server error processing CAP: {str(e)}"}), 500


# --- SocketIO Events ---
@socketio.on('connect', namespace='/ui_client') 
def handle_ui_connect():
    logging.info(f"UI Client connected: {request.sid}")
    emit('connection_ack', {'message': 'Connected to Emergency Platform Server for UI updates'})

@socketio.on('disconnect', namespace='/ui_client')
def handle_ui_disconnect():
    logging.info(f"UI Client disconnected: {request.sid}")

# --- Main Execution ---
if __name__ == '__main__':
    logging.info("Starting Emergency Communications Platform server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False) # use_reloader=False for stability with SocketIO
