from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date
import json
import asyncio
import traceback
from ..core.database import get_db
from ..core.auth import get_current_user
from ..services.trainer_service import TrainerService
from ..schemas import TrainerResponse, TrainerCreate, TrainerUpdate, TrainerStatus, AppRole
from ..core.response import APIResponse
from ..core.error_logger import ErrorLogger
from ..core.logging_config import logger

router = APIRouter(prefix="/trainers", tags=["Trainers"])

@router.get("/me/profile")
async def get_my_trainer_profile(db: AsyncSession = Depends(get_db)):
    logger.info("👤 GET /trainers/me/profile called (TEMP: no auth to stop iteration)")
    try:
        trainer_service = TrainerService(db)
        # Get the first trainer from database to stop the iteration loop
        trainers = await trainer_service.get_trainers(0, 1)
        if not trainers or len(trainers) == 0:
            logger.warning("No trainers found in database")
            return APIResponse.error("No trainers found in database", 404)
        
        trainer = trainers[0]
        logger.info(f"✅ Successfully fetched trainer: {trainer.get('email', 'unknown')}")
        return APIResponse.success(trainer)
    except Exception as e:
        logger.error(f"❌ Error in get_my_trainer_profile: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "get_my_trainer_profile")
        return APIResponse.error("Failed to fetch trainer profile", 500, error_id)

@router.get("/me/assignments")
async def get_my_assignments(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    print(f"\n=== GET MY ASSIGNMENTS CALLED ===")
    print(f"Current user: {current_user}")
    try:
        trainer_service = TrainerService(db)
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT id FROM trainers WHERE user_id = :user_id"),
            {'user_id': current_user['user_id']}
        )
        trainer = result.first()
        print(f"Trainer found: {trainer}")
        if not trainer:
            print("No trainer profile found for this user")
            return APIResponse.error("Trainer profile not found", 404)
        
        trainer_id = trainer[0]
        print(f"Fetching allocations for trainer_id: {trainer_id}")
        allocations = await trainer_service.get_trainer_allocations(trainer_id)
        print(f"Allocations found: {len(allocations)}")
        return APIResponse.success(allocations)
    except Exception as e:
        print(f"Error in get_my_assignments: {e}")
        import traceback
        traceback.print_exc()
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "get_my_assignments")
        return APIResponse.error("Failed to fetch assignments", 500, error_id)

@router.put("/me/expertise")
async def update_my_expertise(
    expertise: List[str],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        trainer_service = TrainerService(db)
        from sqlalchemy import text
        result = await db.execute(
            text("SELECT id FROM trainers WHERE user_id = :user_id"),
            {'user_id': current_user['user_id']}
        )
        trainer = result.first()
        if not trainer:
            return APIResponse.error("Trainer profile not found", 404)
        
        trainer_id = trainer[0]
        update_data = TrainerUpdate(expertise=expertise)
        updated_trainer = await trainer_service.update_trainer(trainer_id, update_data)
        return APIResponse.success(updated_trainer)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "update_my_expertise")
        return APIResponse.error("Failed to update expertise", 500, error_id)

@router.get("/")
async def get_trainers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[TrainerStatus] = None,
    expertise: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"📊 GET /trainers called - skip: {skip}, limit: {limit}, status: {status}, expertise: {expertise}")
    try:
        trainer_service = TrainerService(db)
        logger.info("🔍 Fetching trainers from service...")
        trainers = await trainer_service.get_trainers(skip, limit, status, expertise)
        logger.info(f"✅ Successfully fetched {len(trainers) if trainers else 0} trainers")
        return APIResponse.success(trainers)
    except Exception as e:
        logger.error(f"❌ Error in get_trainers: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "get_trainers")
        return APIResponse.error("Failed to fetch trainers", 500, error_id)

@router.post("/")
async def create_trainer(trainer_data: TrainerCreate, db: AsyncSession = Depends(get_db)):
    try:
        trainer_service = TrainerService(db)
        trainer = await trainer_service.create_trainer(trainer_data)
        return APIResponse.success(trainer, 201)
    except ValueError as e:
        print(f"ValueError creating trainer: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Exception creating trainer: {e}")
        import traceback
        traceback.print_exc()
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "create_trainer")
        raise HTTPException(status_code=500, detail=f"Failed to create trainer: {str(e)}")

@router.post("/bulk")
async def create_trainers_bulk(trainers_data: List[TrainerCreate], db: AsyncSession = Depends(get_db)):
    print(f"\n=== BULK UPLOAD STARTED: {len(trainers_data)} trainers ===")
    async def event_generator():
        from ..core.database import AsyncSessionLocal
        from ..repositories.trainer_repository import TrainerRepository
        from ..repositories.user_repository import UserRepository
        from ..core.security import get_password_hash
        
        total = len(trainers_data)
        created = []
        
        for idx, trainer_data in enumerate(trainers_data, 1):
            print(f"\n[{idx}/{total}] Processing: {trainer_data.email}")
            try:
                async with AsyncSessionLocal() as session:
                    trainer_repo = TrainerRepository(session)
                    user_repo = UserRepository(session)
                    
                    # Check duplicate trainer
                    existing_trainer = await trainer_repo.get_trainer_by_email(trainer_data.email)
                    if existing_trainer:
                        print(f"  -> SKIPPED: Trainer exists")
                        event = json.dumps({'progress': idx, 'total': total, 'status': 'skipped', 'email': trainer_data.email})
                        yield f"data: {event}\n\n"
                        continue
                    
                    # Check duplicate user
                    existing_user = await user_repo.get_by_email(trainer_data.email)
                    if existing_user:
                        print(f"  -> SKIPPED: User exists")
                        event = json.dumps({'progress': idx, 'total': total, 'status': 'skipped', 'email': trainer_data.email})
                        yield f"data: {event}\n\n"
                        continue
                    
                    # Create user account
                    print(f"  -> Creating user...")
                    user = await user_repo.create_user(
                        name=trainer_data.name,
                        email=trainer_data.email,
                        password=get_password_hash("trainer123"),
                        role=AppRole.trainer
                    )
                    print(f"  -> User created: {user.id}")
                    
                    # Create trainer
                    print(f"  -> Creating trainer...")
                    trainer_data_dict = trainer_data.model_dump()
                    # Convert enum objects to their string values
                    if hasattr(trainer_data_dict.get('employment_type'), 'value'):
                        trainer_data_dict['employment_type'] = trainer_data_dict['employment_type'].value
                    if hasattr(trainer_data_dict.get('experience_level'), 'value'):
                        trainer_data_dict['experience_level'] = trainer_data_dict['experience_level'].value
                    if hasattr(trainer_data_dict.get('status'), 'value'):
                        trainer_data_dict['status'] = trainer_data_dict['status'].value
                    
                    trainer_data_dict["user_id"] = user.id
                    trainer_data_dict["current_batches"] = 0
                    if "status" not in trainer_data_dict or not trainer_data_dict["status"]:
                        trainer_data_dict["status"] = "available"
                    trainer = await trainer_repo.create_trainer(trainer_data_dict)
                    await session.commit()
                    print(f"  -> SUCCESS: Trainer created {trainer.id}")
                    
                    created.append(trainer)
                    event = json.dumps({'progress': idx, 'total': total, 'status': 'success', 'name': trainer_data.name})
                    yield f"data: {event}\n\n"
                    
            except Exception as e:
                error_msg = str(e)
                print(f"Error creating trainer {trainer_data.email}: {error_msg}")
                import traceback
                traceback.print_exc()
                event = json.dumps({
                    'progress': idx, 
                    'total': total, 
                    'status': 'error', 
                    'email': trainer_data.email,
                    'error': error_msg[:100]  # Send first 100 chars of error to frontend
                })
                yield f"data: {event}\n\n"
                continue
        
        event = json.dumps({'progress': total, 'total': total, 'status': 'complete', 'count': len(created)})
        yield f"data: {event}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/available")
async def get_available_trainers(
    domain: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        trainer_service = TrainerService(db)
        trainers = await trainer_service.get_available_trainers(domain, start_date, end_date)
        return APIResponse.success(trainers)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "get_available_trainers")
        return APIResponse.error("Failed to fetch available trainers", 500, error_id)

@router.get("/{trainer_id}")
async def get_trainer(trainer_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        trainer_service = TrainerService(db)
        trainer = await trainer_service.get_trainer_by_id(trainer_id)
        if not trainer:
            return APIResponse.error("Trainer not found", 404)
        return APIResponse.success(trainer)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "get_trainer")
        return APIResponse.error("Failed to fetch trainer", 500, error_id)

@router.get("/{trainer_id}/allocations")
async def get_trainer_allocations(trainer_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        trainer_service = TrainerService(db)
        allocations = await trainer_service.get_trainer_allocations(trainer_id)
        return APIResponse.success(allocations)
    except Exception as e:
        print(f"Error getting trainer allocations: {e}")
        import traceback
        traceback.print_exc()
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "get_trainer_allocations")
        return APIResponse.error("Failed to fetch trainer allocations", 500, error_id)

@router.put("/{trainer_id}")
async def update_trainer(
    trainer_id: UUID, 
    trainer_data: TrainerUpdate, 
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        trainer_service = TrainerService(db)
        
        # Get trainer to check ownership
        trainer = await trainer_service.get_trainer_by_id(trainer_id)
        if not trainer:
            return APIResponse.error("Trainer not found", 404)
        
        # Check permissions
        user_role = current_user.get("role")
        user_id = UUID(current_user.get("user_id"))
        
        # If trainer role, only allow updating their own profile and only expertise field
        if user_role == "trainer":
            if str(trainer.get("user_id")) != str(user_id):
                return APIResponse.error("You can only update your own profile", 403)
            # Trainers can only update expertise
            allowed_update = TrainerUpdate(expertise=trainer_data.expertise)
            trainer = await trainer_service.update_trainer(trainer_id, allowed_update)
        else:
            # Admin/HR can update everything
            trainer = await trainer_service.update_trainer(trainer_id, trainer_data)
        
        return APIResponse.success(trainer)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "update_trainer")
        return APIResponse.error("Failed to update trainer", 500, error_id)

@router.delete("/{trainer_id}")
async def delete_trainer(trainer_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        trainer_service = TrainerService(db)
        success = await trainer_service.delete_trainer(trainer_id)
        if not success:
            return APIResponse.error("Trainer not found", 404)
        return APIResponse.success({"message": "Trainer deleted successfully"})
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "trainer_controller", "delete_trainer")
        return APIResponse.error("Failed to delete trainer", 500, error_id)