from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..services.auth_service import AuthService
from ..schemas import LoginRequest, SignupRequest
from ..core.response import APIResponse
from ..core.error_logger import ErrorLogger
from ..core.rate_limiter import limiter
from ..core.logging_config import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        auth_service = AuthService(db)
        result = await auth_service.authenticate_user(login_data.email, login_data.password)
        if not result:
            logger.warning(f"Failed login attempt for: {login_data.email}")
            return APIResponse.error("Invalid credentials", 401)
        
        logger.info(f"Successful login: {login_data.email}")
        logger.info(f"🎫 Login response includes: access_token={bool(result.get('access_token'))}, refresh_token={bool(result.get('refresh_token'))}")
        
        # Store user session for mock authentication
        from ..core.mock_session import set_current_user
        role = user.roles[0].role.value if user.roles else "admin"
        set_current_user(str(user.id), user.email, role)
        logger.info(f"💾 Mock session stored: {user.email} as {role}")
        
        return APIResponse.success(result)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "auth_controller", "login")
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return APIResponse.error("Login failed", 500, error_id)

@router.post("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        auth_service = AuthService(db)
        # Try standard header first, then custom header
        refresh_token = request.headers.get("X-Refresh-Token") or request.headers.get("x-refresh-token") or request.headers.get("X-Refresh")
        logger.info(f"🔄 Refresh token attempt - token present: {refresh_token is not None}")
        
        if not refresh_token:
            logger.warning("❌ No refresh token provided in X-Refresh-Token, x-refresh-token, or X-Refresh header")
            return APIResponse.error("Refresh token required", 400)
        
        logger.info(f"🎫 Refresh token received (first 20 chars): {refresh_token[:20]}...")
        result = await auth_service.refresh_access_token(refresh_token)
        
        if not result:
            logger.warning("❌ Invalid or expired refresh token")
            return APIResponse.error("Invalid refresh token", 401)
        
        logger.info("✅ Token refresh successful")
        return APIResponse.success(result)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "auth_controller", "refresh_token")
        logger.error(f"❌ Token refresh error: {str(e)}")
        return APIResponse.error("Token refresh failed", 500, error_id)

@router.post("/change-password")
async def change_password(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        return APIResponse.error("Change password not implemented yet", 501)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "auth_controller", "change_password")
        return APIResponse.error("Password change failed", 500, error_id)

@router.post("/signup")
async def signup(signup_data: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        return APIResponse.error("Signup not implemented yet", 501)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "auth_controller", "signup")
        return APIResponse.error("Signup failed", 500, error_id)

@router.post("/logout")
async def logout():
    try:
        from ..core.mock_session import clear_session
        clear_session()
        logger.info("🚪 User logged out - session cleared")
        return APIResponse.success({"message": "Logged out successfully"})
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "auth_controller", "logout")
        return APIResponse.error("Logout failed", 500, error_id)