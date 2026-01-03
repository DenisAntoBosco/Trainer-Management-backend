from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date
from ..repositories.trainer_repository import TrainerRepository
from ..repositories.user_repository import UserRepository
from ..schemas import TrainerResponse, TrainerCreate, TrainerUpdate, AppRole
from ..core.security import get_password_hash

class TrainerService:
    def __init__(self, db: AsyncSession):
        self.trainer_repo = TrainerRepository(db)
        self.user_repo = UserRepository(db)

    async def get_trainers(self, skip: int = 0, limit: int = 100, status: Optional[str] = None, expertise: Optional[str] = None) -> List[TrainerResponse]:
        trainers = await self.trainer_repo.get_all(skip, limit, status, expertise)
        return [TrainerResponse.model_validate(trainer) for trainer in trainers]

    async def get_trainer_by_id(self, trainer_id: UUID) -> Optional[TrainerResponse]:
        trainer = await self.trainer_repo.get_by_id(trainer_id)
        return TrainerResponse.model_validate(trainer) if trainer else None

    async def create_trainer(self, trainer_data: TrainerCreate) -> TrainerResponse:
        print(f"\n=== CREATE TRAINER STARTED: {trainer_data.email} ===")
        # Convert TrainerCreate to dict for repository
        trainer_dict = {
            'user_id': None,
            'name': trainer_data.name,
            'email': trainer_data.email,
            'phone': trainer_data.phone,
            'avatar': trainer_data.avatar,
            'expertise': trainer_data.expertise,
            'status': 'available',
            'max_batches': trainer_data.max_batches,
            'current_batches': 0,
            'employment_type': trainer_data.employment_type.value if hasattr(trainer_data.employment_type, 'value') else trainer_data.employment_type,
            'experience_level': trainer_data.experience_level.value if hasattr(trainer_data.experience_level, 'value') else trainer_data.experience_level,
            'join_date': trainer_data.join_date
        }
        
        print(f"Creating trainer with expertise: {trainer_data.expertise}")
        trainer = await self.trainer_repo.create_trainer(trainer_dict)
        print(f"Trainer created with ID: {trainer.id}")
        
        # Create user account for trainer
        try:
            username = trainer_data.email.split('@')[0]
            password_hash = get_password_hash(username)
            user = await self.user_repo.create_user(
                name=trainer_data.name,
                email=trainer_data.email,
                password=password_hash,
                role=AppRole.trainer,
                avatar_url=trainer.avatar
            )
            print(f"User created successfully for trainer: {trainer_data.email}, user_id: {user.id}")
            
            # Update trainer with user_id
            from sqlalchemy import text
            await self.trainer_repo.db.execute(
                text("UPDATE trainers SET user_id = :user_id WHERE id = :trainer_id"),
                {'user_id': user.id, 'trainer_id': trainer.id}
            )
            await self.trainer_repo.db.commit()
            print(f"Trainer {trainer.id} linked to user {user.id}")
            
            # Refresh trainer object to get updated user_id
            trainer = await self.trainer_repo.get_by_id(trainer.id)
        except Exception as e:
            print(f"Failed to create user for trainer: {e}")
            import traceback
            traceback.print_exc()
        
        # Auto-assign trainer to pending batches from HR requests
        print(f"Starting auto-assignment for trainer {trainer.name}...")
        try:
            await self._auto_assign_to_hr_requests(trainer)
            print(f"Auto-assignment completed for trainer {trainer.name}")
        except Exception as e:
            print(f"Failed to auto-assign trainer to HR requests: {e}")
            import traceback
            traceback.print_exc()
        
        return TrainerResponse.model_validate(trainer)

    async def _auto_assign_to_hr_requests(self, trainer):
        """Auto-assign newly created trainer to pending batches from matching HR requests"""
        from ..repositories.hr_request_repository import HRRequestRepository
        from ..repositories.engagement_repository import EngagementRepository
        from sqlalchemy import text
        
        print(f"\n=== AUTO-ASSIGNMENT STARTED for {trainer.name} ===")
        print(f"Trainer expertise: {trainer.expertise}")
        
        hr_repo = HRRequestRepository(self.trainer_repo.db)
        engagement_repo = EngagementRepository(self.trainer_repo.db)
        
        # Get active HR requests
        hr_requests = await hr_repo.get_all()
        print(f"Found {len(hr_requests)} total HR requests")
        
        for hr_request in hr_requests:
            print(f"\nChecking HR request {hr_request.id}:")
            print(f"  - Status: {hr_request.status}")
            print(f"  - Domain: {hr_request.domain}")
            
            if hr_request.status == 'fulfilled':
                print(f"  -> SKIPPED: Already fulfilled")
                continue
            
            # Check if trainer expertise matches HR request domain
            domain_match = any(
                hr_request.domain.lower() in exp.lower() or exp.lower() in hr_request.domain.lower()
                for exp in trainer.expertise
            )
            
            print(f"  - Domain match: {domain_match}")
            
            if not domain_match:
                print(f"  -> SKIPPED: No domain match")
                continue
            
            print(f"  -> MATCH FOUND! Processing engagement {hr_request.engagement_id}")
            
            # Get engagement and its batches
            engagement = await engagement_repo.get_by_id(hr_request.engagement_id)
            if not engagement:
                print(f"  -> ERROR: Engagement not found")
                continue
            
            print(f"  - Engagement has {len(engagement.batches)} batches")
            assigned_count = 0
            
            # Find batches that need trainers (pending OR has conflicted trainer)
            for batch in engagement.batches:
                print(f"    Batch #{batch.batch_number}: status={batch.status}, trainer_id={batch.trainer_id}")
                
                # Skip confirmed batches
                if batch.status == 'confirmed':
                    print(f"      -> SKIPPED: Already confirmed")
                    continue
                
                # Check if batch needs a trainer
                needs_trainer = False
                
                if not batch.trainer_id:
                    # No trainer assigned
                    needs_trainer = True
                    print(f"      -> Needs trainer: No trainer assigned")
                elif batch.trainer_id:
                    # Check if current trainer has conflict
                    current_trainer_conflict = await self._check_trainer_conflict(
                        batch.trainer_id, batch.start_date, batch.end_date, batch.id
                    )
                    if current_trainer_conflict:
                        needs_trainer = True
                        print(f"      -> Needs trainer: Current trainer has conflict")
                
                if not needs_trainer:
                    print(f"      -> SKIPPED: Has trainer without conflicts")
                    continue
                
                # Check if new trainer has conflicts
                new_trainer_conflict = await self._check_trainer_conflict(
                    trainer.id, batch.start_date, batch.end_date, batch.id
                )
                
                if new_trainer_conflict:
                    print(f"      -> SKIPPED: New trainer also has conflict")
                    continue
                
                # Auto-assign trainer to batch
                print(f"      -> ASSIGNING trainer {trainer.id} to batch {batch.id}")
                await self.trainer_repo.db.execute(
                    text("""
                        UPDATE batches 
                        SET trainer_id = :trainer_id, status = 'awaiting_confirmation'
                        WHERE id = :batch_id
                    """),
                    {'trainer_id': trainer.id, 'batch_id': batch.id}
                )
                
                assigned_count += 1
                print(f"      -> SUCCESS: Assigned to batch #{batch.batch_number}")
                
                if assigned_count >= hr_request.trainers_needed:
                    print(f"      -> Reached required trainers count ({hr_request.trainers_needed})")
                    break
            
            # Mark HR request as fulfilled if we assigned trainers
            if assigned_count > 0:
                from ..schemas import HRRequestUpdate
                await hr_repo.update(hr_request.id, HRRequestUpdate(status='fulfilled'))
                print(f"  -> HR request marked as FULFILLED (assigned {assigned_count} batches)")
                await self.trainer_repo.db.commit()
                print(f"  -> Changes committed to database")
            else:
                print(f"  -> No batches assigned")
        
        print(f"\n=== AUTO-ASSIGNMENT COMPLETED ===")
    
    async def _check_trainer_conflict(self, trainer_id: UUID, start_date: date, end_date: date, exclude_batch_id: UUID) -> bool:
        """Check if trainer has conflicting batch assignments"""
        from sqlalchemy import text
        
        result = await self.trainer_repo.db.execute(
            text("""
                SELECT COUNT(*) FROM batches
                WHERE trainer_id = :trainer_id
                AND id != :exclude_batch_id
                AND (
                    (start_date <= :end_date AND end_date >= :start_date)
                )
            """),
            {
                'trainer_id': trainer_id,
                'exclude_batch_id': exclude_batch_id,
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        count = result.scalar()
        return count > 0

    async def update_trainer(self, trainer_id: UUID, trainer_data: TrainerUpdate) -> Optional[TrainerResponse]:
        trainer = await self.trainer_repo.update(trainer_id, trainer_data)
        return TrainerResponse.model_validate(trainer) if trainer else None

    async def delete_trainer(self, trainer_id: UUID) -> bool:
        return await self.trainer_repo.delete(trainer_id)

    async def create_trainers_bulk(self, trainers_data: List[TrainerCreate]) -> List[TrainerResponse]:
        from ..core.database import AsyncSessionLocal
        trainers = []
        
        for trainer_data in trainers_data:
            # Use separate session for each trainer to isolate transactions
            async with AsyncSessionLocal() as isolated_db:
                try:
                    # Create trainer
                    trainer_repo = TrainerRepository(isolated_db)
                    trainer_dict = {
                        'user_id': None,
                        'name': trainer_data.name,
                        'email': trainer_data.email,
                        'phone': trainer_data.phone,
                        'avatar': trainer_data.avatar,
                        'expertise': trainer_data.expertise,
                        'status': 'available',
                        'max_batches': trainer_data.max_batches,
                        'current_batches': 0,
                        'employment_type': trainer_data.employment_type.value if hasattr(trainer_data.employment_type, 'value') else trainer_data.employment_type,
                        'experience_level': trainer_data.experience_level.value if hasattr(trainer_data.experience_level, 'value') else trainer_data.experience_level,
                        'join_date': trainer_data.join_date
                    }
                    trainer = await trainer_repo.create_trainer(trainer_dict)
                    
                    # Create user account
                    user_repo = UserRepository(isolated_db)
                    username = trainer_data.email.split('@')[0]
                    password_hash = get_password_hash(username)
                    user = await user_repo.create_user(
                        name=trainer_data.name,
                        email=trainer_data.email,
                        password=password_hash,
                        role=AppRole.trainer,
                        avatar_url=trainer.avatar
                    )
                    
                    # Link trainer to user
                    from sqlalchemy import text
                    await isolated_db.execute(
                        text("UPDATE trainers SET user_id = :user_id WHERE id = :trainer_id"),
                        {'user_id': user.id, 'trainer_id': trainer.id}
                    )
                    await isolated_db.commit()
                    
                    # Refresh trainer
                    trainer = await trainer_repo.get_by_id(trainer.id)
                    
                    trainers.append(TrainerResponse.model_validate(trainer))
                    print(f"Trainer and user created successfully: {trainer_data.email}")
                except Exception as e:
                    print(f"Failed to create trainer {trainer_data.email}: {e}")
                    # Skip this trainer and continue with next
                    continue
        
        return trainers

    async def get_available_trainers(self, domain: str, start_date: date, end_date: date) -> List[TrainerResponse]:
        trainers = await self.trainer_repo.get_available_by_domain(domain, start_date, end_date)
        return [TrainerResponse.model_validate(trainer) for trainer in trainers]

    async def get_trainer_allocations(self, trainer_id: UUID):
        try:
            return await self.trainer_repo.get_trainer_allocations(trainer_id)
        except Exception as e:
            print(f"Error in trainer_service.get_trainer_allocations: {e}")
            return []