from sqlalchemy import Column, String, Integer, DateTime, Date, Boolean, Text, ForeignKey, ARRAY, Enum as SQLEnum, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from ..core.database import Base

class AppRole(enum.Enum):
    admin = "admin"
    hr = "hr"
    project_manager = "project_manager"
    trainer = "trainer"

class TrainerStatus(enum.Enum):
    available = "available"
    partially_allocated = "partially_allocated"
    fully_allocated = "fully_allocated"
    on_leave = "on_leave"

class EmploymentType(enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    freelance = "freelance"
    intern = "intern"

class ExperienceLevel(enum.Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"

class ProjectStatus(enum.Enum):
    active = "active"
    upcoming = "upcoming"
    completed = "completed"

class EngagementStatus(enum.Enum):
    active = "active"
    upcoming = "upcoming"
    completed = "completed"

class BatchStatus(enum.Enum):
    confirmed = "confirmed"
    pending = "pending"
    awaiting_confirmation = "awaiting_confirmation"

class HRRequestStatus(enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    fulfilled = "fulfilled"

class UrgencyLevel(enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class AttendanceStatus(enum.Enum):
    pending = "pending"
    present = "present"
    absent = "absent"
    half_day = "half_day"

class User(Base):
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    avatar_url = Column(Text)
    password_hash = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    roles = relationship("UserRole", back_populates="user")

class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    role = Column(SQLEnum(AppRole, name='app_role', create_type=False), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="roles")

class Trainer(Base):
    __tablename__ = "trainers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    phone = Column(String(20))
    avatar = Column(Text)
    expertise = Column(ARRAY(Text), nullable=False)
    status = Column(SQLEnum(TrainerStatus, name='trainer_status', create_type=False), nullable=False)
    max_batches = Column(Integer, nullable=False)
    current_batches = Column(Integer, nullable=False, default=0)
    employment_type = Column(SQLEnum(EmploymentType, name='employment_type', create_type=False), nullable=False)
    experience_level = Column(SQLEnum(ExperienceLevel, name='experience_level', create_type=False), nullable=False)
    join_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    client_name = Column(Text, nullable=False)
    primary_contact_name = Column(Text, nullable=False)
    primary_contact_email = Column(Text, nullable=False)
    primary_contact_phone = Column(Text, nullable=False)
    project_type = Column(ARRAY(Text), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(ProjectStatus, name='project_status', create_type=False), nullable=False)
    project_manager_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    
    engagements = relationship("Engagement", back_populates="project")

class Engagement(Base):
    __tablename__ = "engagements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(Text, nullable=False)
    domain = Column(Text, nullable=False)
    training_type = Column(Text, nullable=False)
    total_students = Column(Integer, nullable=False)
    students_per_batch = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SQLEnum(EngagementStatus, name='engagement_status', create_type=False), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", back_populates="engagements")
    batches = relationship("Batch", back_populates="engagement")

class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=False)
    batch_number = Column(Integer, nullable=False)
    students = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SQLEnum(BatchStatus, name='batch_status', create_type=False), nullable=False)
    trainer_id = Column(UUID(as_uuid=True), ForeignKey("trainers.id"))
    confirmed_at = Column(DateTime(timezone=True))
    confirmed_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    engagement = relationship("Engagement", back_populates="batches")

class HRRequest(Base):
    __tablename__ = "hr_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("engagements.id"), nullable=False)
    domain = Column(Text, nullable=False)
    trainers_needed = Column(Integer, nullable=False)
    urgency = Column(SQLEnum(UrgencyLevel, name='urgency_level', create_type=False), nullable=False)
    status = Column(SQLEnum(HRRequestStatus, name='hr_request_status', create_type=False), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    creator = relationship("User", foreign_keys=[created_by])

class Attendance(Base):
    __tablename__ = "trainer_attendance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainer_id = Column(Text, nullable=False)
    trainer_name = Column(Text, nullable=False)
    batch_id = Column(Text, nullable=False)
    project_id = Column(Text, nullable=False)
    engagement_id = Column(Text, nullable=False)
    date = Column(Date, nullable=False, server_default=func.current_date())
    status = Column(SQLEnum(AttendanceStatus, name='attendance_status', create_type=False), nullable=False, default=AttendanceStatus.pending)
    punch_in = Column(DateTime(timezone=True))
    punch_out = Column(DateTime(timezone=True))
    completion_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())