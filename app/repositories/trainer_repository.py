from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from typing import List, Optional
from uuid import UUID
from datetime import date
from ..models import Trainer
from ..schemas import TrainerCreate, TrainerUpdate

class TrainerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100, status: Optional[str] = None, expertise: Optional[str] = None) -> List[Trainer]:
        query = select(Trainer)
        
        if status:
            query = query.where(Trainer.status == status)
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        trainers = result.scalars().all()
        
        # Filter by expertise in Python if specified
        if expertise:
            filtered_trainers = []
            for trainer in trainers:
                if trainer.expertise and any(
                    expertise.lower() in exp.lower() or exp.lower() in expertise.lower()
                    for exp in trainer.expertise
                ):
                    filtered_trainers.append(trainer)
            return filtered_trainers
            
        return trainers

    async def get_by_id(self, trainer_id: UUID) -> Optional[Trainer]:
        result = await self.db.execute(select(Trainer).where(Trainer.id == trainer_id))
        return result.scalar_one_or_none()

    async def get_trainer_by_email(self, email: str) -> Optional[Trainer]:
        result = await self.db.execute(select(Trainer).where(Trainer.email == email))
        return result.scalar_one_or_none()

    async def create_trainer(self, trainer_dict: dict) -> Trainer:
        from sqlalchemy import text
        
        # Use raw SQL with proper parameter placeholders
        query = text("""
            INSERT INTO trainers (id, user_id, name, email, phone, avatar, expertise, status, max_batches, 
                                current_batches, employment_type, experience_level, join_date)
            VALUES (gen_random_uuid(), :user_id, :name, :email, :phone, :avatar, :expertise, 
                    CAST(:status AS trainer_status), :max_batches, :current_batches, 
                    CAST(:employment_type AS employment_type), CAST(:experience_level AS experience_level), :join_date)
            RETURNING id
        """)
        
        result = await self.db.execute(query, trainer_dict)
        await self.db.commit()
        row = result.fetchone()
        
        return await self.get_by_id(row[0])

    async def update(self, trainer_id: UUID, trainer_data: TrainerUpdate) -> Optional[Trainer]:
        from sqlalchemy import text
        update_data = trainer_data.model_dump(exclude_unset=True)
        if update_data:
            # Build SET clause dynamically
            set_parts = []
            params = {'trainer_id': trainer_id}
            
            for key, value in update_data.items():
                if hasattr(value, 'value'):
                    value = value.value
                params[key] = value
                
                # Cast enum fields to their database types
                if key == 'employment_type':
                    set_parts.append(f"{key} = :{key}::employment_type")
                elif key == 'experience_level':
                    set_parts.append(f"{key} = :{key}::experience_level")
                else:
                    set_parts.append(f"{key} = :{key}")
            
            if set_parts:
                query = text(f"UPDATE trainers SET {', '.join(set_parts)} WHERE id = :trainer_id")
                await self.db.execute(query, params)
                await self.db.commit()
        
        return await self.get_by_id(trainer_id)

    async def delete(self, trainer_id: UUID) -> bool:
        result = await self.db.execute(delete(Trainer).where(Trainer.id == trainer_id))
        await self.db.commit()
        return result.rowcount > 0

    async def get_available_by_domain(self, domain: str, start_date: date, end_date: date) -> List[Trainer]:
        # Get all available trainers and filter in Python for better compatibility
        result = await self.db.execute(
            select(Trainer).where(
                and_(
                    Trainer.status.in_(["available", "partially_allocated"]),
                    Trainer.current_batches < Trainer.max_batches
                )
            )
        )
        trainers = result.scalars().all()
        
        # Filter by domain expertise in Python
        filtered_trainers = []
        for trainer in trainers:
            if trainer.expertise and any(
                domain.lower() in expertise.lower() or expertise.lower() in domain.lower()
                for expertise in trainer.expertise
            ):
                filtered_trainers.append(trainer)
        
        return filtered_trainers

    async def get_trainer_allocations(self, trainer_id: UUID):
        from sqlalchemy.orm import selectinload
        from ..models import Batch, Engagement, Project
        
        # Get all batches for this trainer (not just specific statuses)
        query = select(Batch).where(
            Batch.trainer_id == trainer_id
        ).options(
            selectinload(Batch.engagement).selectinload(Engagement.project)
        ).order_by(Batch.start_date)
        
        result = await self.db.execute(query)
        batches = result.scalars().all()
        
        print(f"Found {len(batches)} batches for trainer {trainer_id}")
        
        allocations = []
        for batch in batches:
            try:
                print(f"Processing batch {batch.id}, status: {batch.status}")
                allocations.append({
                    'batch_id': str(batch.id),
                    'batch_name': f"Batch #{batch.batch_number}",
                    'start_date': batch.start_date.isoformat() if batch.start_date else None,
                    'end_date': batch.end_date.isoformat() if batch.end_date else None,
                    'status': batch.status.value if hasattr(batch.status, 'value') else str(batch.status),
                    'project_name': batch.engagement.project.name if batch.engagement and batch.engagement.project else 'Unknown Project',
                    'engagement_name': batch.engagement.name if batch.engagement else 'Unknown Engagement',
                    'domain': batch.engagement.domain if batch.engagement else 'Unknown'
                })
            except Exception as e:
                print(f"Error processing batch {batch.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Returning {len(allocations)} allocations")
        return allocations