from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from uuid import UUID
from datetime import date
from ..models import Attendance
from ..schemas import AttendanceCreate, AttendanceUpdate

class AttendanceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100, trainer_id: Optional[str] = None, date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[Attendance]:
        query = select(Attendance)
        
        if trainer_id:
            query = query.where(Attendance.trainer_id == trainer_id)
        if date_from:
            query = query.where(Attendance.date >= date_from)
        if date_to:
            query = query.where(Attendance.date <= date_to)
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, attendance_data: AttendanceCreate, trainer_id: str, trainer_name: str) -> Attendance:
        attendance = Attendance(
            **attendance_data.model_dump(),
            trainer_id=trainer_id,
            trainer_name=trainer_name,
            status="pending",
            punch_in=func.now()
        )
        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def update(self, attendance_id: UUID, attendance_data: AttendanceUpdate) -> Optional[Attendance]:
        update_data = attendance_data.model_dump(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(Attendance).where(Attendance.id == attendance_id).values(**update_data)
            )
            await self.db.commit()
        
        result = await self.db.execute(select(Attendance).where(Attendance.id == attendance_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, attendance_id: UUID) -> Optional[Attendance]:
        result = await self.db.execute(select(Attendance).where(Attendance.id == attendance_id))
        return result.scalar_one_or_none()