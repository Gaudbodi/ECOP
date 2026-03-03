import os
from pymongo import MongoClient
from datetime import datetime

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from gtts import gTTS
import json

# Directory to save audio files
AUDIO_OUTPUT_DIR = "generated_audio_messages"


# --- Configuration (move to a config file later) ---
MONGO_URI = "mongodb+srv://francisyiryel:gfc3C4OizIvQr6mR@cluster0.pcd3g.mongodb.net/new_numbering?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "fsrp_aggregator"
ADVISORY_COLLECTION = "crop_advisories"
FARMER_COLLECTION = "farmers"


# --- Constants for PXS Website (IDs and Selectors) ---
PXS_LOGIN_URL = "https://web.pxsghana.com/login"
PXS_SEARCH_URL = "https://web.pxsghana.com/search" # Direct URL to the search page

# Login Page Elements
USERNAME_FIELD_ID = "UserName"
PASSWORD_FIELD_ID = "Password"
LOGIN_BUTTON_ID = "LoginButton"

# Post-Login Operator Selection (Inports Page)
OPERATOR_DROPDOWN_ID = "IdentitiesDropDownList" # Dropdown for selecting MTN, Telecel etc.

# Search Page Elements
PHONE_NUMBER_INPUT_ID = "MainContent_OloPhoneNumberTextBox"
SEARCH_BUTTON_ID = "MainContent_OloInfoButton"
# This is the SPAN that will contain the operator name
OPERATOR_RESULT_LABEL_ID = "MainContent_CurrentOperatorLabel"
# This is the TR that appears when results are loaded
OPERATOR_RESULT_ROW_ID = "MainContent_CurrentOperatorRow"



def get_db_connection():
    """Establishes connection to MongoDB."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db
def get_active_advisories(db, current_date_dt):
    """
    Fetches advisories active on the given current_date_dt.
    Assumes 'advisory.start_date' and 'advisory.end_date' are stored as BSON Date types in MongoDB.

    Args:
        db: MongoDB database object.
        current_date_dt: A Python datetime object representing the current date.
                         Time part will be ignored if dates in DB are date-only.
                         For robust comparison, it's good if dates in DB are stored
                         at midnight (e.g., YYYY-MM-DD 00:00:00).
    Returns:
        A list of advisory documents that are active on the current_date_dt.
    """
    if not isinstance(current_date_dt, datetime):
        raise ValueError("current_date_dt must be a datetime object.")

    advisories_col = db[ADVISORY_COLLECTION]

    # Construct the query using the datetime object directly.
    # We are querying against the nested fields within the 'advisory' object.
    query = {
        "advisory.start_date": {"$lte": current_date_dt}, # Advisory starts on or before current_date_dt
        "advisory.end_date": {"$gte": current_date_dt}   # Advisory ends on or after current_date_dt
    }
    
    active_advisories = advisories_col.find(query)
    return list(active_advisories)

def get_farmers_for_crop(db, crop_name):
    """Fetches farmers subscribed to a specific crop."""
    farmers_col = db[FARMER_COLLECTION]

    matched_farmers = farmers_col.find({"crops": {"$regex": f"^{crop_name}$", "$options": "i"}})
    return list(matched_farmers)

def extract_crop_name_from_advisory(advisory_crop_field):
    """Extracts crop name from 'CODE/name' format."""
    if "/" in advisory_crop_field:
        return advisory_crop_field.split("/")[1].lower()
    return advisory_crop_field.lower() # Fallback if no code




#selenium logic for getting network operator from PXS
def convert_to_pxs_format(phone_number_e164):
    """
    Converts a phone number from E.164 format (e.g., +23324xxxxxxx)
    to the local PXS format (e.g., 024xxxxxxx).
    """
    if phone_number_e164 and phone_number_e164.startswith("+233") and len(phone_number_e164) == 13:
        return "0" + phone_number_e164[4:]
    elif phone_number_e164 and phone_number_e164.startswith("0") and len(phone_number_e164) == 10:
        return phone_number_e164 # Already in local format
    else:
        # Handle other cases or return None/raise error if format is unexpected
        print(f"Warning: Phone number {phone_number_e164} is not in expected E.164 or local format.")
        return None


def login_and_navigate_to_search(driver, username, password, operator_to_select="MTN"):
    """
    Logs into the PXS website, handles initial operator selection,
    and navigates to the search page.

    Args:
        driver: The Selenium WebDriver instance.
        username (str): The login username.
        password (str): The login password.
        operator_to_select (str): The operator to select from the dropdown (e.g., "MTN").

    Returns:
        bool: True if navigation to search page is successful, False otherwise.
    """
    try:
        print("Navigating to PXS login page...")
        driver.get(PXS_LOGIN_URL)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, USERNAME_FIELD_ID)))
        driver.find_element(By.ID, USERNAME_FIELD_ID).send_keys(username)
        driver.find_element(By.ID, PASSWORD_FIELD_ID).send_keys(password)
        driver.find_element(By.ID, LOGIN_BUTTON_ID).click()
        print("Login submitted.")

        # Wait for the operator dropdown to appear on the "Inports" page
        print(f"Waiting for operator dropdown '{OPERATOR_DROPDOWN_ID}'...")
        operator_dropdown = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, OPERATOR_DROPDOWN_ID))
        )
        print(f"Selecting operator '{operator_to_select}'...")
        operator_dropdown.send_keys(operator_to_select) 
        # Selecting from dropdown might trigger a page change or content load.
        # Add a small explicit wait or wait for a known element on the next page if needed.
        time.sleep(5) # We allow time for page to react to dropdown selection.
                      # Might replace with WebDriverWait for a specific element if possible.

        print("Navigating to the PXS Search page...")
        driver.get(PXS_SEARCH_URL) # Directly navigate to the search page

        # Verify we are on the search page by checking for the phone number input field
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, PHONE_NUMBER_INPUT_ID))
        )
        print("Successfully navigated to the PXS Search page.")
        return True

    except TimeoutException:
        print("Error: Timeout during login or navigation process.")
        return False
    except NoSuchElementException:
        print("Error: A required element was not found during login/navigation.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during login/navigation: {e}")
        return False


def get_network_operator_from_pxs(driver, phone_number_local):
    """
    Searches for a phone number on the PXS website and retrieves its current network operator.
    Assumes driver is already on the search page.

    Args:
        driver: The Selenium WebDriver instance.
        phone_number_local (str): The phone number in local format (e.g., 024xxxxxxx).

    Returns:
        str: The network operator (e.g., "MTNGMN") or None if not found or an error occurs.
    """
    if not phone_number_local:
        return None
        
    try:
        phone_input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, PHONE_NUMBER_INPUT_ID))
        )
        phone_input_field.clear()
        phone_input_field.send_keys(phone_number_local)

        search_button = driver.find_element(By.ID, SEARCH_BUTTON_ID)
        search_button.click()

        # Wait for the result row to appear, indicating the search is complete
        # and the AJAX/PostBack has updated the content.
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, OPERATOR_RESULT_ROW_ID))
        )
        
        # Now that the row is present, get the operator label
        operator_label = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, OPERATOR_RESULT_LABEL_ID))
        )
        operator_name = operator_label.text.strip()
        

        return operator_name if operator_name else None

    except TimeoutException:
        print(f"Error: Timeout waiting for operator result for {phone_number_local}.")
        return None
    except NoSuchElementException:
        print(f"Error: Operator result element not found for {phone_number_local}.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred fetching operator for {phone_number_local}: {e}")
        return None


def generate_audio_message_gtts(text_to_speak, language_code, output_filename_base):
    """
    Generates an audio message from text using gTTS and saves it as an MP3 file.

    Args:
        text_to_speak (str): The text content for the audio message.
        language_code (str): The language code for TTS (e.g., 'en', 'ak' for Akan, 'fr').
        output_filename_base (str): A base name for the output MP3 file (without extension).
                                     Should be unique per message if possible.

    Returns:
        str: The full path to the saved audio file, or None if generation failed.
    """
    if not os.path.exists(AUDIO_OUTPUT_DIR):
        try:
            os.makedirs(AUDIO_OUTPUT_DIR)
            print(f"Created directory: {AUDIO_OUTPUT_DIR}")
        except OSError as e:
            print(f"Error creating directory {AUDIO_OUTPUT_DIR}: {e}")
            return None

    output_filepath = os.path.join(AUDIO_OUTPUT_DIR, f"{output_filename_base}.mp3")

    try:
        print(f"Generating audio for language '{language_code}' to '{output_filepath}'...")
        tts = gTTS(text=text_to_speak, lang=language_code, slow=False)
        tts.save(output_filepath)
        print("Audio generated successfully.")
        return output_filepath
    except Exception as e:
        # gTTS can sometimes raise errors for unsupported languages or network issues
        print(f"Error generating audio with gTTS for language '{language_code}': {e}")
        return None




def main_processing_logic():
    # --- PXS Credentials (Consider moving to a config file or environment variables) ---
    PXS_USERNAME = "fyiryel"
    PXS_PASSWORD = "NiggaTron38" # IMPORTANT: Securely manage credentials!

    db = get_db_connection()
    if db is None:
        print("Failed to connect to MongoDB. Exiting.")
        return

    # current_date_dt = datetime.now() 
    # Use datetime object for querying
    # For consistent daily checks, you might want to normalize to midnight:
    # current_date_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    #Use a specific date for testing
    current_date_dt = datetime(2025, 3, 20)

    print(f"Processing advisories for date: {current_date_dt.strftime('%Y-%m-%d')}")

    active_advisories = get_active_advisories(db, current_date_dt) # Pass datetime object

    if not active_advisories:
        print("No active advisories for today.")
        return

    # --- Initialize Selenium WebDriver for PXS ---
    pxs_driver = None
    pxs_login_successful = False
    final_output_list = []
    pxs_error_log = [] # Specific log for PXS errors

    try:
        print("Initializing PXS WebDriver...")
        service = Service(ChromeDriverManager().install())
        pxs_driver = webdriver.Chrome(service=service)
        # pxs_driver.implicitly_wait(5) # Optional: general implicit wait

        if login_and_navigate_to_search(pxs_driver, PXS_USERNAME, PXS_PASSWORD, operator_to_select="MTN"):
            pxs_login_successful = True
            print("PXS Login and navigation successful.")
        else:
            print("Failed to login to PXS or navigate to search page. Operator lookups will be skipped.")

        for advisory_doc in active_advisories:
            # The actual advisory data is nested under the 'advisory' key in your example structure
            advisory_data = advisory_doc.get("advisory", {}) # Get the nested advisory object
            sms_text = advisory_doc.get("sms_text", "") # sms_text is top-level with advisory object

            if not advisory_data or not sms_text:
                print(f"Skipping advisory document {advisory_doc.get('_id')} due to missing 'advisory' data or 'sms_text'.")
                continue
            
            advisory_crop_code_name = advisory_data.get("crop", "")
            advisory_crop_name = extract_crop_name_from_advisory(advisory_crop_code_name)

            if not advisory_crop_name:
                print(f"Could not determine crop for advisory linked to document: {advisory_doc.get('_id')}")
                continue

            print(f"\nProcessing advisory for crop: {advisory_crop_name.capitalize()}")
            print(f"Advisory SMS: {sms_text}")

            matched_farmers = get_farmers_for_crop(db, advisory_crop_name)

            if not matched_farmers:
                print(f"No farmers found for crop: {advisory_crop_name.capitalize()}")
                continue

            for farmer in matched_farmers:
                farmer_name = farmer.get("name")
                phone_number_e164 = farmer.get("phone_number")
                preferred_language = farmer.get("preferred_language", "en") # Default to English if not set

                print(f"  -> Preparing message for: {farmer_name} ({phone_number_e164}), Language: {preferred_language}")
                
                network_operator = "UNKNOWN" # Default if PXS lookup fails or is skipped
                if pxs_login_successful and pxs_driver:
                    pxs_phone_format = convert_to_pxs_format(phone_number_e164)
                    if pxs_phone_format:
                        print(f"    Looking up network operator for {pxs_phone_format} on PXS...")
                        op = get_network_operator_from_pxs(pxs_driver, pxs_phone_format)
                        if op:
                            network_operator = op
                            print(f"    Retrieved Operator: {network_operator}")
                        else:
                            print(f"    Failed to retrieve operator for {pxs_phone_format}.")
                            pxs_error_log.append({
                                "timestamp": datetime.now().isoformat(),
                                "phone_number": phone_number_e164,
                                "pxs_format_attempted": pxs_phone_format,
                                "error": "Operator not found or PXS error during lookup"
                            })
                    else:
                        print(f"    Could not convert phone {phone_number_e164} to PXS format for operator lookup.")
                        pxs_error_log.append({
                                "timestamp": datetime.now().isoformat(),
                                "phone_number": phone_number_e164,
                                "error": "Format conversion failed for PXS lookup"
                            })
                
                # Generate unique base filename for audio: farmername_date_crop_phonenumberhash
                # (Hashing part of phone number to avoid overly long filenames and ensure some uniqueness)
                date_str_for_file = current_date_dt.strftime("%Y%m%d")
                phone_hash_suffix = str(hash(phone_number_e164))[-6:] # Last 6 chars of hash
                audio_filename_base = f"{farmer_name.replace(' ', '_')}_{date_str_for_file}_{advisory_crop_name}_{phone_hash_suffix}"
                
                voice_message_path = generate_audio_message_gtts(
                    sms_text,
                    preferred_language, # Use farmer's preferred language
                    audio_filename_base
                )

                output_payload = {
                    "farmer_name": farmer_name,
                    "phone_number": phone_number_e164,
                    "network_operator": network_operator,
                    "preferred_language": preferred_language,
                    "sms_text": sms_text,
                    "voice_message_path": voice_message_path if voice_message_path else "GENERATION_FAILED"
                }
                
                final_output_list.append(output_payload)
                print(f"    Data package prepared for {farmer_name}.")
                # print(f"     Payload: {json.dumps(output_payload, indent=2)}") # Optional: print individual payload

    except Exception as e:
        print(f"An critical error occurred in main_processing_logic: {e}")
    finally:
        if pxs_driver:
            print("Closing PXS WebDriver.")
            pxs_driver.quit()

    print("\n--- Main Processing Complete ---")
    if final_output_list:
        print(f"Generated {len(final_output_list)} message packages.")
        # Save the entire list of JSON objects to a file or print
        output_json_filename = f"farmer_messages_output_{current_date_dt.strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(output_json_filename, 'w') as f:
                json.dump(final_output_list, f, indent=2)
            print(f"Full output saved to: {output_json_filename}")
            # print("\nFinal Output List (JSON):")
            # print(json.dumps(final_output_list, indent=2)) # Print to console if file save fails
        except IOError as e:
            print(f"Error saving output JSON to file: {e}")
            # print("\nFinal Output List (JSON):")
            # print(json.dumps(final_output_list, indent=2)) # Print to console if file save fails
    else:
        print("No message packages were generated.")

    if pxs_error_log:
        print("\n--- PXS Lookup Error Log ---")
        for log_entry in pxs_error_log:
            print(log_entry)


if __name__ == "__main__":
    # Ensure all necessary functions are defined before this call
    main_processing_logic()

