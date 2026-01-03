from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..repositories.hr_request_repository import HRRequestRepository
from ..schemas import HRRequestResponse, HRRequestCreate, HRRequestUpdate

class HRRequestService:
    def __init__(self, db: AsyncSession):
        self.hr_request_repo = HRRequestRepository(db)

    async def get_hr_requests(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[HRRequestResponse]:
        requests = await self.hr_request_repo.get_all(skip, limit, status)
        result = []
        for req in requests:
            req_dict = {
                "id": req.id,
                "project_id": req.project_id,
                "engagement_id": req.engagement_id,
                "domain": req.domain,
                "trainers_needed": req.trainers_needed,
                "urgency": req.urgency,
                "status": req.status,
                "notes": req.notes,
                "created_at": req.created_at,
                "created_by": req.creator.name if hasattr(req, 'creator') and req.creator else str(req.created_by),
                "updated_at": req.updated_at
            }
            result.append(HRRequestResponse(**req_dict))
        return result

    async def create_hr_request(self, hr_request_data: HRRequestCreate, created_by: UUID) -> HRRequestResponse:
        request = await self.hr_request_repo.create(hr_request_data, created_by)
        
        # Get user name for created_by
        from ..repositories.user_repository import UserRepository
        user_repo = UserRepository(self.hr_request_repo.db)
        user = await user_repo.get_by_id(created_by)
        
        req_dict = {
            "id": request.id,
            "project_id": request.project_id,
            "engagement_id": request.engagement_id,
            "domain": request.domain,
            "trainers_needed": request.trainers_needed,
            "urgency": request.urgency,
            "status": request.status,
            "notes": request.notes,
            "created_at": request.created_at,
            "created_by": user.name if user else str(created_by),
            "updated_at": request.updated_at
        }
        return HRRequestResponse(**req_dict)

    async def update_hr_request(self, request_id: UUID, hr_request_data: HRRequestUpdate) -> Optional[HRRequestResponse]:
        request = await self.hr_request_repo.update(request_id, hr_request_data)
        if not request:
            return None
        
        req_dict = {
            "id": request.id,
            "project_id": request.project_id,
            "engagement_id": request.engagement_id,
            "domain": request.domain,
            "trainers_needed": request.trainers_needed,
            "urgency": request.urgency,
            "status": request.status,
            "notes": request.notes,
            "created_at": request.created_at,
            "created_by": request.creator.name if hasattr(request, 'creator') and request.creator else str(request.created_by),
            "updated_at": request.updated_at
        }
        return HRRequestResponse(**req_dict)