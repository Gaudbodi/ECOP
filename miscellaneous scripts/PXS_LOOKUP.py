from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

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
        time.sleep(5) # Allow time for page to react to dropdown selection.
                      # Replace with WebDriverWait for a specific element if possible.

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
        
        # It's good practice to "reset" the state for the next search if the page
        # keeps old results visible. The current indication is that the results area
        # is dynamic. Clearing the input is handled at the start of the function.
        # If the entire table structure changes significantly or if old result rows persist
        # in a confusing way, we might need an additional step here to wait for the
        # "non-result" state before the next call, but your info suggests this is not needed.

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

# --- Example of how to use these functions (Main Orchestration Logic) ---
if __name__ == '__main__':
    # Replace with your actual credentials
    PXS_USERNAME = "fyiryel"  # Use your actual username
    PXS_PASSWORD = "NiggaTron38"  # Use your actual password

    # Sample farmer data (similar to what you'd fetch from MongoDB)
    dummy_farmers = [
        {"name": "Kwame Asante", "phone_number": "+233240000001"}, # Expected: MTN
        {"name": "Adwoa Mensah", "phone_number": "+233200000002"}, # Expected: Telecel (Vodafone)
        {"name": "Femi Adebayo", "phone_number": "+233550000003"}, # Expected: AT (AirtelTigo)
        {"name": "Invalid Number", "phone_number": "+233000000000"}, # Example of potentially invalid
        {"name": "Short Number", "phone_number": "02412345"}, # Example of bad format
    ]

    # Initialize WebDriver
    print("Initializing WebDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.implicitly_wait(5) # Implicit wait for general element presence

    network_operator_results = {}
    error_log = []

    try:
        if login_and_navigate_to_search(driver, PXS_USERNAME, PXS_PASSWORD, operator_to_select="MTN"):
            print("\n--- Starting Network Operator Checks ---")
            for farmer in dummy_farmers:
                farmer_name = farmer["name"]
                original_phone = farmer["phone_number"]
                
                print(f"\nProcessing farmer: {farmer_name}, Phone: {original_phone}")
                
                pxs_phone_format = convert_to_pxs_format(original_phone)
                
                if not pxs_phone_format:
                    print(f"  Could not convert phone number {original_phone} to PXS format. Skipping.")
                    error_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "phone_number": original_phone,
                        "error": "Format conversion failed"
                    })
                    network_operator_results[original_phone] = "Format Error"
                    continue

                print(f"  Converted to PXS format: {pxs_phone_format}")
                operator = get_network_operator_from_pxs(driver, pxs_phone_format)
                
                if operator:
                    print(f"  Retrieved Operator for {pxs_phone_format}: {operator}")
                    network_operator_results[original_phone] = operator
                else:
                    print(f"  Failed to retrieve operator for {pxs_phone_format}.")
                    error_log.append({
                        "timestamp": datetime.now().isoformat(), # Requires: from datetime import datetime
                        "phone_number": original_phone,
                        "pxs_format_attempted": pxs_phone_format,
                        "error": "Operator not found or PXS error"
                    })
                    network_operator_results[original_phone] = "Lookup Failed"
                
                # Add a small delay between requests if worried about overwhelming the server
                # time.sleep(1) # Optional: 1-second delay

        else:
            print("Failed to login or navigate to the search page. Aborting checks.")

    finally:
        print("\n--- Network Operator Check Summary ---")
        for phone, op in network_operator_results.items():
            print(f"Phone: {phone}, Detected Operator/Status: {op}")
        
        if error_log:
            print("\n--- Error Log ---")
            for log_entry in error_log:
                print(log_entry)
        
        print("\nClosing WebDriver.")
        driver.quit()