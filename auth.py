from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import logging

logger = logging.getLogger(__name__)
bearer = HTTPBearer()

# Validate admin key exists on module load (CRITICAL: Prevent bypassing auth if env var missing)
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")
if not ADMIN_API_KEY:
    raise RuntimeError(
        "CRITICAL: ADMIN_API_KEY environment variable is required for production. "
        "Set it in your .env file or deployment secrets. "
        "Without this, the admin API will be publicly accessible!"
    )

def verify_admin(creds: HTTPAuthorizationCredentials = Security(bearer)):
    """
    Verify admin bearer token against ADMIN_API_KEY from environment.
    Raises HTTPException with 403 if token is invalid.
    """
    if creds.credentials != ADMIN_API_KEY:
        logger.warning(f"Unauthorized admin access attempt from token: {creds.credentials[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired admin token"
        )
    return creds.credentials
