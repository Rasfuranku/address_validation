import usaddress
import re

def parse_with_leading_zip_handling(raw_input: str):
    # Regex to detect leading 5-digit zip followed by space
    # ^ = start of string, \b = word boundary
    leading_zip_pattern = r"^(\d{5})\s+(.*)"
    
    match = re.match(leading_zip_pattern, raw_input.strip())
    
    pre_extracted_zip = None
    clean_address = raw_input

    if match:
        # If found, extract zip and keep the rest of the address
        pre_extracted_zip = match.group(1)
        clean_address = match.group(2) # "130 jackson st"

    # Now parse the "clean" address (standard format)
    try:
        parsed_data, address_type = usaddress.tag(clean_address)
    except usaddress.RepeatedLabelError:
        # Fallback to parse if tag fails
        parsed_list = usaddress.parse(clean_address)
        parsed_data = {k: v for v, k in parsed_list}

    # Inject the pre-extracted zip back into the result
    if pre_extracted_zip:
        # Overwrite or add the ZipCode field
        parsed_data['ZipCode'] = pre_extracted_zip

    return parsed_data

# Test
print(parse_with_leading_zip_handling("07055 130 jackson st"))
# Output: OrderedDict([('AddressNumber', '130'), ('StreetName', 'jackson'), ('StreetNamePostType', 'st'), ('ZipCode', '07055')])