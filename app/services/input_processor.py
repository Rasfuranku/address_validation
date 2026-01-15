import re
import unicodedata
from pydantic import BaseModel

class ProcessingResult(BaseModel):
    is_valid: bool
    sanitized_input: str
    canonical_key: str | None = None
    error_message: str | None = None

class AddressInputProcessor:
    # Compile regex patterns once for performance
    SAFE_CHARS_PATTERN = re.compile(r'^[a-zA-Z0-9\s.,#-]*$')
    PUNCTUATION_PATTERN = re.compile(r'[.,#-]')
    WHITESPACE_PATTERN = re.compile(r'\s+')
    
    # Common US abbreviations map
    ABBREVIATIONS = {
        "st": "street",
        "ave": "avenue",
        "apt": "apartment",
        "rd": "road",
        "blvd": "boulevard",
        "ln": "lane",
        "dr": "drive",
        "ct": "court",
        "pl": "place",
        "sq": "square",
        "ste": "suite",
        "hwy": "highway",
        "pkwy": "parkway",
        "cir": "circle",
        "n": "north",
        "s": "south",
        "e": "east",
        "w": "west",
        "ne": "northeast",
        "nw": "northwest",
        "se": "southeast",
        "sw": "southwest",
    }

    def process(self, raw_input: str) -> ProcessingResult:
        # Step 1: Sanitize (Security)
        # Handle None input gracefully if needed, but type hint says str
        if raw_input is None:
             return ProcessingResult(is_valid=False, sanitized_input="", error_message="Input cannot be None")

        # NFKC Normalization (handles full-width chars etc)
        sanitized = unicodedata.normalize('NFKC', raw_input)
        
        # Strip invisible control characters (keep printable + basic whitespace)
        # Categories: C* (Control, Format, etc.)
        sanitized = "".join(ch for ch in sanitized if not unicodedata.category(ch).startswith("C"))
        
        # Trim excessive whitespace
        sanitized = sanitized.strip()

        # Step 2: Validate (Gatekeeping)
        if len(sanitized) < 5:
            return ProcessingResult(
                is_valid=False, 
                sanitized_input=sanitized, 
                error_message="Minimum length is 5 characters"
            )
            
        if len(sanitized) > 200:
            return ProcessingResult(
                is_valid=False, 
                sanitized_input=sanitized, 
                error_message="Maximum length is 200 characters"
            )

        if not self.SAFE_CHARS_PATTERN.match(sanitized):
            return ProcessingResult(
                is_valid=False, 
                sanitized_input=sanitized, 
                error_message="Input contains invalid characters"
            )

        if not any(char.isdigit() for char in sanitized):
            return ProcessingResult(
                is_valid=False, 
                sanitized_input=sanitized, 
                error_message="Address must contain at least one digit"
            )

        # Step 3: Normalize (Caching Efficiency)
        normalized = sanitized.lower()
        
        # Remove punctuation
        normalized = self.PUNCTUATION_PATTERN.sub('', normalized)
        
        # Collapse multiple spaces
        normalized = self.WHITESPACE_PATTERN.sub(' ', normalized).strip()
        
        # Expand abbreviations
        # Split by space to identify words
        words = normalized.split()
        expanded_words = [self.ABBREVIATIONS.get(w, w) for w in words]
        canonical_key = " ".join(expanded_words)

        return ProcessingResult(
            is_valid=True,
            sanitized_input=sanitized,
            canonical_key=canonical_key
        )
