from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class ErrorLog(Base):
    __tablename__ = "error_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    error_id = Column(String(50))
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    component = Column(String(100))
    severity = Column(String(50))
    function_name = Column(String(200))
    
    # Audit columns
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True))
    modified_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    modified_by = Column(UUID(as_uuid=True))