"""
Asset model with fixed asset types for BOM tracking
"""

from enum import Enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, UniqueConstraint, CheckConstraint, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class AssetTypeEnum(str, Enum):
    """Fixed asset types"""
    DOMAIN_SYSTEM_OF_SYSTEMS = "Domain / System of Systems"
    SYSTEM_ENVIRONMENT = "System / Environment"
    SUBSYSTEM = "Subsystem"
    COMPONENT_SEGMENT = "Component / Segment"
    CONFIGURATION_ITEM = "Configuration Item (CI)"
    HARDWARE_CI = "Hardware CI"
    SOFTWARE_CI = "Software CI"
    FIRMWARE_CI = "Firmware CI"


class AssetType(BaseModel):
    """Asset type definitions (pre-populated, read-only)"""
    
    __tablename__ = "asset_types"
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    level = Column(Integer, nullable=False)  # Hierarchy level (1=highest)
    can_have_bom = Column(Integer, default=1)  # Boolean flag
    
    # Relationships
    assets = relationship("Asset", back_populates="asset_type")


class Asset(BaseModel):
    """Core asset model with hierarchical structure"""
    
    __tablename__ = "assets"
    
    # Unique identifiers
    urn = Column(String(255), unique=True, nullable=False)  # e.g., "urn:assetdna:sys:web-server-01"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Asset type (foreign key to fixed types)
    asset_type_id = Column(UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=False)
    
    # Hierarchical relationship
    parent_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=True)
    
    # Additional metadata
    properties = Column(JSON, default={})  # Flexible JSON properties
    tags = Column(JSON, default=[])  # Array of tags
    
    # Status and lifecycle
    status = Column(String(50), default="active")  # active, inactive, deprecated
    lifecycle_stage = Column(String(50), nullable=True)  # development, production, maintenance, retired
    
    # External references
    external_id = Column(String(255), nullable=True)  # ID in external system (e.g., OTOBO)
    external_system = Column(String(100), nullable=True)  # Name of external system
    
    # Versioning
    version = Column(String(50), nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'parent_id', name='uq_asset_name_parent'),
        CheckConstraint("status IN ('active', 'inactive', 'deprecated')", name='ck_asset_status'),
    )
    
    # Relationships
    asset_type = relationship("AssetType", back_populates="assets")
    parent = relationship("Asset", remote_side="Asset.id", backref="children")
    bom_history = relationship("BOMHistory", back_populates="asset", cascade="all, delete-orphan")
    
    def get_full_path(self):
        """Get the full hierarchical path of the asset"""
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return " / ".join(path)
    
    def generate_urn(self):
        """Generate URN based on asset type and name"""
        from app.core.config import settings
        type_map = {
            AssetTypeEnum.DOMAIN_SYSTEM_OF_SYSTEMS: "domain",
            AssetTypeEnum.SYSTEM_ENVIRONMENT: "sys",
            AssetTypeEnum.SUBSYSTEM: "subsys",
            AssetTypeEnum.COMPONENT_SEGMENT: "comp",
            AssetTypeEnum.CONFIGURATION_ITEM: "ci",
            AssetTypeEnum.HARDWARE_CI: "hw",
            AssetTypeEnum.SOFTWARE_CI: "sw",
            AssetTypeEnum.FIRMWARE_CI: "fw"
        }
        type_code = type_map.get(self.asset_type.name, "asset")
        safe_name = self.name.lower().replace(" ", "-").replace("/", "-")
        return f"{settings.URN_PREFIX}:{type_code}:{safe_name}"