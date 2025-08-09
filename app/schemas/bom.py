"""
BOM schemas for validation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class BOMItemBase(BaseModel):
    """Base BOM item schema"""
    component_id: str
    component_name: str
    component_type: Optional[str] = None
    version: Optional[str] = None
    version_range: Optional[str] = None
    supplier: Optional[str] = None
    license: Optional[str] = None
    license_url: Optional[str] = None
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list)
    risk_score: Optional[float] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)


class BOMItemResponse(BOMItemBase):
    """BOM item response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    bom_history_id: UUID
    created_at: datetime


class BOMHistoryBase(BaseModel):
    """Base BOM history schema"""
    asset_id: UUID
    bom_version: str
    bom_date: datetime = Field(default_factory=datetime.utcnow)
    bom_type: str = Field(default="SBOM")
    bom_data: Dict[str, Any]
    bom_format: str = Field(default="CycloneDX")
    source: Optional[str] = None
    import_method: Optional[str] = None


class BOMHistoryCreate(BOMHistoryBase):
    """BOM history creation schema"""
    items: List[BOMItemBase] = Field(default_factory=list)


class BOMHistoryResponse(BaseModel):
    """BOM history response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    asset_id: UUID
    bom_version: str
    bom_date: datetime
    bom_type: str
    bom_data: Dict[str, Any]
    bom_format: str
    total_components: int
    total_vulnerabilities: int
    total_licenses: int
    change_summary: Optional[str] = None
    components_added: int
    components_removed: int
    components_updated: int
    source: Optional[str] = None
    import_method: Optional[str] = None
    is_valid: bool
    validation_errors: Optional[List[str]] = None
    created_at: datetime
    created_by: Optional[str] = None


class BOMChangeReport(BaseModel):
    """BOM change analysis report"""
    asset_id: UUID
    asset_name: str
    asset_urn: str
    period_start: datetime
    period_end: datetime
    total_bom_versions: int
    
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Summary statistics
    total_components_added: int = 0
    total_components_removed: int = 0
    total_components_updated: int = 0
    
    # Vulnerability trends
    vulnerability_trend: List[Dict[str, Any]] = Field(default_factory=list)
    
    # License changes
    license_changes: List[Dict[str, Any]] = Field(default_factory=list)