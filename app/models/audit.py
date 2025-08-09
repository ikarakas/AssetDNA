"""
Audit log model for tracking all changes
"""

from sqlalchemy import Column, String, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Audit trail for all system changes"""
    
    __tablename__ = "audit_logs"
    
    # What was changed
    entity_type = Column(String(100), nullable=False)  # asset, bom, user, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # What action was taken
    action = Column(String(50), nullable=False)  # create, update, delete, import, export
    
    # Change details
    old_values = Column(JSON, nullable=True)  # Previous state
    new_values = Column(JSON, nullable=True)  # New state
    change_summary = Column(Text, nullable=True)
    
    # Who made the change
    user_id = Column(String(100), nullable=True)
    user_name = Column(String(255), nullable=True)
    user_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Additional context
    extra_data = Column(JSON, default={})  # Any additional information