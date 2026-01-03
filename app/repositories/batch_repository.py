from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_
from typing import Optional, List
from uuid import UUID
from datetime import date
from ..models import Batch

class BatchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, batch_id: UUID) -> Optional[Batch]:
        result = await self.db.execute(select(Batch).where(Batch.id == batch_id))
        return result.scalar_one_or_none()

    async def get_trainer_batches_in_range(self, trainer_id: UUID, start_date: date, end_date: date) -> List[Batch]:
        result = await self.db.execute(
            select(Batch).where(
                and_(
                    Batch.trainer_id == trainer_id,
                    Batch.status.in_(["confirmed", "awaiting_confirmation"]),
                    Batch.start_date <= end_date,
                    Batch.end_date >= start_date
                )
            )
        )
        return result.scalars().all()

    async def allocate_trainer(self, batch_id: UUID, trainer_id: UUID) -> Optional[Batch]:
        await self.db.execute(
            update(Batch).where(Batch.id == batch_id).values(
                trainer_id=trainer_id,
                status="awaiting_confirmation"
            )
        )
        await self.db.commit()
        return await self.get_by_id(batch_id)

    async def confirm_allocation(self, batch_id: UUID, confirmed_by: UUID) -> Optional[Batch]:
        await self.db.execute(
            update(Batch).where(Batch.id == batch_id).values(
                status="confirmed",
                confirmed_by=confirmed_by,
                confirmed_at=func.now()
            )
        )
        await self.db.commit()
        return await self.get_by_id(batch_id)