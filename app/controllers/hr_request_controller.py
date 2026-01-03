from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..core.database import get_db
from ..core.auth import get_current_user
from ..services.hr_request_service import HRRequestService
from ..schemas import HRRequestResponse, HRRequestCreate, HRRequestUpdate, HRRequestStatus

router = APIRouter(prefix="/hr-requests", tags=["HR Requests"])

@router.get("/", response_model=List[HRRequestResponse])
async def get_hr_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[HRRequestStatus] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    hr_service = HRRequestService(db)
    return await hr_service.get_hr_requests(skip, limit, status)

@router.post("/", response_model=HRRequestResponse)
async def create_hr_request(
    hr_request_data: HRRequestCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    hr_service = HRRequestService(db)
    return await hr_service.create_hr_request(hr_request_data, UUID(current_user["user_id"]))

@router.put("/{request_id}", response_model=HRRequestResponse)
async def update_hr_request(
    request_id: UUID,
    hr_request_data: HRRequestUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    hr_service = HRRequestService(db)
    request = await hr_service.update_hr_request(request_id, hr_request_data)
    if not request:
        raise HTTPException(status_code=404, detail="HR request not found")
    return request