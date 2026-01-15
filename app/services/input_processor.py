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
    FIVE_DIGIT_PATTERN = re.compile(r'\b(\d{5})\b')
    ANY_DIGIT_PATTERN = re.compile(r'\d+')
    
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

        # Check for zip code in any position (Structural Correction)
        matches = list(self.FIVE_DIGIT_PATTERN.finditer(sanitized))
        candidate_to_move = None
        
        # Check if there is already a candidate at the end
        has_zip_at_end = False
        if matches and matches[-1].end() == len(sanitized):
            has_zip_at_end = True

        for m in matches:
            val = m.group(1)
            
            # Check if it is already at the end
            if m.end() == len(sanitized):
                continue

            # Check logic for candidates
            should_move = False
            
            if val.startswith('0'):
                # Priority 1: Starts with 0 (and not at end) -> Zip. Always move.
                should_move = True
            elif m.start() == 0:
                # Priority 2: At start.
                # If we already have a zip at the end, do NOT move this (assume it's house number)
                if has_zip_at_end:
                    should_move = False
                else:
                    # Move ONLY if other digits exist in the rest of the string
                    rest_of_string = sanitized[m.end():]
                    if self.ANY_DIGIT_PATTERN.search(rest_of_string):
                        should_move = True
            else:
                # Priority 3: Middle. Assume Zip.
                should_move = True
            
            if should_move:
                candidate_to_move = m
                break # Move the first valid candidate we find

        if candidate_to_move:
            val = candidate_to_move.group(1)
            start, end = candidate_to_move.span()
            
            prefix = sanitized[:start].strip()
            suffix = sanitized[end:].strip()
            
            # Reconstruct string with zip at the end
            # Handle cases where prefix or suffix might be empty
            parts = [p for p in [prefix, suffix] if p]
            sanitized = " ".join(parts) + f" {val}"

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
