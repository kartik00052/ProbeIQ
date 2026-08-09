import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id. Never called with a stored hash."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against an Argon2 hash.

    Returns False (never raises) for mismatches, corrupted hashes, or malformed
    input so callers cannot distinguish those cases.
    """
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def generate_session_token() -> str:
    """Cryptographically random opaque session token (URL-safe)."""
    return secrets.token_urlsafe(48)
