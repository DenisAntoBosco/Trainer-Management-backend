from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from ..repositories.user_repository import UserRepository
from ..schemas import UserResponse
from ..core.security import verify_password
from ..core.jwt import create_access_token, create_refresh_token, verify_token
from ..core.logging_config import logger

class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        user = await self.user_repo.get_by_email(email)
        logger.info(f"Auth attempt for: {email}")
        
        if not user:
            return None
        
        is_valid = verify_password(password, user.password_hash)
        
        if not is_valid:
            return None
        
        role = user.roles[0].role.value if user.roles else "admin"
        user_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": role
        }
        
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                avatar_url=user.avatar_url,
                role=role,
                created_at=user.created_at
            )
        }

    async def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        logger.info(f"🔄 Attempting to refresh token (first 20 chars): {refresh_token[:20]}...")
        payload = verify_token(refresh_token)
        
        if not payload:
            logger.warning("❌ Refresh token verification failed - invalid token")
            return None
            
        if payload.get("type") != "refresh":
            logger.warning(f"❌ Invalid token type: {payload.get('type')}, expected 'refresh'")
            return None
        
        logger.info(f"✅ Refresh token valid for user: {payload.get('user_id')}")
        user_data = {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "role": payload.get("role")
        }
        
        access_token = create_access_token(user_data)
        logger.info("✅ New access token created successfully")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }