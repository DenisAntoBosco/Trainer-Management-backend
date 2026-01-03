from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ..core.database import get_db
from ..core.auth import get_current_user
from ..services.batch_service import BatchService
from ..schemas import BatchResponse, BatchAllocation

router = APIRouter(prefix="/batches", tags=["Batches"])

@router.put("/{batch_id}/allocate", response_model=BatchResponse)
async def allocate_trainer(
    batch_id: UUID,
    allocation_data: BatchAllocation,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    batch_service = BatchService(db)
    batch = await batch_service.allocate_trainer(batch_id, allocation_data.trainer_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@router.post("/{batch_id}/confirm", response_model=BatchResponse)
async def confirm_allocation(
    batch_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    batch_service = BatchService(db)
    batch = await batch_service.confirm_allocation(batch_id, UUID(current_user["user_id"]))
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch