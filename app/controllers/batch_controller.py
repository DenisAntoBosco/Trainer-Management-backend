from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..core.database import get_db
from ..services.batch_service import BatchService
from ..schemas import BatchResponse, BatchAllocation
from ..core.response import APIResponse
from ..core.error_logger import ErrorLogger
from ..core.logging_config import logger

router = APIRouter(prefix="/batches", tags=["Batches"])

@router.put("/{batch_id}/allocate")
async def allocate_trainer(
    batch_id: UUID,
    allocation_data: BatchAllocation,
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
    
    logger.info(f"🎯 PUT /batches/{batch_id}/allocate called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        batch_service = BatchService(db)
        batch = await batch_service.allocate_trainer(batch_id, allocation_data.trainer_id)
        if not batch:
            logger.warning(f"Batch not found: {batch_id}")
            return APIResponse.error("Batch not found", 404)
        logger.info(f"✅ Successfully allocated trainer to batch: {batch_id}")
        return APIResponse.success(batch)
    except Exception as e:
        logger.error(f"❌ Error in allocate_trainer: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "batch_controller", "allocate_trainer")
        return APIResponse.error("Failed to allocate trainer", 500, error_id)

@router.post("/{batch_id}/confirm")
async def confirm_allocation(
    batch_id: UUID,
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
    
    logger.info(f"✅ POST /batches/{batch_id}/confirm called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        batch_service = BatchService(db)
        batch = await batch_service.confirm_allocation(batch_id, UUID(session_user["user_id"]))
        if not batch:
            logger.warning(f"Batch not found: {batch_id}")
            return APIResponse.error("Batch not found", 404)
        logger.info(f"✅ Successfully confirmed batch allocation: {batch_id}")
        return APIResponse.success(batch)
    except Exception as e:
        logger.error(f"❌ Error in confirm_allocation: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "batch_controller", "confirm_allocation")
        return APIResponse.error("Failed to confirm allocation", 500, error_id)