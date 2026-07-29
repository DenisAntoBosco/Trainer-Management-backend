from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date
from ..core.database import get_db
from ..services.attendance_service import AttendanceService
from ..schemas import AttendanceResponse, AttendanceCreate, AttendanceUpdate
from ..core.response import APIResponse
from ..core.error_logger import ErrorLogger
from ..core.logging_config import logger

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.get("/")
async def get_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    trainer_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
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
    
    logger.info(f"📊 GET /attendance called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        attendance_service = AttendanceService(db)
        attendance_records = await attendance_service.get_attendance_records(skip, limit, trainer_id, date_from, date_to)
        logger.info(f"✅ Successfully fetched {len(attendance_records) if attendance_records else 0} attendance records")
        return APIResponse.success(attendance_records)
    except Exception as e:
        logger.error(f"❌ Error in get_attendance: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "attendance_controller", "get_attendance")
        return APIResponse.error("Failed to fetch attendance records", 500, error_id)

@router.post("/")
async def create_attendance(
    attendance_data: AttendanceCreate,
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
    
    logger.info(f"🎯 POST /attendance called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        attendance_service = AttendanceService(db)
        attendance_record = await attendance_service.create_attendance(
            attendance_data, 
            session_user["user_id"], 
            session_user.get("name", session_user["email"])
        )
        logger.info(f"✅ Successfully created attendance record: {attendance_record.id}")
        return APIResponse.success(attendance_record, 201)
    except Exception as e:
        logger.error(f"❌ Error in create_attendance: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "attendance_controller", "create_attendance")
        return APIResponse.error("Failed to create attendance record", 500, error_id)

@router.put("/{attendance_id}")
async def update_attendance(
    attendance_id: UUID,
    attendance_data: AttendanceUpdate,
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
    
    logger.info(f"✏️ PUT /attendance/{attendance_id} called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        attendance_service = AttendanceService(db)
        attendance_record = await attendance_service.update_attendance(attendance_id, attendance_data)
        if not attendance_record:
            logger.warning(f"Attendance record not found: {attendance_id}")
            return APIResponse.error("Attendance record not found", 404)
        logger.info(f"✅ Successfully updated attendance record: {attendance_id}")
        return APIResponse.success(attendance_record)
    except Exception as e:
        logger.error(f"❌ Error in update_attendance: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "attendance_controller", "update_attendance")
        return APIResponse.error("Failed to update attendance record", 500, error_id)

@router.post("/punch-out")
async def punch_out(
    attendance_id: UUID,
    completion_notes: Optional[str] = None,
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
    
    logger.info(f"🕒 POST /attendance/punch-out called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        attendance_service = AttendanceService(db)
        attendance_record = await attendance_service.punch_out(attendance_id, completion_notes)
        if not attendance_record:
            logger.warning(f"Attendance record not found: {attendance_id}")
            return APIResponse.error("Attendance record not found", 404)
        logger.info(f"✅ Successfully punched out attendance record: {attendance_id}")
        return APIResponse.success(attendance_record)
    except Exception as e:
        logger.error(f"❌ Error in punch_out: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "attendance_controller", "punch_out")
        return APIResponse.error("Failed to punch out", 500, error_id)