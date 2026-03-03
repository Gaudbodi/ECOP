import os
import platform
import requests
# BeautifulSoup might still be useful if you have other scraping functions,
# but not directly for the RSS-based GMet alerts.
# from bs4 import BeautifulSoup 
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
import re
from urllib.parse import urljoin
import logging

# Selenium imports are no longer needed for get_ghana_meteo_alerts
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.common.exceptions import WebDriverException, TimeoutException
# from selenium.webdriver.chrome.service import Service

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_cap_coordinates(info_element, ns) -> Optional[Dict[str, float]]:
    """
    Tries to extract a representative coordinate (latitude, longitude) from a CAP <info> element.
    """
    if info_element is None:
        return None

    area_block = info_element.find('cap:area', ns)
    if area_block is None: # Fallback for non-prefixed common case in some CAPs
        area_block = info_element.find('{urn:oasis:names:tc:emergency:cap:1.2}area')
    if area_block is None:
        return None
    
    def find_text_in_area(element, path_segment): # Local helper
        if element is None: return None
        # Try with CAP namespace prefix
        el = element.find(f'cap:{path_segment}', ns)
        if el is None: # Try with full namespace URI
            el = element.find(f'{{urn:oasis:names:tc:emergency:cap:1.2}}{path_segment}')
        return el.text.strip() if el is not None and el.text else None

    point_text = find_text_in_area(area_block, 'point')
    if point_text:
        try:
            parts = point_text.split()
            if len(parts) >= 2:
                lat_str = parts[0].replace(',', '.')
                lon_str = parts[1].replace(',', '.')
                return {"latitude": float(lat_str), "longitude": float(lon_str)}
        except ValueError: logging.warning(f"Could not parse CAP <point>: '{point_text}'")

    circle_text = find_text_in_area(area_block, 'circle')
    if circle_text:
        try:
            parts = circle_text.split()
            if len(parts) >= 2:
                coord_part = parts[0]
                lat_str, lon_str = coord_part.split(',')
                return {"latitude": float(lat_str.strip()), "longitude": float(lon_str.strip())}
        except (ValueError, IndexError): logging.warning(f"Could not parse CAP <circle>: '{circle_text}'")
    
    polygon_text = find_text_in_area(area_block, 'polygon')
    if polygon_text:
        try:
            first_coord_pair = polygon_text.strip().split(' ')[0]
            lat_str, lon_str = first_coord_pair.split(',')
            return {"latitude": float(lat_str.strip()), "longitude": float(lon_str.strip())}
        except (ValueError, IndexError): logging.warning(f"Could not parse first coordinate of CAP <polygon>: '{polygon_text}'")
            
    geocode_elements = area_block.findall('cap:geocode', ns)
    if not geocode_elements: geocode_elements = area_block.findall('{urn:oasis:names:tc:emergency:cap:1.2}geocode')
    for geocode_element in geocode_elements:
        value_el = geocode_element.find('cap:value', ns)
        if value_el is None: value_el = geocode_element.find('{urn:oasis:names:tc:emergency:cap:1.2}value')
        if value_el is not None and value_el.text:
            text_val = value_el.text.strip()
            try:
                if ',' in text_val and len(text_val.split(',')) == 2:
                    lat_str, lon_str = text_val.split(',')
                    return {"latitude": float(lat_str.strip()), "longitude": float(lon_str.strip())}
                elif ' ' in text_val and len(text_val.split()) == 2:
                    lat_str, lon_str = text_val.split()
                    return {"latitude": float(lat_str.replace(',', '.').strip()), "longitude": float(lon_str.replace(',', '.').strip())}
            except ValueError: logging.debug(f"Geocode value '{text_val}' not directly parsable as lat,lon.")
    
    logging.info(f"No point, circle, polygon, or parsable geocode coordinates found in CAP area for the alert.")
    return None

def parse_cap_xml_content(xml_content: str, cap_url: str) -> Optional[Dict[str, Any]]:
    try:
        root = ET.fromstring(xml_content)
        ns = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

        def find_text(element, path): # Simplified find_text for this function
            if element is None: return None
            el = element.find(path, ns)
            if el is None and path.startswith('cap:'): # Try with full URI if prefixed
                 el = element.find(path.replace('cap:', '{urn:oasis:names:tc:emergency:cap:1.2}'))
            return el.text.strip() if el is not None and el.text else None

        all_info_blocks = root.findall('cap:info', ns)
        if not all_info_blocks: all_info_blocks = root.findall('{urn:oasis:names:tc:emergency:cap:1.2}info')

        info_element = None
        if all_info_blocks:
            for info_candidate in all_info_blocks:
                lang_text = find_text(info_candidate, 'cap:language')
                if lang_text and lang_text.lower().startswith('en'):
                    info_element = info_candidate; break
            if info_element is None: info_element = all_info_blocks[0]
        
        if info_element is None:
            logging.warning(f"No <info> block in CAP file: {cap_url}"); return None

        area_element = info_element.find('cap:area', ns)
        if area_element is None: area_element = info_element.find('{urn:oasis:names:tc:emergency:cap:1.2}area')
        area_desc = find_text(area_element, 'cap:areaDesc') if area_element is not None else "Not specified"
        
        coordinates = extract_cap_coordinates(info_element, ns) # Use the moved helper

        def parse_cap_datetime(dt_str):
            if not dt_str: return None
            try:
                if dt_str.endswith('Z'): dt_str = dt_str[:-1] + '+00:00'
                dt_str = dt_str.replace(" -", "-").replace(" +", "+")
                return datetime.fromisoformat(dt_str)
            except ValueError:
                logging.warning(f"Could not parse datetime '{dt_str}' via fromisoformat for {cap_url}.")
                for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        dt_obj = datetime.strptime(dt_str.split('.')[0], fmt)
                        if dt_obj.tzinfo is None: dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                        return dt_obj
                    except ValueError: continue
                logging.error(f"Failed to parse datetime '{dt_str}' for {cap_url}.")
                return None
        
        parsed_data = {
            "identifier": find_text(root, 'cap:identifier'), "sender": find_text(root, 'cap:sender'),
            "sent": parse_cap_datetime(find_text(root, 'cap:sent')), "status": find_text(root, 'cap:status'),
            "msgType": find_text(root, 'cap:msgType'), "scope": find_text(root, 'cap:scope'),
            "event": find_text(info_element, 'cap:event'), "headline": find_text(info_element, 'cap:headline'),
            "description": find_text(info_element, 'cap:description'), "areaDesc": area_desc,
            "effective": parse_cap_datetime(find_text(info_element, 'cap:effective')),
            "expires": parse_cap_datetime(find_text(info_element, 'cap:expires')),
            "cap_url": cap_url,
            "latitude": coordinates.get("latitude") if coordinates else None,
            "longitude": coordinates.get("longitude") if coordinates else None,
        }
        return parsed_data
    except ET.ParseError as e:
        logging.error(f"XML ParseError for {cap_url}: {e}"); return None
    except Exception as e:
        logging.error(f"Unexpected error parsing CAP XML {cap_url}: {e}"); return None

def get_ghana_meteo_alerts(
    disaster_keywords: List[str],
    rss_feed_url: str = "https://www.meteo.gov.gh/api/cap/rss.xml"
) -> List[Dict[str, Any]]:
    
    all_parsed_cap_alerts = []
    logging.info(f"Fetching GMet alerts from RSS feed: {rss_feed_url}")

    try:
        response = requests.get(rss_feed_url, timeout=20, verify=False)
        response.raise_for_status()
        rss_content = response.content
        logging.info(f"Successfully fetched RSS feed. Content length: {len(rss_content)}")
    except requests.RequestException as e:
        logging.error(f"Error fetching RSS feed {rss_feed_url}: {e}")
        return [{"error": f"Failed to fetch RSS feed: {e}", "headline": "RSS Fetch Error"}]

    try:
        root_rss = ET.fromstring(rss_content)
        channel = root_rss.find('channel')
        if channel is None:
            logging.error("No <channel> found in RSS feed.")
            return [{"error": "Invalid RSS feed structure.", "headline": "RSS Parse Error"}]
        
        cap_xml_urls_from_rss = [
            link_tag.text for item in channel.findall('item') 
            if (link_tag := item.find('link')) is not None and link_tag.text
        ]
        
        if not cap_xml_urls_from_rss:
            logging.warning("No <item> with <link> found in RSS feed.")
            return []

        logging.info(f"Found {len(cap_xml_urls_from_rss)} alert links in RSS feed.")

    except ET.ParseError as e:
        logging.error(f"Error parsing RSS feed XML: {e}")
        return [{"error": f"Failed to parse RSS feed: {e}", "headline": "RSS Parse Error"}]

    for xml_url in cap_xml_urls_from_rss:
        logging.info(f"  Fetching individual CAP XML from: {xml_url}")
        try:
            cap_response = requests.get(xml_url, timeout=20, verify=False)
            cap_response.raise_for_status()
            xml_content = cap_response.content.decode('utf-8', errors='replace') # Prefer utf-8
            
            parsed_cap_data = parse_cap_xml_content(xml_content, xml_url)
            if parsed_cap_data:
                all_parsed_cap_alerts.append(parsed_cap_data)
            else:
                logging.warning(f"    Could not parse CAP XML content from {xml_url}")
        except requests.RequestException as e: logging.error(f"    Error fetching CAP XML {xml_url}: {e}")
        except Exception as e: logging.error(f"    Unexpected error processing CAP XML {xml_url}: {e}")

    final_alerts = []
    if all_parsed_cap_alerts:
        active_alerts, expired_alerts, unknown_status_alerts = [], [], []
        now_utc = datetime.now(timezone.utc)

        for alert_data in all_parsed_cap_alerts:
            text_to_search = f"{alert_data.get('event','')} {alert_data.get('headline','')} {alert_data.get('description','')}".lower()
            matched_kw = [kw for kw in disaster_keywords if kw.lower() in text_to_search]
            is_weather_related = any(term in text_to_search for term in ['weather', 'storm', 'rain', 'wind', 'meteo'])

            if not ((disaster_keywords and matched_kw) or (not disaster_keywords and is_weather_related)):
                continue 
            alert_data['matched_keywords'] = matched_kw if matched_kw else (['weather-related'] if is_weather_related else [])

            effective = alert_data.get('effective')
            expires = alert_data.get('expires')
            sent = alert_data.get('sent')
            status_cap = alert_data.get("status", "").lower()

            is_active, is_expired = False, False
            if effective and not effective.tzinfo: effective = effective.replace(tzinfo=timezone.utc)
            if expires and not expires.tzinfo: expires = expires.replace(tzinfo=timezone.utc)
            if sent and not sent.tzinfo: sent = sent.replace(tzinfo=timezone.utc)

            if effective and expires:
                if effective <= now_utc < expires: is_active = True
                elif now_utc >= expires: is_expired = True
            elif effective: is_active = effective <= now_utc
            elif expires: is_active = now_utc < expires; is_expired = not is_active
            elif sent: 
                is_active = (now_utc - sent) <= timedelta(days=2) # Heuristic for recent alerts
                if not is_active: is_expired = True
            else: unknown_status_alerts.append(alert_data); continue
            
            if status_cap == "actual":
                if is_active: active_alerts.append(alert_data)
                elif is_expired: expired_alerts.append(alert_data)
                else: unknown_status_alerts.append(alert_data)
            elif status_cap not in ["test", "exercise", "system", "draft"]: # Non-actual, but not test etc.
                 if is_active: active_alerts.append(alert_data) # Treat as active if times match
                 elif is_expired: expired_alerts.append(alert_data)
                 else: unknown_status_alerts.append(alert_data)
        
        logging.info(f"RSS Filtered: {len(active_alerts)} active, {len(expired_alerts)} expired, {len(unknown_status_alerts)} unknown.")
        
        if active_alerts:
            active_alerts.sort(key=lambda x: x.get('sent') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            final_alerts = active_alerts
        else:
            all_fallback_alerts = sorted(expired_alerts + unknown_status_alerts, 
                                         key=lambda x: x.get('sent') or x.get('expires') or datetime.min.replace(tzinfo=timezone.utc), 
                                         reverse=True)
            if all_fallback_alerts:
                logging.info(f"No active 'actual' alerts from RSS. Returning most recent fallback: {all_fallback_alerts[0].get('headline')}")
                final_alerts = all_fallback_alerts[:1] 
    
    return final_alerts


if __name__ == '__main__':
    # ... (Your existing __main__ block or new tests for RSS feed) ...
    logging.basicConfig(level=logging.INFO)
    print("\n--- Testing GMet RSS Alert Fetch (No specific keywords, should fetch general weather) ---")
    rss_alerts = get_ghana_meteo_alerts(disaster_keywords=[])
    if rss_alerts and isinstance(rss_alerts, list) and len(rss_alerts) > 0 and "error" not in rss_alerts[0]:
        print(f"Found {len(rss_alerts)} alert(s) from GMet RSS:")
        for i, alert in enumerate(rss_alerts):
            print(f"\n--- Alert {i+1} ---")
            print(f"  Headline: {alert.get('headline')}")
            print(f"  Event: {alert.get('event')}")
            print(f"  Sent: {alert.get('sent')}")
            print(f"  Effective: {alert.get('effective')}")
            print(f"  Expires: {alert.get('expires')}")
            print(f"  Description: {alert.get('description')[:100]}...")
            print(f"  Area: {alert.get('areaDesc')}")
            print(f"  Coords: Lat {alert.get('latitude')}, Lon {alert.get('longitude')}")
            print(f"  CAP URL: {alert.get('cap_url')}")
    elif rss_alerts and "error" in rss_alerts[0]:
        print(f"Error: {rss_alerts[0]['error']}")
    else:
        print("No alerts found or an error occurred.")