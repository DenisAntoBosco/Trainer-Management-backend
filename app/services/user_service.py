from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from ..repositories.user_repository import UserRepository
from ..schemas import UserResponse, UserCreate
from ..core.password import hash_password
from .email_service import EmailService

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.email_service = EmailService()

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        users = await self.user_repo.get_all(skip, limit)
        return [
            UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                avatar_url=user.avatar_url,
                phone=getattr(user, 'phone', None),
                role=user.roles[0].role.value if user.roles else "trainer",
                status="active",
                created_at=user.created_at
            ) for user in users
        ]

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserResponse]:
        user = await self.user_repo.get_by_id(user_id)
        if user:
            return UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                avatar_url=user.avatar_url,
                phone=getattr(user, 'phone', None),
                role=user.roles[0].role.value if user.roles else "trainer",
                status="active",
                created_at=user.created_at
            )
        return None
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        Create a new user with hashed password and optionally send welcome email.
        """
        # Hash the password
        hashed_password = hash_password(user_data.password)
        
        # Create user in database
        user = await self.user_repo.create_user(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role,
            avatar_url=user_data.avatar_url,
            phone=user_data.phone
        )
        
        # Send welcome email if requested
        if user_data.send_email:
            await self.email_service.send_welcome_email(
                to_email=user_data.email,
                user_name=user_data.name,
                temporary_password=user_data.password  # Send original password, not hashed
            )
        
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            phone=user_data.phone,
            role=user_data.role,
            status="active",
            created_at=user.created_at
        )
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user by ID."""
        return await self.user_repo.delete(user_id)