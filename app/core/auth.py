from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt import verify_token
from .logging_config import logger

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    logger.info(f"🔐 Authentication attempt - credentials present: {credentials is not None}")
    
    if not credentials:
        logger.warning("No authentication credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication credentials provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    logger.info(f"🎫 Token received (first 20 chars): {token[:20]}...")
    
    payload = verify_token(token)
    logger.info(f"🔍 Token verification result: {payload is not None}")
    
    if payload is None:
        logger.warning(f"Invalid token attempted - token: {token[:50]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"✅ User authenticated: {payload.get('user_id')}")
    return payload