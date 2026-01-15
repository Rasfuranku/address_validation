from smartystreets_python_sdk import StaticCredentials, ClientBuilder
from smartystreets_python_sdk.us_street import Lookup as StreetLookup
from app.core.config import settings
import usaddress

def validate_address(address_raw: str):
    auth_id = settings.SMARTY_AUTH_ID
    auth_token = settings.SMARTY_AUTH_TOKEN
    
    if not auth_id or not auth_token:
        # Handle missing credentials gracefully, or let it fail if critical
        pass

    credentials = StaticCredentials(auth_id, auth_token)
    client = ClientBuilder(credentials).build_us_street_api_client()


    
    lookup = StreetLookup()
    # lookup.match = "enhanced" # Optional, if using enhanced matching

    # Parse address using usaddress
    try:
        parsed_list = usaddress.parse(address_raw)
        street_parts = []
        city_parts = []
        state_parts = []
        zip_parts = []

        for val, label in parsed_list:
            if label == 'PlaceName':
                city_parts.append(val)
            elif label == 'StateName':
                state_parts.append(val)
            elif label == 'ZipCode':
                zip_parts.append(val)
            elif label != 'CountryName': # Ignore country if present, assume US
                street_parts.append(val)

        # Smarty works best if you give it what you have.
        # If we found components, use them. 
        # If street_parts is empty but we have raw text, fall back to raw text for street.
        lookup.street = " ".join(street_parts).strip() if street_parts else address_raw
        lookup.city = " ".join(city_parts).strip()
        lookup.state = " ".join(state_parts).strip()
        lookup.zipcode = " ".join(zip_parts).strip()
        
    except Exception as e:
        # Fallback on error
        print(f"Error parsing address locally: {e}")
        lookup.street = address_raw

    lookup.candidates = 1
    try:
        client.send_lookup(lookup)
    except Exception as e:
        # Log error
        print(f"Error calling Smarty: {e}")
        return None

    if lookup.result:
        candidate = lookup.result[0]
        # Return structured data or the candidate object
        is_corrected = candidate.analysis.dpv_match_code == "Y" and \
            candidate.delivery_line_1.lower() != address_raw.lower()
        print(f"Address corrected: {is_corrected}")
        candidate.is_corrected = is_corrected
        return candidate
    return None
        