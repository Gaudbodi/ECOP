from pymongo import MongoClient
from datetime import datetime

# --- Configuration ---
# IMPORTANT: Be cautious about hardcoding URIs with credentials in scripts,
# especially if sharing or committing to version control.
# Consider environment variables or a separate config file.
MONGO_URI = "mongodb+srv://francisyiryel:gfc3C4OizIvQr6mR@cluster0.pcd3g.mongodb.net/new_numbering?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "fsrp_aggregator"
ADVISORY_COLLECTION = "crop_advisories"
# FARMER_COLLECTION = "farmers" # Not used in this specific script, can be removed for clarity here

def get_db_connection():
    """Establishes connection to MongoDB."""
    # It's good practice to handle potential connection errors here
    try:
        client = MongoClient(MONGO_URI)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster') # Verifies connection
        print("MongoDB connection successful.")
        db = client[DB_NAME]
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        # Depending on the use case, you might want to exit or raise the exception
        return None


# connect to crop_advisories collection and convert all string date fields to datetime objects
def convert_string_dates_to_datetime(): # Renamed for clarity
    db = get_db_connection()
    if db is None:
        return # Exit if DB connection failed

    advisories_collection = db[ADVISORY_COLLECTION]
    documents_processed = 0
    conversions_done = 0
    conversion_failures = 0

    print(f"\nStarting date conversion for collection: {ADVISORY_COLLECTION}")

    # Using a try-except block for the overall database operation
    try:
        for doc in advisories_collection.find():
            documents_processed += 1
            update_payload = {} # To store fields that need to be updated for this document

            # Check if 'advisory' key exists and is a dictionary
            if "advisory" not in doc or not isinstance(doc["advisory"], dict):
                print(f"Skipping document ID {doc['_id']}: 'advisory' field missing or not a dictionary.")
                continue

            nested_advisory_obj = doc["advisory"]

            for key, value in nested_advisory_obj.items():
                # Ensure the field is one of the date fields and is a string
                if key in ["start_date", "end_date"] and isinstance(value, str):
                    try:
                        # Attempt to parse the string value to a datetime object
                        # datetime.fromisoformat() expects "YYYY-MM-DDTHH:MM:SS" or "YYYY-MM-DD"
                        # If your dates are just "YYYY-MM-DD", this is fine.
                        # If they have other formats, you might need datetime.strptime(value, "your_format_here")
                        datetime_obj = datetime.fromisoformat(value)
                        
                        # Prepare the field for update using the correct dot notation for nested fields
                        update_payload[f"advisory.{key}"] = datetime_obj
                        
                    except ValueError:
                        print(f"Failed to convert date string '{value}' for key '{key}' in document ID {doc['_id']}. It might not be in ISO format.")
                        conversion_failures += 1
                    except Exception as e:
                        print(f"An unexpected error occurred converting date for key '{key}' in document ID {doc['_id']}: {e}")
                        conversion_failures += 1
            
            # If there are any fields to update in this document
            if update_payload:
                try:
                    result = advisories_collection.update_one(
                        {"_id": doc["_id"]}, # Filter by document ID
                        {"$set": update_payload} # Set the new datetime values
                    )
                    if result.modified_count > 0:
                        print(f"Successfully converted date(s) for document ID {doc['_id']}. Fields updated: {list(update_payload.keys())}")
                        conversions_done +=1
                    elif result.matched_count == 1 and result.modified_count == 0:
                        print(f"Document ID {doc['_id']} matched but no changes made (data might be same or already converted).")
                    else:
                        print(f"Warning: Document ID {doc['_id']} matched, but update reported no modification. Check data.")

                except Exception as e:
                    print(f"Error updating document ID {doc['_id']} in MongoDB: {e}")
                    conversion_failures += 1
        
        print("\n--- Conversion Summary ---")
        print(f"Total documents scanned: {documents_processed}")
        print(f"Documents with successful date conversions: {conversions_done}")
        print(f"Date conversion failures/errors: {conversion_failures}")

    except Exception as e:
        print(f"An error occurred during the find operation: {e}")


if __name__ == "__main__":
    # Your original function name was convert_timestamps_to_datetime,
    # but the code converts string dates to datetime objects.
    # If you were converting Unix timestamps (integers/floats) to datetimes,
    # datetime.fromtimestamp() would be used.
    # If you are converting strings like "2025-05-10", then "string dates" is more accurate.
    convert_string_dates_to_datetime()