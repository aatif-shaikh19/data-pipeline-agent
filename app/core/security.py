import hashlib
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings

security_scheme = HTTPBearer(auto_error=False)


def hash_token(token: str) -> str:
    """Hash a raw token using SHA-256 for secure comparison and storage."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def verify_bearer_token(raw_token: str, expected_hash: str) -> bool:
    """Verify raw token against stored SHA-256 hash using constant-time comparison."""
    if not raw_token or not expected_hash:
        return False
    computed_hash = hash_token(raw_token)
    return secrets.compare_digest(computed_hash, expected_hash)


async def validate_api_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> str:
    """FastAPI dependency to enforce Bearer token authentication in constant-time."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header or Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = credentials.credentials
    expected_hash = settings.API_BEARER_TOKEN_HASH

    is_valid = False
    if expected_hash and verify_bearer_token(raw_token, expected_hash):
        is_valid = True
    elif settings.API_BEARER_TOKEN and verify_bearer_token(raw_token, hash_token(settings.API_BEARER_TOKEN)):
        is_valid = True

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return hashed representation for safe audit logging
    return hash_token(raw_token)
