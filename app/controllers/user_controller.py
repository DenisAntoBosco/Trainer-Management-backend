from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from ..core.database import get_db
from ..core.auth import get_current_user
from ..services.user_service import UserService
from ..schemas import UserResponse, UserCreate
from ..core.response import APIResponse
from ..core.error_logger import ErrorLogger
from ..core.logging_config import logger
import traceback

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"👤 GET /users/me called - user_id: {current_user.get('user_id')}, role: {current_user.get('role')}")
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(UUID(current_user["user_id"]))
        if not user:
            logger.warning(f"User not found: {current_user['user_id']}")
            return APIResponse.error("User not found", 404)
        logger.info(f"✅ Successfully fetched user: {user.email} (role: {current_user.get('role')})")
        return APIResponse.success(user)
    except Exception as e:
        logger.error(f"❌ Error in get_current_user_profile: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_id = await ErrorLogger.log_error(e, "user_controller", "get_current_user_profile")
        return APIResponse.error("Failed to fetch user profile", 500, error_id)

@router.get("/")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"📊 GET /users called - skip: {skip}, limit: {limit}")
    try:
        user_service = UserService(db)
        users = await user_service.get_users(skip, limit)
        logger.info(f"✅ Successfully fetched {len(users) if users else 0} users")
        return APIResponse.success(users)
    except Exception as e:
        logger.error(f"❌ Error in get_users: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_id = await ErrorLogger.log_error(e, "user_controller", "get_users")
        return APIResponse.error("Failed to fetch users", 500, error_id)

@router.post("/")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"👥 POST /users called - creating user: {user_data.email}")
    try:
        user_service = UserService(db)
        new_user = await user_service.create_user(user_data)
        logger.info(f"✅ Successfully created user: {new_user.email}")
        return APIResponse.success(new_user, 201)
    except Exception as e:
        logger.error(f"❌ Error in create_user: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_id = await ErrorLogger.log_error(e, "user_controller", "create_user")
        return APIResponse.error(f"Failed to create user: {str(e)}", 400, error_id)

@router.get("/{user_id}")
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(f"👤 GET /users/{user_id} called")
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            logger.warning(f"User not found: {user_id}")
            return APIResponse.error("User not found", 404)
        logger.info(f"✅ Successfully fetched user: {user.email}")
        return APIResponse.success(user)
    except Exception as e:
        logger.error(f"❌ Error in get_user: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_id = await ErrorLogger.log_error(e, "user_controller", "get_user")
        return APIResponse.error("Failed to fetch user", 500, error_id)

@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"🗑️ DELETE /users/{user_id} called")
    try:
        user_service = UserService(db)
        success = await user_service.delete_user(user_id)
        if not success:
            logger.warning(f"User not found for deletion: {user_id}")
            return APIResponse.error("User not found", 404)
        logger.info(f"✅ Successfully deleted user: {user_id}")
        return APIResponse.success({"message": "User deleted successfully"})
    except Exception as e:
        logger.error(f"❌ Error in delete_user: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_id = await ErrorLogger.log_error(e, "user_controller", "delete_user")
        return APIResponse.error("Failed to delete user", 500, error_id)