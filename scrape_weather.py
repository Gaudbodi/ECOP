import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
from scrapegraphai.graphs import SmartScraperGraph
from scrapegraphai.utils import prettify_exec_info
import logging

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# AI Configuration for ScrapeGraphAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

def get_ai_config_for_scraping():
    """
    Determines the best AI configuration for ScrapeGraphAI based on available services.
    Priority: OpenAI -> Ollama -> Error
    """
    if OPENAI_API_KEY:
        return {
            "llm": {
                "api_key": OPENAI_API_KEY,
                "model": f"openai/{OPENAI_MODEL}",
                "temperature": 0.1,
            },
            "verbose": True,
            "headless": True,
        }
    else:
        # Check if Ollama is available
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=2)
            if response.status_code == 200:
                return {
                    "llm": {
                        "model": f"ollama/{OLLAMA_MODEL}",
                        "temperature": 0.1,
                        "base_url": OLLAMA_BASE_URL,
                    },
                    "verbose": True,
                    "headless": True,
                }
            else:
                raise Exception("Ollama not available")
        except Exception as e:
            logging.error(f"Neither OpenAI nor Ollama available for scraping: {e}")
            return None

def scrape_ghaap_with_ai(url, force_model=None):
    """
    Uses ScrapeGraphAI with OpenAI (primary) or Ollama (fallback) to intelligently scrape
    agricultural advisory data from GHAAP website.

    Args:
        url (str): The GHAAP URL to scrape
        force_model (str, optional): Force a specific model (e.g., "openai/gpt-3.5-turbo")

    Returns:
        dict: Structured data containing agricultural advisory information
    """
    logging.info(f"Starting AI-powered scraping of URL: {url}")

    # Extract expected parameters from URL for targeted scraping
    region_hint = "Ashanti Region"
    district_hint = "Ejisu"
    crop_hint = "Maize"
    year_hint = "2025"

    # Try to extract actual parameters from URL
    if "REG02" in url:
        region_hint = "Ashanti Region"
    if "DS031" in url:
        district_hint = "Ejisu"
    if "CT0000000001" in url:
        crop_hint = "Maize"
    if "yeartxt=" in url:
        year_match = url.split("yeartxt=")[1].split("&")[0] if "&" in url.split("yeartxt=")[1] else url.split("yeartxt=")[1]
        year_hint = year_match

    # Define the enhanced prompt for agricultural data extraction
    prompt = f"""
    Extract agricultural advisory information from this GHAAP (Ghana Agriculture and Agribusiness Portal) webpage.

    IMPORTANT: This page should contain information specifically for:
    - Region: {region_hint}
    - District: {district_hint}
    - Crop: {crop_hint}
    - Year: {year_hint}

    Please focus on finding and extracting information that matches these specific parameters. If the page shows different location or crop information, please note that in your response.

    Extract the following information in a structured JSON format:

    1. **Weather Information**: Current weather conditions, forecasts, temperature, rainfall, humidity, wind for {region_hint}, {district_hint}
    2. **Agricultural Advisories**: Specific farming recommendations, planting advice, harvest timing for {crop_hint}
    3. **Crop Information**: Details about {crop_hint} cultivation, growth stages, recommended varieties
    4. **Regional Data**: Verify if this matches {region_hint}, {district_hint}
    5. **Temporal Information**: Dates, seasons, timing information for {year_hint}
    6. **Warnings/Alerts**: Any urgent farming alerts, pest warnings, disease alerts for {crop_hint}
    7. **Seasonal Guidance**: Planting seasons, harvest periods for {crop_hint} in {region_hint}

    Please return a JSON object with these fields:
    {{
        "weather_forecast": "weather information found for {region_hint}, {district_hint}",
        "agricultural_recommendations": "farming advice for {crop_hint}",
        "crop_information": "details about {crop_hint} cultivation",
        "regional_information": "geographic coverage (verify if matches {region_hint}, {district_hint})",
        "date_information": "timing and dates for {year_hint}",
        "warnings_alerts": "any urgent information for {crop_hint}",
        "seasonal_recommendations": "seasonal farming guidance for {crop_hint}",
        "raw_advisory_text": "complete advisory text found on the page",
        "location_match": "true/false - does the found location match {region_hint}, {district_hint}",
        "crop_match": "true/false - does the found crop match {crop_hint}",
        "year_match": "true/false - does the found year match {year_hint}"
    }}

    If any information is not available, set the value to "Not available".
    Focus on extracting actual agricultural content for {crop_hint} in {region_hint}, {district_hint} for {year_hint}, not navigation or UI elements.
    If the page contains information for different locations or crops, please clearly indicate this in the response.
    """

    # Get AI configuration
    if force_model:
        if force_model.startswith("openai/"):
            graph_config = {
                "llm": {
                    "api_key": OPENAI_API_KEY,
                    "model": force_model,
                    "temperature": 0.1,
                },
                "verbose": True,
                "headless": True,
            }
        elif force_model.startswith("ollama/"):
            graph_config = {
                "llm": {
                    "model": force_model,
                    "temperature": 0.1,
                    "base_url": OLLAMA_BASE_URL,
                },
                "verbose": True,
                "headless": True,
            }
        else:
            logging.error(f"Unsupported model format: {force_model}")
            return {"error": f"Unsupported model: {force_model}"}
    else:
        graph_config = get_ai_config_for_scraping()
        if not graph_config:
            return {"error": "No AI service available for scraping"}

    try:
        # Create the SmartScraperGraph
        logging.info(f"Creating SmartScraperGraph with model: {graph_config['llm'].get('model', 'unknown')}")
        smart_scraper_graph = SmartScraperGraph(
            prompt=prompt,
            source=url,
            config=graph_config
        )

        # Run the scraper
        logging.info("Running AI scraper...")
        result = smart_scraper_graph.run()

        if result and isinstance(result, dict):
            logging.info("AI scraping completed successfully")
            # Ensure we have a raw_advisory_text field for summarization
            if "raw_advisory_text" not in result or not result["raw_advisory_text"]:
                # Create a combined text from all available fields
                text_parts = []
                for key, value in result.items():
                    if value and value != "Not available" and isinstance(value, str):
                        text_parts.append(f"{key}: {value}")
                result["raw_advisory_text"] = " | ".join(text_parts) if text_parts else "No advisory text extracted"

            return result
        else:
            logging.warning("AI scraping returned empty or invalid result")
            return {"error": "AI scraping returned no data", "advisory_text": "No data extracted by AI scraper"}

    except Exception as e:
        logging.error(f"Error during AI scraping: {e}")
        return {"error": str(e), "advisory_text": "Failed to scrape data using AI method"}

def scrape_ghaap_with_selenium(url, target_element_id="wt_smssend", timeout=30):
    """
    Uses Selenium to scrape GHAAP website and specifically target an element by ID.

    Args:
        url (str): The GHAAP URL to scrape
        target_element_id (str): The ID of the element to find (default: "wt_smssend")
        timeout (int): Maximum time to wait for elements (default: 30 seconds)

    Returns:
        dict: Structured data containing the scraped information
    """
    logging.info(f"Starting Selenium scraping of URL: {url}")
    logging.info(f"Looking for element with ID: {target_element_id}")

    driver = None
    try:
        # Configure Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Initialize the Chrome driver
        logging.info("Initializing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Set page load timeout
        driver.set_page_load_timeout(timeout)

        # Navigate to the URL
        logging.info(f"Navigating to URL: {url}")
        driver.get(url)

        # Wait for the page to load
        logging.info("Waiting for page to load...")
        time.sleep(3)

        # Try to find the target element by ID
        target_element = None
        target_text = ""

        try:
            logging.info(f"Looking for element with ID: {target_element_id}")
            target_element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, target_element_id))
            )
            target_text = target_element.text.strip()
            logging.info(f"Found target element! Text content: {target_text[:200]}...")

        except TimeoutException:
            logging.warning(f"Target element with ID '{target_element_id}' not found within {timeout} seconds")

        # Also try to find other relevant elements and content
        additional_content = []

        # Look for common agricultural/weather content selectors
        content_selectors = [
            "div[class*='advisory']",
            "div[class*='forecast']",
            "div[class*='weather']",
            "div[class*='crop']",
            "div[class*='content']",
            ".panel-body",
            ".card-body",
            "main",
            "article"
        ]

        for selector in content_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements[:3]:  # Limit to first 3 matches per selector
                    text = element.text.strip()
                    if len(text) > 50 and text not in additional_content:
                        additional_content.append(text)
                        logging.info(f"Found additional content via selector '{selector}': {text[:100]}...")
            except Exception as e:
                logging.debug(f"Error with selector '{selector}': {e}")

        # Try to find tables with agricultural data
        table_data = []
        try:
            tables = driver.find_elements(By.TAG_NAME, "table")
            for i, table in enumerate(tables[:2]):  # Check first 2 tables
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) > 1:  # Has header and data rows
                        table_text = table.text.strip()
                        if len(table_text) > 50:
                            table_data.append({
                                "table_index": i,
                                "content": table_text,
                                "row_count": len(rows)
                            })
                            logging.info(f"Found table {i} with {len(rows)} rows")
                except Exception as e:
                    logging.debug(f"Error processing table {i}: {e}")
        except Exception as e:
            logging.debug(f"Error finding tables: {e}")

        # Get page title and URL for context
        page_title = driver.title
        current_url = driver.current_url

        # Compile results
        result = {
            "method": "selenium_scraping",
            "source": "GHAAP (Selenium)",
            "url": current_url,
            "page_title": page_title,
            "target_element_id": target_element_id,
            "target_element_found": target_element is not None,
            "target_element_text": target_text,
            "additional_content": additional_content,
            "table_data": table_data,
            "scraping_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": True
        }

        # Create advisory text from found content
        advisory_parts = []

        if target_text:
            advisory_parts.append(f"Target Content (ID={target_element_id}): {target_text}")

        if additional_content:
            advisory_parts.append(f"Additional Content: {' | '.join(additional_content[:3])}")

        if table_data:
            table_summaries = [f"Table {t['table_index']}: {t['content'][:100]}..." for t in table_data]
            advisory_parts.append(f"Table Data: {' | '.join(table_summaries)}")

        if advisory_parts:
            result["advisory_text"] = " || ".join(advisory_parts)
        else:
            result["advisory_text"] = f"Page loaded successfully but no relevant content found. Page title: {page_title}"

        logging.info(f"Selenium scraping completed successfully. Found target element: {target_element is not None}")
        return result

    except WebDriverException as e:
        error_msg = f"WebDriver error: {str(e)}"
        logging.error(error_msg)
        return {
            "method": "selenium_scraping",
            "source": "GHAAP (Selenium)",
            "error": error_msg,
            "advisory_text": f"Failed to scrape using Selenium: {error_msg}",
            "success": False,
            "scraping_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        error_msg = f"Unexpected error during Selenium scraping: {str(e)}"
        logging.error(error_msg)
        return {
            "method": "selenium_scraping",
            "source": "GHAAP (Selenium)",
            "error": error_msg,
            "advisory_text": f"Failed to scrape using Selenium: {error_msg}",
            "success": False,
            "scraping_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    finally:
        # Always close the driver
        if driver:
            try:
                driver.quit()
                logging.info("Chrome WebDriver closed successfully")
            except Exception as e:
                logging.warning(f"Error closing WebDriver: {e}")

def scrape_ghaap_weather_forecast(url):
    """
    Enhanced scraping function for GHAAP website with better error handling and multiple fallback strategies.
    """
    print(f"Attempting to scrape URL: {url}")

    # Define multiple User-Agent headers to try
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
    ]

    for i, user_agent in enumerate(user_agents):
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        try:
            print(f"Attempt {i+1}: Using User-Agent: {user_agent[:50]}...")

            # Fetch the content of the page with timeout
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try multiple table selectors
            table_selectors = [
                'table.table.table-striped.table-bordered.table-hover',
                'table.table-striped',
                'table.table-bordered',
                'table',
                '.table',
                '#forecast-table',
                '[class*="table"]'
            ]

            table = None
            for selector in table_selectors:
                table = soup.select_one(selector)
                if table:
                    print(f"Found table using selector: {selector}")
                    print(f"Table HTML preview: {str(table)[:200]}...")
                    break

            if not table:
                # Table is empty or doesn't exist - try to find other content
                print(f"Attempt {i+1}: Table empty or not found, looking for alternative content...")

                # Look for any content that might contain agricultural data
                content_selectors = [
                    'div[class*="content"]',
                    'div[class*="forecast"]',
                    'div[class*="advisory"]',
                    'div[class*="weather"]',
                    'div[class*="crop"]',
                    'section',
                    'article',
                    '.panel-body',
                    '.card-body',
                    'main'
                ]

                text_content = []
                for selector in content_selectors:
                    elements = soup.select(selector)
                    for element in elements[:2]:  # Limit to first 2 per selector
                        text = element.get_text(strip=True)
                        if len(text) > 100:  # Only include substantial content
                            text_content.append(text)

                # Also try to get any text from the page that might be relevant
                page_text = soup.get_text()
                if len(page_text) > 500:
                    # Look for agricultural keywords in the page
                    agro_keywords = ['forecast', 'weather', 'crop', 'advisory', 'temperature', 'rainfall', 'planting', 'harvest', 'season']
                    if any(keyword.lower() in page_text.lower() for keyword in agro_keywords):
                        # Extract relevant paragraphs
                        paragraphs = soup.find_all('p')
                        for p in paragraphs[:5]:
                            p_text = p.get_text(strip=True)
                            if len(p_text) > 50 and any(keyword.lower() in p_text.lower() for keyword in agro_keywords):
                                text_content.append(p_text)

                if text_content:
                    print(f"Found {len(text_content)} content areas with potential agricultural data")
                    return create_advisory_from_text(text_content, url)

                print(f"Attempt {i+1}: No relevant content found")
                continue

            # Extract table data
            headers_list = []
            tbody = table.find('tbody')
            thead = table.find('thead')

            if thead:
                for th in thead.find_all(['th', 'td']):
                    headers_list.append(th.get_text(strip=True))

            # Extract table rows
            data_rows = []
            rows = tbody.find_all('tr') if tbody else table.find_all('tr')

            print(f"Found {len(rows)} rows in table")

            for j, row in enumerate(rows):
                columns = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
                print(f"Row {j+1}: {len(columns)} columns - {columns[:3] if columns else 'No columns'}")
                if columns and len(columns) > 0:  # Accept any row with data
                    data_rows.append(columns)

            print(f"Extracted {len(data_rows)} data rows")

            if data_rows:
                # Ensure headers match data columns
                if not headers_list or len(headers_list) != len(data_rows[0]):
                    headers_list = [f"Column_{i+1}" for i in range(len(data_rows[0]))]

                df = pd.DataFrame(data_rows, columns=headers_list)
                print(f"Scraping successful! Found {len(df)} rows of data.")
                return df
            else:
                print(f"Attempt {i+1}: Table found but no data rows extracted")
                # Try to extract content from the page instead
                print(f"Attempt {i+1}: Looking for alternative content...")

                # Look for any content that might contain agricultural data
                content_selectors = [
                    'div[class*="content"]',
                    'div[class*="forecast"]',
                    'div[class*="advisory"]',
                    'div[class*="weather"]',
                    'div[class*="crop"]',
                    'section',
                    'article',
                    '.panel-body',
                    '.card-body',
                    'main'
                ]

                text_content = []
                for selector in content_selectors:
                    elements = soup.select(selector)
                    for element in elements[:2]:  # Limit to first 2 per selector
                        text = element.get_text(strip=True)
                        if len(text) > 100:  # Only include substantial content
                            text_content.append(text)

                # Also try to get any text from the page that might be relevant
                page_text = soup.get_text()
                if len(page_text) > 500:
                    # Look for agricultural keywords in the page
                    agro_keywords = ['forecast', 'weather', 'crop', 'advisory', 'temperature', 'rainfall', 'planting', 'harvest', 'season']
                    if any(keyword.lower() in page_text.lower() for keyword in agro_keywords):
                        # Extract relevant paragraphs
                        paragraphs = soup.find_all('p')
                        for p in paragraphs[:5]:
                            p_text = p.get_text(strip=True)
                            if len(p_text) > 50 and any(keyword.lower() in p_text.lower() for keyword in agro_keywords):
                                text_content.append(p_text)

                if text_content:
                    print(f"Found {len(text_content)} content areas with potential agricultural data")
                    return create_advisory_from_text(text_content, url)

                continue

        except requests.exceptions.RequestException as e:
            print(f"Attempt {i+1}: Network error: {e}")
            continue
        except Exception as e:
            print(f"Attempt {i+1}: Unexpected error: {e}")
            continue

    print("All scraping attempts failed.")
    return pd.DataFrame()

def create_advisory_from_text(text_content, url):
    """
    Creates an advisory DataFrame from extracted text content when table scraping fails.
    """
    advisory_data = []

    for i, text in enumerate(text_content):
        # Look for weather-related keywords and extract relevant information
        weather_keywords = ['temperature', 'rainfall', 'humidity', 'wind', 'forecast', 'advisory', 'crop', 'planting']

        relevant_sentences = []
        sentences = text.split('.')

        for sentence in sentences:
            if any(keyword.lower() in sentence.lower() for keyword in weather_keywords):
                relevant_sentences.append(sentence.strip())

        if relevant_sentences:
            advisory_data.append({
                'Section': f'Content_Area_{i+1}',
                'Advisory_Text': ' | '.join(relevant_sentences[:3]),  # Limit to first 3 relevant sentences
                'Source': 'GHAAP_Text_Extraction',
                'URL': url
            })

    if advisory_data:
        return pd.DataFrame(advisory_data)
    else:
        return pd.DataFrame()

def scrape_ghaap_hybrid(url, use_ai=True, use_selenium=True, force_model=None, target_element_id="wt_smssend"):
    """
    Enhanced hybrid scraping function with multiple fallback strategies:
    1. AI scraping with OpenAI/Ollama (if use_ai=True)
    2. Selenium scraping (if use_selenium=True)
    3. Traditional requests + BeautifulSoup scraping

    Args:
        url (str): The GHAAP URL to scrape
        use_ai (bool): Whether to try AI scraping first (default: True)
        use_selenium (bool): Whether to try Selenium scraping (default: True)
        force_model (str, optional): Force a specific AI model
        target_element_id (str): ID of target element for Selenium (default: "wt_smssend")

    Returns:
        dict: Structured data containing agricultural advisory information
    """
    logging.info(f"Starting hybrid scraping of URL: {url} (AI: {use_ai}, Selenium: {use_selenium})")

    if use_ai:
        try:
            logging.info("Attempting AI-powered scraping with OpenAI/Ollama...")
            ai_result = scrape_ghaap_with_ai(url, force_model)

            if ai_result and "error" not in ai_result:
                logging.info("AI scraping successful!")
                advisory_text = format_ai_result_for_advisory(ai_result)

                return {
                    "method": "ai_scraping",
                    "ai_model": ai_result.get("model_used", "unknown"),
                    "data": ai_result,
                    "advisory_text": advisory_text,
                    "raw_advisory_text": ai_result.get("raw_advisory_text", advisory_text),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "GHAAP (AI-scraped with OpenAI/Ollama)"
                }
            else:
                error_msg = ai_result.get("error", "Unknown AI error") if ai_result else "No result from AI"
                logging.warning(f"AI scraping failed: {error_msg}, trying next method...")
        except Exception as e:
            logging.warning(f"AI scraping error: {e}, trying next method...")

    # Strategy 2: Selenium scraping
    if use_selenium:
        try:
            logging.info(f"Attempting Selenium scraping targeting element ID: {target_element_id}...")
            selenium_result = scrape_ghaap_with_selenium(url, target_element_id)

            if selenium_result and selenium_result.get("success", False):
                # Selenium scraping succeeded
                logging.info("Selenium scraping completed successfully")
                return selenium_result
            else:
                logging.warning(f"Selenium scraping failed: {selenium_result.get('error', 'Unknown error')}, falling back to traditional scraping...")

        except Exception as e:
            logging.warning(f"Selenium scraping failed: {e}, falling back to traditional scraping...")

    # Strategy 3: Traditional scraping fallback
    logging.info("Using traditional scraping method...")
    try:
        df_result = scrape_ghaap_weather_forecast(url)

        if not df_result.empty:
            advisory_text = format_dataframe_for_advisory(df_result)
            return {
                "method": "traditional_scraping",
                "data": df_result.to_dict('records'),
                "advisory_text": advisory_text,
                "raw_advisory_text": advisory_text,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "GHAAP (Traditional scraping)"
            }
        else:
            logging.error("Traditional scraping also failed - no data extracted")
            return {
                "method": "failed",
                "error": "Both AI and traditional scraping methods failed to extract data",
                "advisory_text": "Unable to retrieve agricultural advisory data from GHAAP website. Please check the website directly.",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "GHAAP"
            }
    except Exception as e:
        logging.error(f"Traditional scraping failed with error: {e}")
        return {
            "method": "failed",
            "error": f"All scraping methods failed. Last error: {str(e)}",
            "advisory_text": "Unable to retrieve agricultural advisory data from GHAAP website. Please check the website directly.",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "GHAAP"
        }

def format_ai_result_for_advisory(ai_result):
    """
    Formats AI scraping result into a readable advisory text with enhanced structure.
    Now includes validation checks for location and crop matching.
    """
    if not isinstance(ai_result, dict):
        return str(ai_result)[:500] + "..." if len(str(ai_result)) > 500 else str(ai_result)

    advisory_parts = []

    # Check if location and crop match expectations
    location_match = ai_result.get("location_match", "unknown")
    crop_match = ai_result.get("crop_match", "unknown")
    year_match = ai_result.get("year_match", "unknown")

    # Add validation info if there are mismatches
    if location_match == "false" or crop_match == "false" or year_match == "false":
        mismatch_info = []
        if location_match == "false":
            mismatch_info.append("location")
        if crop_match == "false":
            mismatch_info.append("crop")
        if year_match == "false":
            mismatch_info.append("year")
        advisory_parts.append(f"⚠️ Data mismatch detected for: {', '.join(mismatch_info)}")

    # Priority order for information extraction
    priority_fields = [
        ("weather_forecast", "Weather"),
        ("agricultural_recommendations", "Agricultural Advice"),
        ("crop_information", "Crop Info"),
        ("warnings_alerts", "Alerts"),
        ("regional_information", "Region"),
        ("seasonal_recommendations", "Seasonal Guidance"),
        ("date_information", "Timing")
    ]

    # Extract information in priority order
    for field, label in priority_fields:
        if field in ai_result and ai_result[field] and ai_result[field] != "Not available":
            value = ai_result[field]
            if isinstance(value, str) and len(value.strip()) > 0:
                # Truncate very long values
                if len(value) > 150:
                    value = value[:147] + "..."
                advisory_parts.append(f"{label}: {value}")

    # If we have structured data, use it
    if advisory_parts:
        return " | ".join(advisory_parts)

    # Fallback: try to use raw_advisory_text if available
    if "raw_advisory_text" in ai_result and ai_result["raw_advisory_text"]:
        raw_text = ai_result["raw_advisory_text"]
        if len(raw_text) > 500:
            return raw_text[:497] + "..."
        return raw_text

    # Final fallback: convert entire result to string
    result_str = str(ai_result)
    return result_str[:500] + "..." if len(result_str) > 500 else result_str

def build_ghaap_url(region="REG02", district="DS031", crop="CT0000000001", year="2025"):
    """
    Builds a GHAAP URL with the specified parameters.

    Args:
        region (str): Region code (e.g., "REG02" for Ashanti Region)
        district (str): District code (e.g., "DS031" for Ejisu)
        crop (str): Crop code (e.g., "CT0000000001" for Maize)
        year (str): Year (e.g., "2025")

    Returns:
        str: Complete GHAAP URL
    """
    base_url = "https://ghaap.com/weather-forecast/index.php"
    # Try different parameter formats that might work with GHAAP
    params = f"?p=crop-search-event&regiontxt={region}&districttxt={district}&crop={crop}&yeartxt={year}"
    return base_url + params

def get_alternative_ghaap_urls(region="REG02", district="DS031", crop="CT0000000001", year="2025"):
    """
    Returns multiple URL variations to try for GHAAP scraping.
    """
    base_url = "https://ghaap.com/weather-forecast/index.php"

    # Different parameter formats to try
    url_variations = [
        f"{base_url}?p=crop-search-event&regiontxt={region}&districttxt={district}&crop={crop}&yeartxt={year}",
        f"{base_url}?p=crop-search-event®iontxt={region}&districttxt={district}&crop={crop}&yeartxt={year}",
        f"{base_url}?regiontxt={region}&districttxt={district}&crop={crop}&yeartxt={year}",
        f"{base_url}?p=crop-search-event&region={region}&district={district}&crop={crop}&year={year}",
        # Try with different region codes that might work for Ashanti
        f"{base_url}?p=crop-search-event&regiontxt=REG02&districttxt=DS031&crop=CT0000000001&yeartxt={year}",
        # Fallback to a working example URL structure
        f"{base_url}?p=crop-search-event®iontxt=REG02&districttxt=DS028&crop=CT0000000008&yeartxt={year}",
    ]

    return url_variations

def get_ghaap_advisory(url=None, region=None, district=None, crop=None, year=None, use_ai=True, use_selenium=True, force_model=None, target_element_id="wt_smssend"):
    """
    Main function to get GHAAP agricultural advisory data using AI-powered scraping.
    This function can be easily imported and used by other modules like Flask app.
    Now tries multiple URL variations to find working data.

    Args:
        url (str, optional): Custom URL to scrape. If None, builds URL from parameters.
        region (str, optional): Region code (e.g., "REG02" for Ashanti Region)
        district (str, optional): District code (e.g., "DS031" for Ejisu)
        crop (str, optional): Crop code (e.g., "CT0000000001" for Maize)
        year (str, optional): Year (e.g., "2025")
        use_ai (bool): Whether to use AI scraping first (default: True)
        force_model (str, optional): Force a specific AI model (e.g., "openai/gpt-3.5-turbo")

    Returns:
        dict: Structured advisory data with AI-extracted information
    """
    if url is not None:
        # Use provided URL directly
        logging.info(f"Getting GHAAP advisory for provided URL: {url}")
        return scrape_ghaap_hybrid(url, use_ai=use_ai, force_model=force_model)

    # Build URLs from parameters or use defaults for Ashanti Region, Ejisu, Maize, 2025
    region = region or "REG02"  # Ashanti Region
    district = district or "DS031"  # Ejisu
    crop = crop or "CT0000000001"  # Maize
    year = year or "2025"

    # Get multiple URL variations to try
    url_variations = get_alternative_ghaap_urls(region, district, crop, year)

    logging.info(f"Trying {len(url_variations)} URL variations for GHAAP advisory")

    best_result = None
    for i, test_url in enumerate(url_variations):
        logging.info(f"Attempt {i+1}/{len(url_variations)}: {test_url}")

        result = scrape_ghaap_hybrid(test_url, use_ai=use_ai, use_selenium=use_selenium, force_model=force_model, target_element_id=target_element_id)

        if result and result.get('method') != 'failed':
            # Check if this result contains relevant data for our target location/crop
            advisory_text = result.get('advisory_text', '').lower()

            # Look for indicators that this might be the right data
            has_relevant_data = any(keyword in advisory_text for keyword in [
                'ashanti', 'ejisu', 'maize', 'corn', 'crop', 'agricultural', 'farming'
            ])

            # Check if it's not showing wrong location data
            has_wrong_location = any(wrong_loc in advisory_text for wrong_loc in [
                'asunafo north', 'asunafo south', 'goaso', 'kukuom'
            ])

            if has_relevant_data and not has_wrong_location:
                logging.info(f"Found relevant data on attempt {i+1}")
                return result
            elif not best_result or (has_relevant_data and not has_wrong_location):
                # Keep this as the best result so far
                best_result = result
                logging.info(f"Keeping result from attempt {i+1} as best so far")
        else:
            logging.warning(f"Attempt {i+1} failed: {result.get('error', 'Unknown error') if result else 'No result'}")

    # Return the best result we found, or the last result if none were good
    if best_result:
        logging.info("Returning best result found from URL variations")
        return best_result
    else:
        logging.error("All URL variations failed")
        return {
            "method": "failed",
            "error": "All URL variations failed to retrieve relevant data",
            "advisory_text": f"Unable to retrieve agricultural advisory data for {region}, {district}, {crop}, {year}. Please check the website directly.",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "GHAAP"
        }

def get_ghaap_advisory_single_url(url, use_ai=True, use_selenium=True, force_model=None, target_element_id="wt_smssend"):
    """
    Get GHAAP advisory for a single URL using the hybrid scraping approach.
    """
    return scrape_ghaap_hybrid(url, use_ai=use_ai, use_selenium=use_selenium, force_model=force_model, target_element_id=target_element_id)

def format_dataframe_for_advisory(df):
    """
    Formats DataFrame result into a readable advisory text.
    """
    if df.empty:
        return "No agricultural data available."

    # Try to create a summary from the DataFrame
    summary_parts = []

    # Get first few rows as summary
    for _, row in df.head(3).iterrows():
        row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
        if row_text:
            summary_parts.append(row_text)

    if summary_parts:
        return " || ".join(summary_parts)
    else:
        return f"Agricultural data available with {len(df)} records. Check detailed output for more information."

# --- Main execution ---
if __name__ == "__main__":
    # Use the correct URL for Ashanti Region, Ejisu, Maize, 2025
    target_url = build_ghaap_url(region="REG02", district="DS031", crop="CT0000000001", year="2025")
    output_filename = "ghaap_weather_forecast_data.csv"
    json_output_filename = "ghaap_ai_scraped_data.json"

    print("=== GHAAP Agricultural Data Scraper (Enhanced with AI) ===\n")
    print(f"Target URL: {target_url}")
    print("Expected data: Ashanti Region, Ejisu District, Maize crop, Year 2025\n")

    # Try hybrid scraping (AI-powered with OpenAI first, then traditional fallback)
    print("Attempting AI-powered scraping with OpenAI/Ollama...")
    result = scrape_ghaap_hybrid(target_url, use_ai=True, force_model=None)

    print(f"\n--- Scraping Results ---")
    print(f"Method used: {result.get('method', 'unknown')}")
    print(f"Source: {result.get('source', 'unknown')}")
    print(f"Timestamp: {result.get('timestamp', 'unknown')}")

    if "error" in result:
        print(f"Error: {result['error']}")

    print(f"\n--- Advisory Text ---")
    print(result.get('advisory_text', 'No advisory text available'))

    # Save results
    if result.get('method') == 'ai':
        # Save AI results as JSON
        try:
            with open(json_output_filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nAI scraping results saved to {json_output_filename}")
        except Exception as e:
            print(f"Error saving AI results: {e}")

    elif result.get('method') == 'traditional' and result.get('data'):
        # Save traditional results as CSV
        try:
            df = pd.DataFrame(result['data'])
            df.to_csv(output_filename, index=False, encoding='utf-8')
            print(f"\nTraditional scraping results saved to {output_filename}")

            print("\n--- Scraped Data (first 5 rows) ---")
            print(df.head())
        except Exception as e:
            print(f"Error saving traditional results: {e}")

    # Also save a summary JSON file regardless of method
    summary_filename = "ghaap_scraping_summary.json"
    summary = {
        "url": target_url,
        "method": result.get('method'),
        "timestamp": result.get('timestamp'),
        "advisory_text": result.get('advisory_text'),
        "source": result.get('source'),
        "success": "error" not in result
    }

    try:
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\nScraping summary saved to {summary_filename}")
    except Exception as e:
        print(f"Error saving summary: {e}")

    print("\n=== Script finished ===")