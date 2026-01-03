from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from ..models import Project, Engagement
from ..schemas import ProjectCreate, ProjectUpdate

class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[Project]:
        query = select(Project).options(
            selectinload(Project.engagements).selectinload(Engagement.batches)
        )
        
        if status:
            query = query.where(Project.status == status)
            
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, project_id: UUID) -> Optional[Project]:
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.engagements).selectinload(Engagement.batches))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def create(self, project_data: ProjectCreate, created_by: UUID, pm_ids: Optional[List[UUID]] = None) -> Project:
        project_dict = project_data.model_dump()
        contact = project_dict.pop("primary_contact")
        project_dict.update({
            "primary_contact_name": contact["name"],
            "primary_contact_email": contact["email"],
            "primary_contact_phone": contact["phone"],
            "created_by": created_by,
            "project_manager_ids": pm_ids or [],
            "status": "upcoming"
        })
        
        project = Project(**project_dict)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update(self, project_id: UUID, project_data: ProjectUpdate) -> Optional[Project]:
        update_data = project_data.model_dump(exclude_unset=True)
        if "primary_contact" in update_data:
            contact = update_data.pop("primary_contact")
            update_data.update({
                "primary_contact_name": contact["name"],
                "primary_contact_email": contact["email"],
                "primary_contact_phone": contact["phone"]
            })
        
        if update_data:
            await self.db.execute(
                update(Project).where(Project.id == project_id).values(**update_data)
            )
            await self.db.commit()
        return await self.get_by_id(project_id)

    async def delete(self, project_id: UUID) -> bool:
        from ..models import Batch
        # Delete all batches for all engagements in this project
        await self.db.execute(
            delete(Batch).where(
                Batch.engagement_id.in_(
                    select(Engagement.id).where(Engagement.project_id == project_id)
                )
            )
        )
        # Delete all engagements
        await self.db.execute(delete(Engagement).where(Engagement.project_id == project_id))
        # Delete the project
        result = await self.db.execute(delete(Project).where(Project.id == project_id))
        await self.db.commit()
        return result.rowcount > 0