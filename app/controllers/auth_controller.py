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
        return APIResponse.success(result)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "auth_controller", "login")
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return APIResponse.error("Login failed", 500, error_id)

@router.post("/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        auth_service = AuthService(db)
        refresh_token = request.headers.get("X-Refresh-Token")
        if not refresh_token:
            return APIResponse.error("Refresh token required", 400)
        
        result = await auth_service.refresh_access_token(refresh_token)
        if not result:
            return APIResponse.error("Invalid refresh token", 401)
        
        return APIResponse.success(result)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "auth_controller", "refresh_token")
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
        logger.info("User logged out")
        return APIResponse.success({"message": "Logged out successfully"})
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "auth_controller", "logout")
        return APIResponse.error("Logout failed", 500, error_id)