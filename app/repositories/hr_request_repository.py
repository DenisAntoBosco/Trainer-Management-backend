from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from uuid import UUID
from ..models import HRRequest
from ..schemas import HRRequestCreate, HRRequestUpdate

class HRRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[HRRequest]:
        from sqlalchemy.orm import selectinload
        from ..models import User
        
        query = select(HRRequest).options(selectinload(HRRequest.creator))
        
        if status:
            query = query.where(HRRequest.status == status)
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, hr_request_data: HRRequestCreate, created_by: UUID) -> HRRequest:
        hr_request = HRRequest(**hr_request_data.model_dump(), created_by=created_by, status="pending")
        self.db.add(hr_request)
        await self.db.commit()
        await self.db.refresh(hr_request)
        return hr_request

    async def update(self, request_id: UUID, hr_request_data: HRRequestUpdate) -> Optional[HRRequest]:
        from sqlalchemy.orm import selectinload
        
        update_data = hr_request_data.model_dump(exclude_unset=True)
        if update_data:
            await self.db.execute(
                update(HRRequest).where(HRRequest.id == request_id).values(**update_data)
            )
            await self.db.commit()
        
        result = await self.db.execute(
            select(HRRequest).options(selectinload(HRRequest.creator)).where(HRRequest.id == request_id)
        )
        return result.scalar_one_or_none()