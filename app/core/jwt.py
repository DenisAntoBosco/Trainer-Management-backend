from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

# Use hardcoded SECRET_KEY to ensure consistency
SECRET_KEY = "sk_prod_trainer_mgmt_2024_secure_key_32_chars_min"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    from .logging_config import logger
    logger.info(f"🎫 Creating access token with SECRET_KEY: {SECRET_KEY[:10]}...")
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    try:
        from .logging_config import logger
        logger.info(f"🔍 Verifying token with SECRET_KEY: {SECRET_KEY[:10]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"✅ Token verification successful: {payload.get('user_id')}")
        return payload
    except JWTError as e:
        from .logging_config import logger
        logger.error(f"❌ JWT Error: {str(e)}")
        return None
