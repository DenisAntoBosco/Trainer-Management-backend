from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..core.database import get_db
from ..services.project_service import ProjectService
from ..schemas import ProjectResponse, ProjectCreate, ProjectUpdate, ProjectStatus, EngagementCreate, EngagementResponse
from ..core.response import APIResponse
from ..core.error_logger import ErrorLogger
from ..core.logging_config import logger

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/")
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[ProjectStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"📊 GET /projects called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        projects = await project_service.get_projects(skip, limit, status)
        logger.info(f"✅ Successfully fetched {len(projects) if projects else 0} projects")
        return APIResponse.success(projects)
    except Exception as e:
        logger.error(f"❌ Error in get_projects: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "get_projects")
        return APIResponse.error("Failed to fetch projects", 500, error_id)

@router.post("/")
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"🎯 POST /projects called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        project = await project_service.create_project(project_data, UUID(session_user["user_id"]))
        logger.info(f"✅ Successfully created project: {project.name}")
        return APIResponse.success(project, 201)
    except Exception as e:
        logger.error(f"❌ Error in create_project: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "create_project")
        return APIResponse.error("Failed to create project", 500, error_id)

@router.get("/{project_id}")
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"🔍 GET /projects/{project_id} called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        project = await project_service.get_project_by_id(project_id)
        if not project:
            logger.warning(f"Project not found: {project_id}")
            return APIResponse.error("Project not found", 404)
        logger.info(f"✅ Successfully fetched project: {project.name}")
        return APIResponse.success(project)
    except Exception as e:
        logger.error(f"❌ Error in get_project: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "get_project")
        return APIResponse.error("Failed to fetch project", 500, error_id)

@router.put("/{project_id}")
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"✏️ PUT /projects/{project_id} called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        project = await project_service.update_project(project_id, project_data)
        if not project:
            logger.warning(f"Project not found: {project_id}")
            return APIResponse.error("Project not found", 404)
        logger.info(f"✅ Successfully updated project: {project.name}")
        return APIResponse.success(project)
    except Exception as e:
        logger.error(f"❌ Error in update_project: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "update_project")
        return APIResponse.error("Failed to update project", 500, error_id)

@router.post("/{project_id}/engagements")
async def create_engagement(
    project_id: UUID,
    engagement_data: EngagementCreate,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"🎯 POST /projects/{project_id}/engagements called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        engagement = await project_service.create_engagement(project_id, engagement_data)
        logger.info(f"✅ Successfully created engagement for project: {project_id}")
        return APIResponse.success(engagement, 201)
    except Exception as e:
        logger.error(f"❌ Error in create_engagement: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "create_engagement")
        return APIResponse.error("Failed to create engagement", 500, error_id)

@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"🗑️ DELETE /projects/{project_id} called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        success = await project_service.delete_project(project_id)
        if not success:
            logger.warning(f"Project not found: {project_id}")
            return APIResponse.error("Project not found", 404)
        logger.info(f"✅ Successfully deleted project: {project_id}")
        return APIResponse.success({"message": "Project deleted successfully"})
    except Exception as e:
        logger.error(f"❌ Error in delete_project: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "delete_project")
        return APIResponse.error(f"Failed to delete project: {str(e)}", 500, error_id)

@router.delete("/engagements/{engagement_id}")
async def delete_engagement(
    engagement_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"🗑️ DELETE /engagements/{engagement_id} called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        success = await project_service.delete_engagement(engagement_id)
        if not success:
            logger.warning(f"Engagement not found: {engagement_id}")
            return APIResponse.error("Engagement not found", 404)
        logger.info(f"✅ Successfully deleted engagement: {engagement_id}")
        return APIResponse.success({"message": "Engagement deleted successfully"})
    except Exception as e:
        logger.error(f"❌ Error in delete_engagement: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "delete_engagement")
        return APIResponse.error(f"Failed to delete engagement: {str(e)}", 500, error_id)

@router.post("/{project_id}/project-managers/{pm_id}")
async def add_project_manager(
    project_id: UUID,
    pm_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"👥 POST /projects/{project_id}/project-managers/{pm_id} called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        project = await project_service.add_project_manager(project_id, pm_id)
        if not project:
            logger.warning(f"Project not found or PM already assigned: {project_id}, {pm_id}")
            return APIResponse.error("Project not found or PM already assigned", 404)
        logger.info(f"✅ Successfully added project manager {pm_id} to project {project_id}")
        return APIResponse.success(project)
    except Exception as e:
        logger.error(f"❌ Error in add_project_manager: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "add_project_manager")
        return APIResponse.error("Failed to add project manager", 500, error_id)

@router.delete("/{project_id}/project-managers/{pm_id}")
async def remove_project_manager(
    project_id: UUID,
    pm_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Mock authentication - get user from session
    from ..core.mock_session import get_current_user as get_session_user
    
    session_user = get_session_user()
    
    # If no session, default to admin for development
    if not session_user.get("user_id"):
        session_user = {
            "user_id": "761d9409-8ed5-4ed3-b560-b2e8416d1003",
            "email": "admin@neoallocate.com",
            "role": "admin"
        }
        logger.info(f"👤 No session found, using default admin user")
    
    logger.info(f"🗑️ DELETE /projects/{project_id}/project-managers/{pm_id} called - User: {session_user['email']} (role: {session_user['role']})")
    
    try:
        project_service = ProjectService(db)
        project = await project_service.remove_project_manager(project_id, pm_id)
        if not project:
            logger.warning(f"Project not found or PM not assigned: {project_id}, {pm_id}")
            return APIResponse.error("Project not found or PM not assigned", 404)
        logger.info(f"✅ Successfully removed project manager {pm_id} from project {project_id}")
        return APIResponse.success(project)
    except Exception as e:
        logger.error(f"❌ Error in remove_project_manager: {str(e)}")
        error_id = await ErrorLogger.log_error(e, "project_controller", "remove_project_manager")
        return APIResponse.error("Failed to remove project manager", 500, error_id)