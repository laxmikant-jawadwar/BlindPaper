"""Password hashing and session tokens, using only the standard library."""

import base64
import hashlib
import hmac
import secrets

PBKDF2_ITERATIONS = 200_000
HASH_PREFIX = "pbkdf2_sha256"


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 with a random salt, stored as 'pbkdf2_sha256$iterations$salt$hash'."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{HASH_PREFIX}${PBKDF2_ITERATIONS}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        prefix, iterations, salt_b64, digest_b64 = stored_hash.split("$")
        if prefix != HASH_PREFIX:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Sessions are stored by the SHA-256 of their token, so a database leak exposes no usable tokens."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# Verified against when an email is unknown, so unknown and wrong-password logins take equally long
DUMMY_HASH = hash_password("not-a-real-password")
