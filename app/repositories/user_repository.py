from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from ..models import User, UserRole
from ..schemas import AppRole

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: dict) -> User:
        user = User(**user_data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def create_user(self, name: str, email: str, password: str, role: AppRole, avatar_url: Optional[str] = None, phone: Optional[str] = None) -> User:
        """
        Create a new user with role assignment using raw SQL to avoid ORM defaults.
        """
        from sqlalchemy import text
        import uuid
        
        user_id = uuid.uuid4()
        role_id = uuid.uuid4()
        
        # Insert user
        await self.db.execute(
            text("""
                INSERT INTO profiles (id, name, email, avatar_url, password_hash)
                VALUES (:id, :name, :email, :avatar_url, :password_hash)
            """),
            {'id': user_id, 'name': name, 'email': email, 'avatar_url': avatar_url, 'password_hash': password}
        )
        
        # Insert role
        await self.db.execute(
            text("""
                INSERT INTO user_roles (id, user_id, role)
                VALUES (:id, :user_id, :role)
            """),
            {'id': role_id, 'user_id': user_id, 'role': role.value}
        )
        
        await self.db.commit()
        
        # Return user object
        return await self.get_by_id(user_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete a user and their associated roles and trainer record if exists."""
        from sqlalchemy import text
        
        # Check if user exists
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        # Delete trainer record if exists (foreign key constraint)
        await self.db.execute(
            text("DELETE FROM trainers WHERE user_id = :user_id"),
            {'user_id': user_id}
        )
        
        # Delete user roles
        await self.db.execute(
            text("DELETE FROM user_roles WHERE user_id = :user_id"),
            {'user_id': user_id}
        )
        
        # Delete user
        await self.db.execute(
            text("DELETE FROM profiles WHERE id = :user_id"),
            {'user_id': user_id}
        )
        
        await self.db.commit()
        return True