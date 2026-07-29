from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from enum import Enum

class AppRole(str, Enum):
    admin = "admin"
    hr = "hr"
    project_manager = "project_manager"
    trainer = "trainer"

class TrainerStatus(str, Enum):
    available = "available"
    partially_allocated = "partially_allocated"
    fully_allocated = "fully_allocated"
    on_leave = "on_leave"

class EmploymentType(str, Enum):
    full_time = "full_time"
    part_time = "part_time"
    freelance = "freelance"
    intern = "intern"

class ExperienceLevel(str, Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"

class Gender(str, Enum):
    male = "male"
    female = "female"

class ProjectStatus(str, Enum):
    active = "active"
    upcoming = "upcoming"
    completed = "completed"

class EngagementStatus(str, Enum):
    active = "active"
    upcoming = "upcoming"
    completed = "completed"

class BatchStatus(str, Enum):
    confirmed = "confirmed"
    pending = "pending"
    awaiting_confirmation = "awaiting_confirmation"

class HRRequestStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    fulfilled = "fulfilled"

class UrgencyLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class AttendanceStatus(str, Enum):
    pending = "pending"
    present = "present"
    absent = "absent"
    half_day = "half_day"

# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    name: str
    email: EmailStr
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    role: AppRole
    password: str
    phone: Optional[str] = None
    send_email: Optional[bool] = True
    password: str
    phone: Optional[str] = None
    send_email: Optional[bool] = True

class UserResponse(UserBase):
    id: UUID
    role: AppRole
    phone: Optional[str] = None
    status: str = "active"
    created_at: datetime
    
    class Config:
        from_attributes = True

# Trainer Schemas
class TrainerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    expertise: List[str]
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    max_batches: int
    avatar: Optional[str] = None

class TrainerCreate(TrainerBase):
    join_date: date

class TrainerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    expertise: Optional[List[str]] = None
    status: Optional[TrainerStatus] = None
    employment_type: Optional[EmploymentType] = None
    experience_level: Optional[ExperienceLevel] = None
    max_batches: Optional[int] = None
    avatar: Optional[str] = None

class TrainerResponse(TrainerBase):
    id: UUID
    user_id: Optional[UUID] = None
    status: TrainerStatus
    current_batches: int
    join_date: date
    created_at: datetime
    
    class Config:
        from_attributes = True

# Project Schemas
class PrimaryContact(BaseModel):
    name: str
    email: EmailStr
    phone: str

class ProjectBase(BaseModel):
    name: str
    client_name: str
    primary_contact: PrimaryContact
    project_type: List[str]
    start_date: date
    end_date: date
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    primary_contact: Optional[PrimaryContact] = None
    project_type: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    project_manager_ids: Optional[List[UUID]] = None

class ProjectResponse(BaseModel):
    id: UUID
    name: str
    client_name: str
    primary_contact_name: str
    primary_contact_email: str
    primary_contact_phone: str
    project_type: List[str]
    start_date: date
    end_date: date
    description: Optional[str]
    status: ProjectStatus
    project_manager_ids: Optional[List[UUID]] = []
    created_at: datetime
    created_by: UUID
    engagements: Optional[List['EngagementWithBatches']] = []
    
    class Config:
        from_attributes = True

# Engagement Schemas
class EngagementBase(BaseModel):
    name: str
    domain: str
    training_type: str
    total_students: int
    students_per_batch: int
    start_date: date
    end_date: date

class EngagementCreate(EngagementBase):
    pass

class EngagementResponse(EngagementBase):
    id: UUID
    project_id: UUID
    status: EngagementStatus
    created_at: datetime
    batches: Optional[List['BatchResponse']] = []
    
    class Config:
        from_attributes = True

# Create alias for use in ProjectResponse
class EngagementWithBatches(EngagementResponse):
    pass

# Batch Schemas
class BatchBase(BaseModel):
    batch_number: int
    students: int
    start_date: date
    end_date: date

class BatchResponse(BatchBase):
    id: UUID
    engagement_id: UUID
    status: BatchStatus
    trainer_id: Optional[UUID] = None
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class BatchAllocation(BaseModel):
    trainer_id: UUID
    support_staff: Optional[List[UUID]] = []

# HR Request Schemas
class HRRequestBase(BaseModel):
    project_id: UUID
    engagement_id: UUID
    domain: str
    trainers_needed: int
    urgency: UrgencyLevel
    notes: Optional[str] = None

class HRRequestCreate(HRRequestBase):
    pass

class HRRequestUpdate(BaseModel):
    status: Optional[HRRequestStatus] = None
    notes: Optional[str] = None

class HRRequestResponse(HRRequestBase):
    id: UUID
    status: HRRequestStatus
    created_at: datetime
    created_by: str  # User name instead of UUID
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Attendance Schemas
class AttendanceBase(BaseModel):
    batch_id: str
    project_id: str
    engagement_id: str
    date: Optional[date] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    punch_out: Optional[datetime] = None
    completion_notes: Optional[str] = None

class AttendanceResponse(BaseModel):
    id: UUID
    trainer_id: str
    trainer_name: str
    batch_id: str
    project_id: str
    engagement_id: str
    date: date
    status: AttendanceStatus
    punch_in: Optional[datetime] = None
    punch_out: Optional[datetime] = None
    completion_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Response wrappers
class PaginatedResponse(BaseModel):
    data: List[dict]
    total: int
    page: int
    limit: int

# Update forward references
ProjectResponse.model_rebuild()
EngagementWithBatches.model_rebuild()