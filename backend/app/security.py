"""
Security utilities.

Provides helpers for password hashing and verification,
secure code generation, and code hashing operations used
for authentication, email verification, and account
recovery workflows.
"""
import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.config import settings

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_code(code: str) -> str:
    return hmac.new(
        settings.session_secret.encode(), code.encode(), hashlib.sha256
    ).hexdigest()


def verify_code(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_code(code), code_hash)