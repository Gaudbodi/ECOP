
# import os
# import platform
# import requests
# import xml.etree.ElementTree as ET
# from datetime import datetime, timezone
# from typing import List, Dict, Optional, Any
# import re
# import logging

# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# # Setup logging to see output in your console
# if not logging.getLogger().hasHandlers():
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# def parse_polygon_string(polygon_str: str) -> List[Dict[str, float]]:
#     """Parses a space-separated string of 'lat,lon' coordinates into a list of dictionaries."""
#     polygon_points = []
#     if not polygon_str:
#         return polygon_points
        
#     coord_pairs = polygon_str.strip().split(' ')
#     # for pair in coord_pairs:
#         # try:
#         #     lat_str, lon_str = pair.split(',')
#         #     polygon_points.append(float(lat_str))
#         #     polygon_points.append(float(lon_str))
#         # except (ValueError, IndexError):
#         #     logging.warning(f"Could not parse coordinate pair: '{pair}' in polygon string.")
#         #     continue
        

#     for pair in coord_pairs:
#         try:
#             lat_str, lon_str = pair.split(',')
#             polygon_points.append({"latitude": float(lat_str), "longitude": float(lon_str)})
#         except (ValueError, IndexError):
#             logging.warning(f"Could not parse coordinate pair: '{pair}' in polygon string.")
#             continue
#     return polygon_points




# def parse_cap_xml_content(xml_content: str, cap_url: str) -> Optional[Dict[str, Any]]:
#     """
#     Parses CAP XML content, correctly handling namespaces and extracting a comprehensive
#     set of fields, including all specified alert details and parameters.
#     """
#     try:
#         if isinstance(xml_content, bytes):
#             xml_content = xml_content.decode('utf-8', errors='ignore')

#         ET.register_namespace('cap', "urn:oasis:names:tc:emergency:cap:1.2")
#         root = ET.fromstring(xml_content)
#         ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

#         def find_text(element, path, default=''):
#             el = element.find(path, ns)
#             return el.text.strip() if el is not None and el.text else default

#         def parse_cap_datetime(dt_str):
#             if not dt_str: return None
#             try:
#                 if dt_str.endswith('Z'): dt_str = dt_str[:-1] + '+00:00'
#                 dt_str = dt_str.replace(" -", "-").replace(" +", "+")
#                 return datetime.fromisoformat(dt_str)
#             except ValueError:
#                 logging.warning(f"Could not parse datetime '{dt_str}' for {cap_url}.")
#                 return None
        
#         info_element = root.find('cap:info', ns)
#         if info_element is None:
#             logging.warning(f"No <info> block found in CAP file: {cap_url}")
#             return None

#         # --- Process all <area> blocks ---
#         all_areas = []
#         area_descriptions = []
#         all_polygons = []
#         area_elements = info_element.findall('cap:area', ns)
        
#         for area_block in area_elements:
#             area_desc = find_text(area_block, 'cap:areaDesc')
#             if area_desc:
#                 area_descriptions.append(area_desc)
            
#             polygon_str = find_text(area_block, 'cap:polygon')
#             polygon_coords = parse_polygon_string(polygon_str)
#             if polygon_coords:
#                 all_polygons.append(polygon_coords)
            
#             all_areas.append({
#                 "areaDesc": area_desc,
#                 "polygon": polygon_coords,
#             })
        
#         # --- Determine Time of Day from Onset ---
#         time_of_day = "Not specified"
#         onset_dt = parse_cap_datetime(find_text(info_element, 'cap:onset'))
#         if onset_dt:
#             hour = onset_dt.hour
#             if 5 <= hour < 12:
#                 time_of_day = "Morning"
#             elif 12 <= hour < 17:
#                 time_of_day = "Afternoon"
#             elif 17 <= hour < 21:
#                 time_of_day = "Evening"
#             else:
#                 time_of_day = "Night"
        
#         # --- Construct the final data dictionary with all requested fields ---
#         parsed_data = {
#             'cap:identifier': find_text(root, 'cap:identifier'),
#             'cap:sender': find_text(root, 'cap:sender'),
#             'cap:senderName': find_text(info_element, 'cap:senderName'),
#             'cap:sent': (dt.isoformat() if (dt := parse_cap_datetime(find_text(root, 'cap:sent'))) else None),
#             'cap:': find_text(root, 'cap:status'),
#             'cap:msg_type': find_text(root, 'cap:msgType'),
#             'cap:scope': find_text(root, 'cap:scope'),

#             'cap:headline': find_text(info_element, 'cap:headline'),
#             'cap:description': find_text(info_element, 'cap:description'),
#             'cap:instruction': find_text(info_element, 'cap:instruction'),
#             'cap:category': find_text(info_element, 'cap:category'),
#             'cap:urgency': find_text(info_element, 'cap:urgency'),
#             'cap:severity': find_text(info_element, 'cap:severity'),
#             'cap:certainty': find_text(info_element, 'cap:certainty'),
#             'cap:onset': (dt.isoformat() if (dt := onset_dt) else None),
#             'cap:expires': (dt.isoformat() if (dt := parse_cap_datetime(find_text(info_element, 'cap:expires'))) else None),
#             'cap:effective': (dt.isoformat() if (dt := parse_cap_datetime(find_text(info_element, 'cap:effective'))) else None),
#             'cap:web': find_text(info_element, 'cap:web'),
#             'cap:contact': find_text(info_element, 'cap:contact'),

#             # These are not standard CAP fields but are included as requested
#             'cap:temperature_range': find_text(info_element, 'cap:temperature_range', '0 to 0'),
#             'cap:humidity_range': find_text(info_element, 'cap:humidity_range', '0 to 0'),
#             'cap:windspeed_range': find_text(info_element, 'cap:windspeed_range', '0 to 0'),
#             'cap:event': find_text(info_element, 'cap:event'),

#             'areas': all_areas,
#             'polygon_list': all_polygons, # A list containing all polygon coordinate lists
#             'location_description': ', '.join(area_descriptions), # A combined string of all area descriptions
#             'time_of_day': time_of_day,
#             'cap_url': cap_url
#         }
        
#         # Add a top-level lat/lon for easy access by the map's initial zoom function
#         if all_polygons and all_polygons[0]:

#             first_point = all_polygons[0][0]
#             first_point = all_polygons[0][0]


# #main         
#             parsed_data['latitude'] = first_point.get('latitude')
#             parsed_data['longitude'] = first_point.get('longitude')
        
#         return parsed_data

#     except ET.ParseError as e:
#         logging.error(f"XML ParseError for {cap_url}: {e}")
#         return None
#     except Exception as e:
#         logging.error(f"Unexpected error parsing CAP XML {cap_url}: {e}", exc_info=True)
#         return None
    



# def get_ghana_meteo_alerts(
#     disaster_keywords: List[str],
#     rss_feed_url: str = "https://www.meteo.gov.gh/api/cap/rss.xml"
# ) -> List[Dict[str, Any]]:
    
#     all_parsed_cap_alerts = []
#     logging.info(f"Fetching GMet alerts from RSS feed: {rss_feed_url}")

#     try:
#         response = requests.get(rss_feed_url, timeout=20, verify=False)
#         response.raise_for_status()
#         rss_content = response.content
#     except requests.RequestException as e:
#         logging.error(f"Error fetching RSS feed {rss_feed_url}: {e}")
#         return []

#     try:
#         root_rss = ET.fromstring(rss_content)
#         channel = root_rss.find('channel')
#         if channel is None: return []
        
#         cap_xml_urls_from_rss = [link.text for item in channel.findall('item') if (link := item.find('link')) is not None and link.text]
#         logging.info(f"Found {len(cap_xml_urls_from_rss)} alert links in RSS feed.")

#     except ET.ParseError as e:
#         logging.error(f"Error parsing RSS feed XML: {e}")
#         return []

#     for xml_url in cap_xml_urls_from_rss:
#         logging.info(f"  Fetching individual CAP XML from: {xml_url}")
#         try:
#             cap_response = requests.get(xml_url, timeout=20, verify=False)
#             cap_response.raise_for_status()
            
#             xml_content = cap_response.content
#             parsed_cap_data = parse_cap_xml_content(xml_content, xml_url)
            
#             if parsed_cap_data:
#                 all_parsed_cap_alerts.append(parsed_cap_data)
#             else:
#                 logging.warning(f"    Could not parse CAP XML content from {xml_url}")

#         except Exception as e:
#             logging.error(f"    Unexpected error processing CAP from {xml_url}: {e}")
            
#     return all_parsed_cap_alerts

# # This allows you to test this file directly
# if __name__ == '__main__':
#     logging.basicConfig(level=logging.INFO)
#     print("\n--- Testing Local XML File 'pageSoure.xml' ---")
#     try:
#         with open('pageSoure.xml', 'rb') as f:
#             local_xml_content = f.read()
        
#         alert = parse_cap_xml_content(local_xml_content, "local_file_test")
#         if alert:
#             print("\n--- PARSED ALERT DATA ---")
#             print(f"Headline: {alert.get('headline')}")
#             print(f"Description: {alert.get('description')}")
#             print(f"Found {len(alert.get('areas', []))} areas:")
#             for i, area in enumerate(alert.get('areas', [])):
#                 print(f"  - Area {i+1}: {area.get('areaDesc')}")
#                 polygon = area.get('polygon', [])
#                 print(f"    - Polygon has {len(polygon)} points.")
#         else:
#             print("Failed to parse the local XML file.")

#     except FileNotFoundError:
#         print("Error: 'pageSoure.xml' not found in the current directory. Skipping local test.")
#     except Exception as e:
#         print(f"An error occurred during local file test: {e}")



import os
import platform
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import re
import logging

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging to see output in your console
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_polygon_string(polygon_str: str) -> List[Dict[str, float]]:
    """Parses a space-separated string of 'lat,lon' coordinates into a list of dictionaries."""
    polygon_points = []
    if not polygon_str:
        return polygon_points
        
    coord_pairs = polygon_str.strip().split(' ')
    for pair in coord_pairs:
        try:
            lat_str, lon_str = pair.split(',')
            polygon_points.append({"latitude": float(lat_str), "longitude": float(lon_str)})
        except (ValueError, IndexError):
            logging.warning(f"Could not parse coordinate pair: '{pair}' in polygon string.")
            continue
    return polygon_points

def parse_polygon_string_for_api(polygon_str: str) -> List[float]:
    """
    Parses a space-separated string of 'lat,lon' coordinates into a flat list
    of floats [lat1, lon1, lat2, lon2, ...].
    """
    polygon_points = []
    if not polygon_str:
        return polygon_points
        
    coord_pairs = polygon_str.strip().split(' ')
    for pair in coord_pairs:
        try:
            lat_str, lon_str = pair.split(',')
            polygon_points.append(float(lat_str))
            polygon_points.append(float(lon_str))
        except (ValueError, IndexError):
            logging.warning(f"Could not parse coordinate pair for API format: '{pair}'")
            continue
    return polygon_points

def parse_cap_xml_content(xml_content: str, cap_url: str) -> Optional[Dict[str, Any]]:
    """
    Parses CAP XML content for the primary frontend, keeping the original data structure.
    """
    try:
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode('utf-8', errors='ignore')

        ET.register_namespace('cap', "urn:oasis:names:tc:emergency:cap:1.2")
        root = ET.fromstring(xml_content)
        ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

        def find_text(element, path, default=''):
            el = element.find(path, ns)
            return el.text.strip() if el is not None and el.text else default

        def parse_cap_datetime(dt_str):
            if not dt_str: return None
            try:
                if dt_str.endswith('Z'): dt_str = dt_str[:-1] + '+00:00'
                return datetime.fromisoformat(dt_str.replace(" -", "-").replace(" +", "+"))
            except ValueError:
                return None
        
        info_element = root.find('cap:info', ns)
        if info_element is None: return None

        all_areas = []
        area_elements = info_element.findall('cap:area', ns)
        
        for area_block in area_elements:
            all_areas.append({
                "areaDesc": find_text(area_block, 'cap:areaDesc'),
                "polygon": parse_polygon_string(find_text(area_block, 'cap:polygon')),
            })

        onset_dt = parse_cap_datetime(find_text(info_element, 'cap:onset'))
        time_of_day = "Not specified"
        if onset_dt:
            hour = onset_dt.hour
            if 5 <= hour < 12: time_of_day = "Morning"
            elif 12 <= hour < 17: time_of_day = "Afternoon"
            elif 17 <= hour < 21: time_of_day = "Evening"
            else: time_of_day = "Night"
        
        parsed_data = {
            'identifier': find_text(root, 'cap:identifier'), 'sender': find_text(root, 'cap:sender'),
            'sender_name': find_text(info_element, 'cap:senderName'),
            'sent': (dt.isoformat() if (dt := parse_cap_datetime(find_text(root, 'cap:sent'))) else None),
            'status': find_text(root, 'cap:status'), 'msg_type': find_text(root, 'cap:msgType'),
            'scope': find_text(root, 'cap:scope'), 'headline': find_text(info_element, 'cap:headline'),
            'description': find_text(info_element, 'cap:description'),
            'instruction': find_text(info_element, 'cap:instruction'),
            'category': find_text(info_element, 'cap:category'), 'urgency': find_text(info_element, 'cap:urgency'),
            'severity': find_text(info_element, 'cap:severity'), 'certainty': find_text(info_element, 'cap:certainty'),
            'onset': (dt.isoformat() if (dt := onset_dt) else None),
            'expires': (dt.isoformat() if (dt := parse_cap_datetime(find_text(info_element, 'cap:expires'))) else None),
            'effective': (dt.isoformat() if (dt := parse_cap_datetime(find_text(info_element, 'cap:effective'))) else None),
            'web': find_text(info_element, 'cap:web'), 'contact': find_text(info_element, 'cap:contact'),
            'temperature_range': find_text(info_element, 'cap:temperature_range', '0 to 0'),
            'humidity_range': find_text(info_element, 'cap:humidity_range', '0 to 0'),
            'windspeed_range': find_text(info_element, 'cap:windspeed_range', '0 to 0'),
            'condition': find_text(info_element, 'cap:event'),
            'areas': all_areas,
            'location_description': ', '.join([a['areaDesc'] for a in all_areas if a['areaDesc']]),
            'time_of_day': time_of_day, 'cap_url': cap_url
        }
        
        if all_areas and all_areas[0].get('polygon'):
            first_point = all_areas[0]['polygon'][0]
            parsed_data['latitude'] = first_point.get('latitude')
            parsed_data['longitude'] = first_point.get('longitude')
        
        return parsed_data
    except Exception as e:
        logging.error(f"Error in parse_cap_xml_content for {cap_url}: {e}", exc_info=True)
        return None

def create_api_formatted_alert(original_alert: Dict) -> Dict:
    """
    Transforms a standard parsed alert into the special format required by the API client,
    with 'cap:' prefixes and a flat polygon list.
    """
    if not original_alert:
        return {}
    
    # Create the new structure with 'cap:' prefixes
    api_data = {f"cap:{key}": value for key, value in original_alert.items() if key not in ['areas', 'location_description', 'time_of_day', 'cap_url']}
    
    # Handle the special fields that are not prefixed
    api_data['location_description'] = original_alert.get('location_description', '')
    api_data['time_of_day'] = original_alert.get('time_of_day', 'Not specified')
    api_data['cap_url'] = original_alert.get('cap_url', '')

    # Transform the 'areas' data
    api_areas = []
    all_polygons_flat = []
    for area in original_alert.get('areas', []):
        flat_polygon = []
        # Re-parse the polygon from the original dictionary structure
        if area.get('polygon'):
            for point in area['polygon']:
                flat_polygon.append(point['latitude'])
                flat_polygon.append(point['longitude'])
        
        api_areas.append({
            "areaDesc": area.get('areaDesc'),
            "polygon": flat_polygon
        })
        all_polygons_flat.append(flat_polygon)
        
    api_data['areas'] = api_areas
    api_data['polygon_list'] = all_polygons_flat
    
    return api_data


def get_ghana_meteo_alerts(
    disaster_keywords: List[str],
    rss_feed_url: str = "https://www.meteo.gov.gh/api/cap/rss.xml"
) -> List[Dict[str, Any]]:
    """
    Fetches emergency alerts from the Ghana Meteorological Agency RSS feed.
    """
    all_parsed_cap_alerts = []
    logging.info(f"Fetching GMet alerts from: {rss_feed_url}")

    try:
        # Disable SSL verification as GMet sometimes has certificate issues
        response = requests.get(rss_feed_url, timeout=25, verify=False)
        response.raise_for_status()
        
        root_rss = ET.fromstring(response.content)
        channel = root_rss.find('channel')
        if channel is None:
            logging.error("No <channel> found in GMet RSS.")
            return []
        
        items = channel.findall('item')
        logging.info(f"Found {len(items)} items in RSS feed.")

        for item in items:
            link_el = item.find('link')
            if link_el is None or not link_el.text:
                continue
            
            xml_url = link_el.text.strip()
            logging.info(f"Processing individual CAP XML: {xml_url}")
            
            try:
                cap_response = requests.get(xml_url, timeout=20, verify=False)
                cap_response.raise_for_status()
                
                parsed_data = parse_cap_xml_content(cap_response.content, xml_url)
                if parsed_data:
                    # Filter by keywords if provided
                    headline = parsed_data.get('headline', '').lower()
                    description = parsed_data.get('description', '').lower()
                    
                    is_relevant = any(k.lower() in headline or k.lower() in description for k in disaster_keywords)
                    if is_relevant:
                        all_parsed_cap_alerts.append(parsed_data)
                        logging.info(f"  Alert matches keywords: {parsed_data.get('headline')}")
                    else:
                        logging.info(f"  Alert ignored (not relevant): {parsed_data.get('headline')}")
                
            except Exception as e:
                logging.error(f"  Error processing CAP from {xml_url}: {e}")
            
    except Exception as e:
        logging.error(f"Error fetching or parsing RSS feed {rss_feed_url}: {e}")
            
    return all_parsed_cap_alerts