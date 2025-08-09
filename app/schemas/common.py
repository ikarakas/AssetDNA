"""
Common schemas used across the application
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    """Supported export formats"""
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    EXCEL = "excel"


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=1000)
    sort_by: Optional[str] = None
    sort_desc: bool = False


class ImportResult(BaseModel):
    """Result of an import operation"""
    success: bool
    total_records: int
    imported: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class BulkOperationResult(BaseModel):
    """Result of a bulk operation"""
    success: bool
    total: int
    processed: int
    failed: int
    results: List[Dict[str, Any]] = Field(default_factory=list)