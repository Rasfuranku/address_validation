import hashlib
import secrets

def hash_key(key: str) -> str:
    """Returns the SHA-256 hash of the given key."""
    return hashlib.sha256(key.encode()).hexdigest()

def generate_key(prefix: str = "addr_vk_") -> tuple[str, str]:
    """
    Generates a secure random API key and its hash.
    Returns: (raw_key, key_hash)
    """
    # 32 bytes of randomness
    token = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{token}"
    return raw_key, hash_key(raw_key)
