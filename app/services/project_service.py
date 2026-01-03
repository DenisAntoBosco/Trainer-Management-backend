from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..repositories.project_repository import ProjectRepository
from ..repositories.engagement_repository import EngagementRepository
from ..schemas import ProjectResponse, ProjectCreate, ProjectUpdate, EngagementResponse, EngagementCreate

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.project_repo = ProjectRepository(db)
        self.engagement_repo = EngagementRepository(db)

    async def get_projects(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[ProjectResponse]:
        projects = await self.project_repo.get_all(skip, limit, status)
        result = []
        for project in projects:
            project_dict = {
                "id": project.id,
                "name": project.name,
                "client_name": project.client_name,
                "primary_contact_name": project.primary_contact_name,
                "primary_contact_email": project.primary_contact_email,
                "primary_contact_phone": project.primary_contact_phone,
                "project_type": project.project_type,
                "start_date": project.start_date,
                "end_date": project.end_date,
                "description": project.description,
                "status": project.status,
                "project_manager_ids": project.project_manager_ids or [],
                "created_at": project.created_at,
                "created_by": project.created_by,
                "engagements": []
            }
            
            # Add engagements with batches
            if hasattr(project, 'engagements') and project.engagements:
                for engagement in project.engagements:
                    engagement_dict = {
                        "id": engagement.id,
                        "project_id": engagement.project_id,
                        "name": engagement.name,
                        "domain": engagement.domain,
                        "training_type": engagement.training_type,
                        "total_students": engagement.total_students,
                        "students_per_batch": engagement.students_per_batch,
                        "start_date": engagement.start_date,
                        "end_date": engagement.end_date,
                        "status": engagement.status,
                        "created_at": engagement.created_at,
                        "batches": []
                    }
                    
                    # Add batches
                    if hasattr(engagement, 'batches') and engagement.batches:
                        for batch in engagement.batches:
                            batch_dict = {
                                "id": batch.id,
                                "engagement_id": batch.engagement_id,
                                "batch_number": batch.batch_number,
                                "students": batch.students,
                                "start_date": batch.start_date.isoformat() if batch.start_date else None,
                                "end_date": batch.end_date.isoformat() if batch.end_date else None,
                                "status": batch.status,
                                "trainer_id": str(batch.trainer_id) if batch.trainer_id else None,
                                "confirmed_at": batch.confirmed_at,
                                "confirmed_by": batch.confirmed_by,
                                "created_at": batch.created_at
                            }
                            engagement_dict["batches"].append(batch_dict)
                    
                    project_dict["engagements"].append(engagement_dict)
            
            result.append(ProjectResponse(**project_dict))
        return result

    async def get_project_by_id(self, project_id: UUID) -> Optional[ProjectResponse]:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None
            
        project_dict = {
            "id": project.id,
            "name": project.name,
            "client_name": project.client_name,
            "primary_contact_name": project.primary_contact_name,
            "primary_contact_email": project.primary_contact_email,
            "primary_contact_phone": project.primary_contact_phone,
            "project_type": project.project_type,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "description": project.description,
            "status": project.status,
            "project_manager_ids": project.project_manager_ids or [],
            "created_at": project.created_at,
            "created_by": project.created_by,
            "engagements": []
        }
        
        # Add engagements with batches
        if hasattr(project, 'engagements') and project.engagements:
            for engagement in project.engagements:
                engagement_dict = {
                    "id": engagement.id,
                    "project_id": engagement.project_id,
                    "name": engagement.name,
                    "domain": engagement.domain,
                    "training_type": engagement.training_type,
                    "total_students": engagement.total_students,
                    "students_per_batch": engagement.students_per_batch,
                    "start_date": engagement.start_date,
                    "end_date": engagement.end_date,
                    "status": engagement.status,
                    "created_at": engagement.created_at,
                    "batches": []
                }
                
                # Add batches
                if hasattr(engagement, 'batches') and engagement.batches:
                    for batch in engagement.batches:
                        batch_dict = {
                            "id": batch.id,
                            "engagement_id": batch.engagement_id,
                            "batch_number": batch.batch_number,
                            "students": batch.students,
                            "start_date": batch.start_date.isoformat() if batch.start_date else None,
                            "end_date": batch.end_date.isoformat() if batch.end_date else None,
                            "status": batch.status,
                            "trainer_id": str(batch.trainer_id) if batch.trainer_id else None,
                            "confirmed_at": batch.confirmed_at,
                            "confirmed_by": batch.confirmed_by,
                            "created_at": batch.created_at
                        }
                        engagement_dict["batches"].append(batch_dict)
                
                project_dict["engagements"].append(engagement_dict)
        
        return ProjectResponse(**project_dict)

    async def create_project(self, project_data: ProjectCreate, created_by: UUID) -> ProjectResponse:
        pm_id = await self._auto_assign_project_manager()
        pm_ids = [pm_id] if pm_id else []
        project = await self.project_repo.create(project_data, created_by, pm_ids)
        print(f"Project created with PM(s): {pm_ids}")
        return await self.get_project_by_id(project.id)
    
    async def _auto_assign_project_manager(self) -> Optional[UUID]:
        """Auto-assign project manager with least active projects (max 6 projects per PM)"""
        from sqlalchemy import text
        
        print("\n=== AUTO-ASSIGNING PROJECT MANAGER ===")
        
        result = await self.project_repo.db.execute(
            text("""
                SELECT u.id, u.name, COUNT(p.id) as project_count
                FROM profiles u
                INNER JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN projects p ON u.id = ANY(p.project_manager_ids) AND p.status IN ('active', 'upcoming')
                WHERE ur.role = 'project_manager'
                GROUP BY u.id, u.name
                HAVING COUNT(p.id) < 6
                ORDER BY COUNT(p.id) ASC, u.created_at ASC
                LIMIT 1
            """)
        )
        
        pm = result.first()
        if pm:
            print(f"Assigned PM: {pm.name} (current projects: {pm.project_count})")
            return pm.id
        
        print("No available PM found (all PMs have 6+ projects)")
        return None

    async def update_project(self, project_id: UUID, project_data: ProjectUpdate) -> Optional[ProjectResponse]:
        project = await self.project_repo.update(project_id, project_data)
        return await self.get_project_by_id(project_id) if project else None

    async def create_engagement(self, project_id: UUID, engagement_data: EngagementCreate) -> EngagementResponse:
        engagement = await self.engagement_repo.create(project_id, engagement_data)
        
        # Return engagement with batches
        engagement_dict = {
            "id": engagement.id,
            "project_id": engagement.project_id,
            "name": engagement.name,
            "domain": engagement.domain,
            "training_type": engagement.training_type,
            "total_students": engagement.total_students,
            "students_per_batch": engagement.students_per_batch,
            "start_date": engagement.start_date,
            "end_date": engagement.end_date,
            "status": engagement.status,
            "created_at": engagement.created_at,
            "batches": []
        }
        
        # Add batches
        if hasattr(engagement, 'batches') and engagement.batches:
            for batch in engagement.batches:
                batch_dict = {
                    "id": batch.id,
                    "engagement_id": batch.engagement_id,
                    "batch_number": batch.batch_number,
                    "students": batch.students,
                    "start_date": batch.start_date.isoformat() if batch.start_date else None,
                    "end_date": batch.end_date.isoformat() if batch.end_date else None,
                    "status": batch.status,
                    "trainer_id": str(batch.trainer_id) if batch.trainer_id else None,
                    "confirmed_at": batch.confirmed_at,
                    "confirmed_by": batch.confirmed_by,
                    "created_at": batch.created_at
                }
                engagement_dict["batches"].append(batch_dict)
        
        return EngagementResponse(**engagement_dict)

    async def delete_project(self, project_id: UUID) -> bool:
        return await self.project_repo.delete(project_id)
    
    async def delete_engagement(self, engagement_id: UUID) -> bool:
        return await self.engagement_repo.delete(engagement_id)
    
    async def add_project_manager(self, project_id: UUID, pm_id: UUID) -> Optional[ProjectResponse]:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None
        
        pm_ids = list(project.project_manager_ids or [])
        if pm_id in pm_ids:
            return None
        
        pm_ids.append(pm_id)
        await self.project_repo.update(project_id, ProjectUpdate(project_manager_ids=pm_ids))
        return await self.get_project_by_id(project_id)
    
    async def remove_project_manager(self, project_id: UUID, pm_id: UUID) -> Optional[ProjectResponse]:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            return None
        
        pm_ids = list(project.project_manager_ids or [])
        if pm_id not in pm_ids:
            return None
        
        pm_ids.remove(pm_id)
        await self.project_repo.update(project_id, ProjectUpdate(project_manager_ids=pm_ids))
        return await self.get_project_by_id(project_id)