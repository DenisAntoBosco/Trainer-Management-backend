from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date
from ..core.database import get_db
from ..core.auth import get_current_user
from ..services.attendance_service import AttendanceService
from ..schemas import AttendanceResponse, AttendanceCreate, AttendanceUpdate

router = APIRouter(prefix="/attendance", tags=["Attendance"])

@router.get("/", response_model=List[AttendanceResponse])
async def get_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    trainer_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    attendance_service = AttendanceService(db)
    return await attendance_service.get_attendance_records(skip, limit, trainer_id, date_from, date_to)

@router.post("/", response_model=AttendanceResponse)
async def create_attendance(
    attendance_data: AttendanceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    attendance_service = AttendanceService(db)
    return await attendance_service.create_attendance(
        attendance_data, 
        current_user["user_id"], 
        current_user.get("name", "Unknown")
    )

@router.put("/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance(
    attendance_id: UUID,
    attendance_data: AttendanceUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    attendance_service = AttendanceService(db)
    record = await attendance_service.update_attendance(attendance_id, attendance_data)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record

@router.post("/punch-out", response_model=AttendanceResponse)
async def punch_out(
    attendance_id: UUID,
    completion_notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    attendance_service = AttendanceService(db)
    record = await attendance_service.punch_out(attendance_id, completion_notes)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record