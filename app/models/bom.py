"""
BOM (Bill of Materials) history tracking models
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, Float, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class BOMHistory(BaseModel):
    """Historical snapshots of BOMs for assets"""
    
    __tablename__ = "bom_history"
    
    # Link to asset
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    
    # BOM metadata
    bom_version = Column(String(50), nullable=False)
    bom_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    bom_type = Column(String(50), default="SBOM")  # SBOM, HBOM, etc.
    
    # Snapshot data
    bom_data = Column(JSON, nullable=False)  # Complete BOM in JSON format
    bom_format = Column(String(50), default="CycloneDX")  # CycloneDX, SPDX, custom
    
    # Statistics
    total_components = Column(Integer, default=0)
    total_vulnerabilities = Column(Integer, default=0)
    total_licenses = Column(Integer, default=0)
    
    # Change tracking
    change_summary = Column(Text, nullable=True)  # Summary of changes from previous version
    components_added = Column(Integer, default=0)
    components_removed = Column(Integer, default=0)
    components_updated = Column(Integer, default=0)
    
    # Source information
    source = Column(String(100), nullable=True)  # Where this BOM came from
    import_method = Column(String(50), nullable=True)  # manual, api, file_upload
    
    # Validation
    is_valid = Column(Integer, default=1)  # Boolean flag
    validation_errors = Column(JSON, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_bom_history_asset_date', 'asset_id', 'bom_date'),
        Index('idx_bom_history_asset_version', 'asset_id', 'bom_version'),
    )
    
    # Relationships
    asset = relationship("Asset", back_populates="bom_history")
    bom_items = relationship("BOMItem", back_populates="bom_history", cascade="all, delete-orphan")
    
    def calculate_changes(self, previous_bom):
        """Calculate changes from a previous BOM"""
        if not previous_bom:
            return {
                "added": self.total_components,
                "removed": 0,
                "updated": 0
            }
        
        # Compare component lists
        current_components = set(item.component_id for item in self.bom_items)
        previous_components = set(item.component_id for item in previous_bom.bom_items)
        
        added = current_components - previous_components
        removed = previous_components - current_components
        
        # Check for updates (same component, different version)
        common = current_components & previous_components
        updated = 0
        for comp_id in common:
            current_item = next(i for i in self.bom_items if i.component_id == comp_id)
            previous_item = next(i for i in previous_bom.bom_items if i.component_id == comp_id)
            if current_item.version != previous_item.version:
                updated += 1
        
        return {
            "added": len(added),
            "removed": len(removed),
            "updated": updated
        }


class BOMItem(BaseModel):
    """Individual items/components within a BOM"""
    
    __tablename__ = "bom_items"
    
    # Link to BOM history
    bom_history_id = Column(UUID(as_uuid=True), ForeignKey("bom_history.id", ondelete="CASCADE"), nullable=False)
    
    # Component information
    component_id = Column(String(255), nullable=False)  # Unique ID within BOM
    component_name = Column(String(255), nullable=False)
    component_type = Column(String(100), nullable=True)  # library, framework, application, etc.
    
    # Version information
    version = Column(String(100), nullable=True)
    version_range = Column(String(100), nullable=True)
    
    # Source and licensing
    supplier = Column(String(255), nullable=True)
    license = Column(String(100), nullable=True)
    license_url = Column(String(500), nullable=True)
    
    # Security information
    vulnerabilities = Column(JSON, default=[])  # List of known vulnerabilities
    risk_score = Column(Float, nullable=True)
    
    # Additional metadata
    properties = Column(JSON, default={})
    dependencies = Column(JSON, default=[])  # List of dependencies
    
    # Relationships
    bom_history = relationship("BOMHistory", back_populates="bom_items")
    
    # Indexes
    __table_args__ = (
        Index('idx_bom_item_history_component', 'bom_history_id', 'component_id'),
        Index('idx_bom_item_component_name', 'component_name'),
    )