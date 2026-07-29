from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.orm import selectinload
from typing import Optional
from uuid import UUID
from ..models import Engagement, Batch, Trainer
from ..schemas import EngagementCreate

class EngagementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, project_id: UUID, engagement_data: EngagementCreate) -> Engagement:
        engagement = Engagement(**engagement_data.model_dump(), project_id=project_id, status="upcoming")
        self.db.add(engagement)
        await self.db.flush()
        
        # Find available trainers for this domain
        available_trainers = await self._get_available_trainers(engagement_data.domain)
        
        # Auto-generate batches with smart distribution
        total = engagement_data.total_students
        per_batch = engagement_data.students_per_batch
        
        # Calculate base batches and remainder
        base_batches = total // per_batch
        remainder = total % per_batch
        
        # If remainder is less than 50% of batch size, distribute among existing batches
        # Otherwise create a new batch
        threshold = per_batch * 0.5
        if remainder > 0 and remainder < threshold and base_batches > 0:
            # Distribute remainder among existing batches
            batch_count = base_batches
            extra_per_batch = remainder // base_batches
            extra_remainder = remainder % base_batches
        else:
            # Create separate batch for remainder
            batch_count = base_batches + (1 if remainder > 0 else 0)
            extra_per_batch = 0
            extra_remainder = 0
        
        for i in range(batch_count):
            # Calculate students for this batch
            if i < base_batches:
                batch_students = per_batch + extra_per_batch
                # Add one more student to first few batches if there's still remainder
                if i < extra_remainder:
                    batch_students += 1
            else:
                # Last batch gets the remainder
                batch_students = remainder
            
            # Auto-assign trainer if available WITHOUT conflicts
            trainer_id = None
            status = "pending"
            
            for trainer in available_trainers:
                # Check if trainer has conflicts with this batch's dates
                has_conflict = await self._check_trainer_conflict(
                    trainer.id, 
                    engagement_data.start_date, 
                    engagement_data.end_date
                )
                
                if not has_conflict:
                    trainer_id = trainer.id
                    status = "awaiting_confirmation"
                    # Update trainer
                    new_batches = trainer.current_batches + 1
                    new_status = "fully_allocated" if new_batches >= trainer.max_batches else "partially_allocated"
                    await self.db.execute(
                        text("UPDATE trainers SET current_batches = :batches, status = :status WHERE id = :id"),
                        {"batches": new_batches, "status": new_status, "id": str(trainer_id)}
                    )
                    # Remove this trainer from available list
                    available_trainers.remove(trainer)
                    break
            
            batch = Batch(
                engagement_id=engagement.id,
                batch_number=i + 1,
                students=batch_students,
                start_date=engagement_data.start_date,
                end_date=engagement_data.end_date,
                status=status,
                trainer_id=trainer_id
            )
            self.db.add(batch)
        
        await self.db.commit()
        await self.db.refresh(engagement, ['batches'])
        return engagement
    
    async def _get_available_trainers(self, domain: str):
        """Get available trainers matching the domain expertise, prioritizing those without conflicts"""
        result = await self.db.execute(
            select(Trainer).where(
                Trainer.current_batches < Trainer.max_batches
            ).order_by(Trainer.current_batches)
        )
        trainers = result.scalars().all()
        
        # Filter by domain expertise
        matching_trainers = [
            trainer for trainer in trainers
            if trainer.expertise and any(
                domain.lower() in exp.lower() or exp.lower() in domain.lower()
                for exp in trainer.expertise
            )
        ]
        
        return matching_trainers
    
    async def _check_trainer_conflict(self, trainer_id: UUID, start_date, end_date) -> bool:
        """Check if trainer has conflicting batch assignments"""
        result = await self.db.execute(
            text("""
                SELECT COUNT(*) FROM batches
                WHERE trainer_id = :trainer_id
                AND (
                    (start_date <= :end_date AND end_date >= :start_date)
                )
            """),
            {
                'trainer_id': trainer_id,
                'start_date': start_date,
                'end_date': end_date
            }
        )
        count = result.scalar()
        return count > 0

    async def get_by_id(self, engagement_id: UUID) -> Optional[Engagement]:
        result = await self.db.execute(
            select(Engagement)
            .options(selectinload(Engagement.batches))
            .where(Engagement.id == engagement_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_batches(self, engagement_id: UUID) -> Optional[Engagement]:
        result = await self.db.execute(
            select(Engagement)
            .options(selectinload(Engagement.batches))
            .where(Engagement.id == engagement_id)
        )
        return result.scalar_one_or_none()
    
    async def delete(self, engagement_id: UUID) -> bool:
        # Delete all batches first
        await self.db.execute(delete(Batch).where(Batch.engagement_id == engagement_id))
        # Then delete the engagement
        result = await self.db.execute(delete(Engagement).where(Engagement.id == engagement_id))
        await self.db.commit()
        return result.rowcount > 0

class BatchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, batch_id: UUID) -> Optional[Batch]:
        result = await self.db.execute(select(Batch).where(Batch.id == batch_id))
        return result.scalar_one_or_none()

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