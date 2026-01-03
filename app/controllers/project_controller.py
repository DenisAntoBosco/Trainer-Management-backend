from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..core.database import get_db
from ..core.auth import get_current_user
from ..services.project_service import ProjectService
from ..schemas import ProjectResponse, ProjectCreate, ProjectUpdate, ProjectStatus, EngagementCreate, EngagementResponse
from ..core.response import APIResponse
from ..core.error_logger import ErrorLogger

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/")
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[ProjectStatus] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        project_service = ProjectService(db)
        projects = await project_service.get_projects(skip, limit, status)
        return APIResponse.success(projects)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "project_controller", "get_projects")
        return APIResponse.error("Failed to fetch projects", 500, error_id)

@router.post("/")
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        project_service = ProjectService(db)
        project = await project_service.create_project(project_data, UUID(current_user["user_id"]))
        return APIResponse.success(project, 201)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "project_controller", "create_project")
        return APIResponse.error("Failed to create project", 500, error_id)

@router.get("/{project_id}")
async def get_project(project_id: UUID, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id)
        if not project:
            return APIResponse.error("Project not found", 404)
        return APIResponse.success(project)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "project_controller", "get_project")
        return APIResponse.error("Failed to fetch project", 500, error_id)

@router.put("/{project_id}")
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        project_service = ProjectService(db)
        project = await project_service.update_project(project_id, project_data)
        if not project:
            return APIResponse.error("Project not found", 404)
        return APIResponse.success(project)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "project_controller", "update_project")
        return APIResponse.error("Failed to update project", 500, error_id)

@router.post("/{project_id}/engagements")
async def create_engagement(
    project_id: UUID,
    engagement_data: EngagementCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        project_service = ProjectService(db)
        engagement = await project_service.create_engagement(project_id, engagement_data)
        return APIResponse.success(engagement, 201)
    except Exception as e:
        print(f"Error creating engagement: {e}")
        import traceback
        traceback.print_exc()
        error_id = await ErrorLogger.log_error(e, "project_controller", "create_engagement")
        return APIResponse.error("Failed to create engagement", 500, error_id)

@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        print(f"\n=== DELETE PROJECT: {project_id} ===")
        project_service = ProjectService(db)
        success = await project_service.delete_project(project_id)
        if not success:
            print(f"Project not found: {project_id}")
            return APIResponse.error("Project not found", 404)
        print(f"Project deleted successfully: {project_id}")
        return APIResponse.success({"message": "Project deleted successfully"})
    except Exception as e:
        print(f"Error deleting project {project_id}: {e}")
        import traceback
        traceback.print_exc()
        error_id = await ErrorLogger.log_error(e, "project_controller", "delete_project")
        return APIResponse.error(f"Failed to delete project: {str(e)}", 500, error_id)

@router.delete("/engagements/{engagement_id}")
async def delete_engagement(
    engagement_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        print(f"\n=== DELETE ENGAGEMENT: {engagement_id} ===")
        project_service = ProjectService(db)
        success = await project_service.delete_engagement(engagement_id)
        if not success:
            print(f"Engagement not found: {engagement_id}")
            return APIResponse.error("Engagement not found", 404)
        print(f"Engagement deleted successfully: {engagement_id}")
        return APIResponse.success({"message": "Engagement deleted successfully"})
    except Exception as e:
        print(f"Error deleting engagement {engagement_id}: {e}")
        import traceback
        traceback.print_exc()
        error_id = await ErrorLogger.log_error(e, "project_controller", "delete_engagement")
        return APIResponse.error(f"Failed to delete engagement: {str(e)}", 500, error_id)

@router.post("/{project_id}/project-managers/{pm_id}")
async def add_project_manager(
    project_id: UUID,
    pm_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        project_service = ProjectService(db)
        project = await project_service.add_project_manager(project_id, pm_id)
        if not project:
            return APIResponse.error("Project not found or PM already assigned", 404)
        return APIResponse.success(project)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "project_controller", "add_project_manager")
        return APIResponse.error("Failed to add project manager", 500, error_id)

@router.delete("/{project_id}/project-managers/{pm_id}")
async def remove_project_manager(
    project_id: UUID,
    pm_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        project_service = ProjectService(db)
        project = await project_service.remove_project_manager(project_id, pm_id)
        if not project:
            return APIResponse.error("Project not found or PM not assigned", 404)
        return APIResponse.success(project)
    except Exception as e:
        error_id = await ErrorLogger.log_error(e, "project_controller", "remove_project_manager")
        return APIResponse.error("Failed to remove project manager", 500, error_id)