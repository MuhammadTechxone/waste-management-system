from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

bearer = HTTPBearer()

def verify_admin(creds: HTTPAuthorizationCredentials = Security(bearer)):
    # Admin key must be stored in environment variables (e.g., Hugging Face Spaces Secrets)
    if creds.credentials != os.environ.get("ADMIN_API_KEY"): # Use .get() without a default for production, or raise an error if not found
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")