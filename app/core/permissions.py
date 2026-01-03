from fastapi import HTTPException, status
from typing import List
from ..schemas import AppRole

class Permission:
    # User management
    CREATE_USER = "create_user"
    DELETE_USER = "delete_user"
    VIEW_USERS = "view_users"
    
    # Trainer management
    CREATE_TRAINER = "create_trainer"
    UPDATE_TRAINER = "update_trainer"
    DELETE_TRAINER = "delete_trainer"
    VIEW_TRAINERS = "view_trainers"
    
    # Project management
    CREATE_PROJECT = "create_project"
    UPDATE_PROJECT = "update_project"
    DELETE_PROJECT = "delete_project"
    VIEW_PROJECTS = "view_projects"
    
    # Engagement management
    CREATE_ENGAGEMENT = "create_engagement"
    DELETE_ENGAGEMENT = "delete_engagement"
    
    # Batch management
    ALLOCATE_TRAINER = "allocate_trainer"
    CONFIRM_BATCH = "confirm_batch"
    
    # HR requests
    CREATE_HR_REQUEST = "create_hr_request"
    UPDATE_HR_REQUEST = "update_hr_request"
    VIEW_HR_REQUESTS = "view_hr_requests"
    
    # Attendance
    VIEW_ALL_ATTENDANCE = "view_all_attendance"
    VIEW_OWN_ATTENDANCE = "view_own_attendance"
    MANAGE_ATTENDANCE = "manage_attendance"

ROLE_PERMISSIONS = {
    "admin": [
        Permission.CREATE_USER,
        Permission.DELETE_USER,
        Permission.VIEW_USERS,
        Permission.CREATE_TRAINER,
        Permission.UPDATE_TRAINER,
        Permission.DELETE_TRAINER,
        Permission.VIEW_TRAINERS,
        Permission.CREATE_PROJECT,
        Permission.UPDATE_PROJECT,
        Permission.DELETE_PROJECT,
        Permission.VIEW_PROJECTS,
        Permission.CREATE_ENGAGEMENT,
        Permission.DELETE_ENGAGEMENT,
        Permission.ALLOCATE_TRAINER,
        Permission.CONFIRM_BATCH,
        Permission.CREATE_HR_REQUEST,
        Permission.UPDATE_HR_REQUEST,
        Permission.VIEW_HR_REQUESTS,
        Permission.VIEW_ALL_ATTENDANCE,
        Permission.MANAGE_ATTENDANCE,
    ],
    "project_manager": [
        Permission.VIEW_USERS,
        Permission.VIEW_TRAINERS,
        Permission.CREATE_PROJECT,
        Permission.UPDATE_PROJECT,
        Permission.DELETE_PROJECT,
        Permission.VIEW_PROJECTS,
        Permission.CREATE_ENGAGEMENT,
        Permission.DELETE_ENGAGEMENT,
        Permission.ALLOCATE_TRAINER,
        Permission.CONFIRM_BATCH,
        Permission.CREATE_HR_REQUEST,
        Permission.VIEW_HR_REQUESTS,
        Permission.VIEW_ALL_ATTENDANCE,
    ],
    "hr": [
        Permission.VIEW_USERS,
        Permission.CREATE_TRAINER,
        Permission.UPDATE_TRAINER,
        Permission.VIEW_TRAINERS,
        Permission.VIEW_PROJECTS,
        Permission.UPDATE_HR_REQUEST,
        Permission.VIEW_HR_REQUESTS,
        Permission.VIEW_ALL_ATTENDANCE,
    ],
    "trainer": [
        Permission.VIEW_OWN_ATTENDANCE,
        Permission.MANAGE_ATTENDANCE,
    ],
}

def has_permission(user_role: str, permission: str) -> bool:
    """Check if a role has a specific permission"""
    return permission in ROLE_PERMISSIONS.get(user_role, [])

def require_permission(permission: str):
    """Decorator to check if user has required permission"""
    def decorator(current_user: dict):
        user_role = current_user.get("role")
        if not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        return current_user
    return decorator
