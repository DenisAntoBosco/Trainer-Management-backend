from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.permissions import Permission, has_permission
from ..services.user_service import UserService
from ..schemas import UserResponse, UserCreate

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(UUID(current_user["user_id"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not has_permission(current_user.get('role'), Permission.VIEW_USERS):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    user_service = UserService(db)
    return await user_service.get_users(skip, limit)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not has_permission(current_user.get('role'), Permission.CREATE_USER):
        raise HTTPException(status_code=403, detail="Only admins can create users")
    
    user_service = UserService(db)
    try:
        new_user = await user_service.create_user(user_data)
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not has_permission(current_user.get('role'), Permission.CREATE_USER):
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    user_service = UserService(db)
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "message": "User deleted successfully"}