from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..core.database import get_db
from ..services.hr_request_service import HRRequestService
from ..schemas import HRRequestResponse, HRRequestCreate, HRRequestUpdate, HRRequestStatus
from ..core.response import APIResponse
from ..core.error_logger import ErrorLogger
from ..core.logging_config import logger

router = APIRouter(prefix="/hr-requests", tags=["HR Requests"])

@router.get("/")
async def get_hr_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[HRRequestStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"📊 GET /hr-requests called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        hr_service = HRRequestService(db)
        hr_requests = await hr_service.get_hr_requests(skip, limit, status)
        logger.info(f"✅ Successfully fetched {len(hr_requests) if hr_requests else 0} HR requests")
        return APIResponse.success(hr_requests)
    except Exception as e:
        logger.error(f"❌ Error in get_hr_requests: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "hr_request_controller", "get_hr_requests")
        return APIResponse.error("Failed to fetch HR requests", 500, error_id)

@router.post("/")
async def create_hr_request(
    hr_request_data: HRRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"🎯 POST /hr-requests called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        hr_service = HRRequestService(db)
        hr_request = await hr_service.create_hr_request(hr_request_data, UUID(session_user["user_id"]))
        logger.info(f"✅ Successfully created HR request: {hr_request.id}")
        return APIResponse.success(hr_request, 201)
    except Exception as e:
        logger.error(f"❌ Error in create_hr_request: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "hr_request_controller", "create_hr_request")
        return APIResponse.error("Failed to create HR request", 500, error_id)

@router.put("/{request_id}")
async def update_hr_request(
    request_id: UUID,
    hr_request_data: HRRequestUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"✏️ PUT /hr-requests/{request_id} called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        hr_service = HRRequestService(db)
        hr_request = await hr_service.update_hr_request(request_id, hr_request_data)
        if not hr_request:
            logger.warning(f"HR request not found: {request_id}")
            return APIResponse.error("HR request not found", 404)
        logger.info(f"✅ Successfully updated HR request: {request_id}")
        return APIResponse.success(hr_request)
    except Exception as e:
        logger.error(f"❌ Error in update_hr_request: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "hr_request_controller", "update_hr_request")
        return APIResponse.error("Failed to update HR request", 500, error_id)