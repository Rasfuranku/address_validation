from smartystreets_python_sdk import StaticCredentials, ClientBuilder
from smartystreets_python_sdk.us_street import Lookup as StreetLookup
from app.core.config import settings

def validate_address(address_raw: str):
    auth_id = settings.SMARTY_AUTH_ID
    auth_token = settings.SMARTY_AUTH_TOKEN
    
    if not auth_id or not auth_token:
        # Handle missing credentials gracefully, or let it fail if critical
        pass

    credentials = StaticCredentials(auth_id, auth_token)
    client = ClientBuilder(credentials).build_us_street_api_client()
    
    lookup = StreetLookup()
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
        return candidate
    return None