from smartystreets_python_sdk import StaticCredentials, ClientBuilder
from smartystreets_python_sdk.us_street import Lookup as StreetLookup
from app.core.config import settings
from redis.asyncio import Redis
from datetime import datetime, timezone
from smartystreets_python_sdk.exceptions import SmartyException
from app.core.exceptions import DailyQuotaExceededError, AddressProviderError, ProviderTimeoutError
from app.interfaces.validator import AddressValidator
from app.schemas import StandardizedAddress
import usaddress
import asyncio
import logging

logger = logging.getLogger(__name__)

class SmartyValidator(AddressValidator):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def validate(self, address_raw: str) -> StandardizedAddress | None:
        # 1. Quota Check
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        quota_key = f"smarty_quota:{today}"
        
        count = await self.redis.incr(quota_key)
        if count == 1:
            await self.redis.expire(quota_key, 86400)
            
        if count > settings.SMARTY_DAILY_LIMIT:
            await self.redis.decr(quota_key)
            raise DailyQuotaExceededError("Daily validation quota exceeded.")

        auth_id = settings.SMARTY_AUTH_ID
        auth_token = settings.SMARTY_AUTH_TOKEN
        
        if not auth_id or not auth_token:
            logger.warning("Smarty credentials missing.")
            # Should probably raise AddressProviderError if critical?
            # Existing logic just passed. Assuming it fails later or returns None.
            pass

        credentials = StaticCredentials(auth_id, auth_token)
        client = ClientBuilder(credentials).build_us_street_api_client()

        lookup = StreetLookup()
        
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
                elif label != 'CountryName': 
                    street_parts.append(val)

            lookup.street = " ".join(street_parts).strip() if street_parts else address_raw
            lookup.city = " ".join(city_parts).strip()
            lookup.state = " ".join(state_parts).strip()
            lookup.zipcode = " ".join(zip_parts).strip()
            
        except Exception as e:
            logger.warning("Error parsing address locally: %s", e, exc_info=True)
            lookup.street = address_raw

        lookup.candidates = 1
        
        logger.info("Calling Smarty API for address: %s", address_raw)
        try:
            # Wrap with timeout
            await asyncio.wait_for(
                asyncio.to_thread(client.send_lookup, lookup),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("Provider timed out")
            raise ProviderTimeoutError("Smarty API timed out")
        except SmartyException as e:
            logger.error("Smarty SDK Error: %s", e, exc_info=True)
            raise AddressProviderError(f"Smarty API Error: {str(e)}")
        except Exception as e:
            # General exception during call
            logger.error("Error calling Smarty: %s", e, exc_info=True)
            raise AddressProviderError("Unknown Provider Error")

        if lookup.result:
            candidate = lookup.result[0]
            is_corrected = candidate.analysis.dpv_match_code == "Y" and \
                candidate.delivery_line_1.lower() != address_raw.lower()
            logger.info("Address corrected: %s", is_corrected)
            
            return StandardizedAddress(
                street=candidate.delivery_line_1,
                city=candidate.components.city_name,
                state=candidate.components.state_abbreviation,
                zip_code=candidate.components.zipcode + "-" + candidate.components.plus4_code
            )
        return None

# For backward compatibility / easier mocking in tests that import 'validate_address'
async def validate_address(address_raw: str, redis: Redis):
    validator = SmartyValidator(redis)
    return await validator.validate(address_raw)
        