from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from datetime import datetime
from ..repositories.batch_repository import BatchRepository
from ..repositories.trainer_repository import TrainerRepository
from ..schemas import BatchResponse
from ..core.logging_config import logger

class BatchService:
    def __init__(self, db: AsyncSession):
        self.batch_repo = BatchRepository(db)
        self.trainer_repo = TrainerRepository(db)

    async def check_trainer_availability(self, trainer_id: UUID, start_date: datetime, end_date: datetime, allow_overlap: bool = False) -> tuple[bool, str]:
        trainer = await self.trainer_repo.get_by_id(trainer_id)
        if not trainer:
            return False, "Trainer not found"
        
        if trainer.status == "on_leave":
            return False, "Trainer is on leave"
        
        # Check for date overlaps
        overlapping_batches = await self.batch_repo.get_trainer_batches_in_range(trainer_id, start_date, end_date)
        if overlapping_batches and not allow_overlap:
            batch_names = ', '.join([b.name for b in overlapping_batches[:3]])
            return False, f"Trainer already allocated to: {batch_names}"
        
        if trainer.current_batches >= trainer.max_batches:
            return False, f"Trainer is fully allocated ({trainer.current_batches}/{trainer.max_batches} batches)"
        
        return True, "Trainer is available"

    async def allocate_trainer(self, batch_id: UUID, trainer_id: UUID) -> Optional[BatchResponse]:
        # Check trainer availability first
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            logger.error(f"Batch {batch_id} not found")
            return None
        
        available, message = await self.check_trainer_availability(trainer_id, batch.start_date, batch.end_date)
        if not available:
            logger.warning(f"Trainer allocation failed: {message}")
            raise ValueError(message)
        
        batch = await self.batch_repo.allocate_trainer(batch_id, trainer_id)
        logger.info(f"Trainer {trainer_id} allocated to batch {batch_id}")
        return BatchResponse.model_validate(batch) if batch else None

    async def confirm_allocation(self, batch_id: UUID, confirmed_by: UUID) -> Optional[BatchResponse]:
        batch = await self.batch_repo.confirm_allocation(batch_id, confirmed_by)
        logger.info(f"Batch {batch_id} allocation confirmed by {confirmed_by}")
        return BatchResponse.model_validate(batch) if batch else None