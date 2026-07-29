from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, time
from ..repositories.attendance_repository import AttendanceRepository
from ..schemas import AttendanceResponse, AttendanceCreate, AttendanceUpdate, AttendanceStatus
from ..core.logging_config import logger

class AttendanceService:
    def __init__(self, db: AsyncSession):
        self.attendance_repo = AttendanceRepository(db)

    async def get_attendance_records(self, skip: int = 0, limit: int = 100, trainer_id: Optional[str] = None, date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[AttendanceResponse]:
        records = await self.attendance_repo.get_all(skip, limit, trainer_id, date_from, date_to)
        return [AttendanceResponse.model_validate(record) for record in records]

    async def create_attendance(self, attendance_data: AttendanceCreate, trainer_id: str, trainer_name: str) -> AttendanceResponse:
        # Check for existing attendance on same day
        today = date.today()
        existing = await self.attendance_repo.get_by_trainer_and_date(trainer_id, today)
        if existing:
            raise ValueError("Attendance already recorded for today")
        
        # Validate business hours (8 AM - 8 PM)
        current_time = datetime.now().time()
        if current_time < time(8, 0) or current_time > time(20, 0):
            logger.warning(f"Punch-in attempted outside business hours: {current_time}")
        
        record = await self.attendance_repo.create(attendance_data, trainer_id, trainer_name)
        logger.info(f"Attendance created for trainer {trainer_id}")
        return AttendanceResponse.model_validate(record)

    async def update_attendance(self, attendance_id: UUID, attendance_data: AttendanceUpdate) -> Optional[AttendanceResponse]:
        record = await self.attendance_repo.update(attendance_id, attendance_data)
        return AttendanceResponse.model_validate(record) if record else None

    async def punch_out(self, attendance_id: UUID, completion_notes: Optional[str] = None) -> Optional[AttendanceResponse]:
        # Get existing record
        record = await self.attendance_repo.get_by_id(attendance_id)
        if not record:
            raise ValueError("Attendance record not found")
        
        if not record.punch_in:
            raise ValueError("Cannot punch out without punch in")
        
        if record.punch_out:
            raise ValueError("Already punched out")
        
        # Validate punch out is after punch in
        punch_out_time = datetime.utcnow()
        if punch_out_time <= record.punch_in:
            raise ValueError("Punch out time must be after punch in time")
        
        update_data = AttendanceUpdate(
            status=AttendanceStatus.present,
            punch_out=punch_out_time,
            completion_notes=completion_notes
        )
        logger.info(f"Punch out recorded for attendance {attendance_id}")
        return await self.update_attendance(attendance_id, update_data)