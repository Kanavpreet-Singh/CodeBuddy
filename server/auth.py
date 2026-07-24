import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Verifies the short-lived HS256 token minted by the Next.js proxy and returns the user id."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    secret = os.environ["SERVICE_JWT_SECRET"]
    try:
        payload = jwt.decode(creds.credentials, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject")
    return user_id
