"""
Asset schemas for validation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class AssetTypeResponse(BaseModel):
    """Asset type response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    level: int
    can_have_bom: bool


class AssetBase(BaseModel):
    """Base asset schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type_id: UUID
    parent_id: Optional[UUID] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    status: str = Field(default="active", pattern="^(active|inactive|deprecated)$")
    lifecycle_stage: Optional[str] = None
    external_id: Optional[str] = None
    external_system: Optional[str] = None
    version: Optional[str] = None


class AssetCreate(AssetBase):
    """Asset creation schema"""
    pass


class AssetUpdate(BaseModel):
    """Asset update schema (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    properties: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|deprecated)$")
    lifecycle_stage: Optional[str] = None
    external_id: Optional[str] = None
    external_system: Optional[str] = None
    version: Optional[str] = None


class AssetResponse(BaseModel):
    """Asset response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    urn: str
    name: str
    description: Optional[str] = None
    asset_type: AssetTypeResponse
    parent_id: Optional[UUID] = None
    properties: Dict[str, Any]
    tags: List[str]
    status: str
    lifecycle_stage: Optional[str] = None
    external_id: Optional[str] = None
    external_system: Optional[str] = None
    version: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class AssetTreeResponse(AssetResponse):
    """Asset with children for tree representation"""
    children: List['AssetTreeResponse'] = Field(default_factory=list)
    bom_count: int = 0


# Update forward references
AssetTreeResponse.model_rebuild()