"""
Asset management endpoints
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.asset import Asset, AssetType
from app.schemas.asset import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetTreeResponse,
    AssetTypeResponse
)
from app.schemas.common import PaginationParams

router = APIRouter()


@router.get("/types", response_model=List[AssetTypeResponse])
async def get_asset_types(db: AsyncSession = Depends(get_db)):
    """Get all available asset types"""
    result = await db.execute(select(AssetType).order_by(AssetType.level, AssetType.name))
    return result.scalars().all()


@router.get("/tree", response_model=List[AssetTreeResponse])
async def get_asset_tree(
    parent_id: Optional[UUID] = None,
    max_depth: int = Query(default=5, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Get hierarchical asset tree"""
    
    async def build_tree(parent_id: Optional[UUID], depth: int = 0):
        if depth >= max_depth:
            return []
        
        query = select(Asset).where(Asset.parent_id == parent_id)
        query = query.options(selectinload(Asset.asset_type))
        query = query.order_by(Asset.name)  # Sort alphabetically
        result = await db.execute(query)
        assets = result.scalars().all()
        
        tree = []
        uncategorized_items = []
        
        for asset in assets:
            # Count BOMs for this asset
            from sqlalchemy import func
            from app.models.bom import BOMHistory
            bom_count_result = await db.execute(
                select(func.count(BOMHistory.id)).where(BOMHistory.asset_id == asset.id)
            )
            bom_count = bom_count_result.scalar() or 0
            
            # Convert asset to dict manually to avoid async issues
            asset_dict = {
                "id": asset.id,
                "urn": asset.urn,
                "name": asset.name,
                "description": asset.description,
                "asset_type": {
                    "id": asset.asset_type.id,
                    "name": asset.asset_type.name,
                    "description": asset.asset_type.description,
                    "level": asset.asset_type.level,
                    "can_have_bom": bool(asset.asset_type.can_have_bom)
                },
                "parent_id": asset.parent_id,
                "properties": asset.properties,
                "tags": asset.tags,
                "status": asset.status,
                "lifecycle_stage": asset.lifecycle_stage,
                "external_id": asset.external_id,
                "external_system": asset.external_system,
                "version": asset.version,
                "created_at": asset.created_at,
                "updated_at": asset.updated_at,
                "created_by": asset.created_by,
                "updated_by": asset.updated_by,
                "bom_count": bom_count,
                "children": await build_tree(asset.id, depth + 1)
            }
            
            # Sort Uncategorized items to the end
            if asset.name.lower() == "uncategorized":
                uncategorized_items.append(asset_dict)
            else:
                tree.append(asset_dict)
        
        # Add uncategorized items at the end
        tree.extend(uncategorized_items)
        
        return tree
    
    return await build_tree(parent_id)


@router.get("")
async def get_assets(
    pagination: PaginationParams = Depends(),
    parent_id: Optional[UUID] = None,
    asset_type_id: Optional[UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get assets with filtering and pagination"""
    query = select(Asset).options(selectinload(Asset.asset_type))
    
    # Apply filters
    if parent_id is not None:
        query = query.where(Asset.parent_id == parent_id)
    if asset_type_id:
        query = query.where(Asset.asset_type_id == asset_type_id)
    if status:
        query = query.where(Asset.status == status)
    if search:
        query = query.where(Asset.name.ilike(f"%{search}%"))
    
    # Apply sorting
    if pagination.sort_by:
        order_column = getattr(Asset, pagination.sort_by, Asset.name)
        query = query.order_by(order_column.desc() if pagination.sort_desc else order_column)
    else:
        query = query.order_by(Asset.name)
    
    # Apply pagination
    offset = (pagination.page - 1) * pagination.page_size
    query = query.offset(offset).limit(pagination.page_size)
    
    result = await db.execute(query)
    assets = result.scalars().all()
    
    # Add BOM count for each asset
    assets_with_bom_count = []
    for asset in assets:
        # Count BOMs for this asset
        from sqlalchemy import func
        from app.models.bom import BOMHistory
        bom_count_result = await db.execute(
            select(func.count(BOMHistory.id)).where(BOMHistory.asset_id == asset.id)
        )
        bom_count = bom_count_result.scalar() or 0
        
        # Convert to dict and add bom_count
        asset_dict = {
            "id": asset.id,
            "urn": asset.urn,
            "name": asset.name,
            "description": asset.description,
            "asset_type": asset.asset_type,
            "asset_type_id": asset.asset_type_id,
            "parent_id": asset.parent_id,
            "properties": asset.properties,
            "tags": asset.tags,
            "status": asset.status,
            "lifecycle_stage": asset.lifecycle_stage,
            "external_id": asset.external_id,
            "external_system": asset.external_system,
            "version": asset.version,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
            "created_by": asset.created_by,
            "updated_by": asset.updated_by,
            "bom_count": bom_count
        }
        assets_with_bom_count.append(asset_dict)
    
    return assets_with_bom_count


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific asset by ID"""
    query = select(Asset).where(Asset.id == asset_id)
    query = query.options(selectinload(Asset.asset_type))
    result = await db.execute(query)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return asset


@router.post("", response_model=AssetResponse)
async def create_asset(
    asset_data: AssetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new asset"""
    # Verify asset type exists
    result = await db.execute(select(AssetType).where(AssetType.id == asset_data.asset_type_id))
    asset_type = result.scalar_one_or_none()
    if not asset_type:
        raise HTTPException(status_code=400, detail="Invalid asset type")
    
    # Verify parent exists if specified
    if asset_data.parent_id:
        result = await db.execute(select(Asset).where(Asset.id == asset_data.parent_id))
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent asset not found")
    
    # Create asset
    asset = Asset(**asset_data.model_dump())
    asset.asset_type = asset_type
    asset.urn = asset.generate_urn()
    
    db.add(asset)
    await db.commit()
    await db.refresh(asset, ["asset_type"])
    
    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    asset_data: AssetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing asset"""
    # Get existing asset with asset_type loaded
    query = select(Asset).where(Asset.id == asset_id).options(selectinload(Asset.asset_type))
    result = await db.execute(query)
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Update fields
    update_data = asset_data.model_dump(exclude_unset=True)
    
    # If asset_type_id is being updated, load the new asset type
    if "asset_type_id" in update_data and update_data["asset_type_id"]:
        result = await db.execute(select(AssetType).where(AssetType.id == update_data["asset_type_id"]))
        new_asset_type = result.scalar_one_or_none()
        if not new_asset_type:
            raise HTTPException(status_code=400, detail="Invalid asset type")
        asset.asset_type = new_asset_type
        asset.asset_type_id = update_data["asset_type_id"]
        # Remove from update_data to avoid setting it again
        del update_data["asset_type_id"]
    
    # Update other fields
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    # Regenerate URN if name or asset type changed
    if "name" in update_data or "asset_type_id" in asset_data.model_dump(exclude_unset=True):
        # Generate URN manually to avoid async issues
        type_map = {
            "Domain / System of Systems": "domain",
            "System / Environment": "sys",
            "Subsystem": "subsys",
            "Component / Segment": "comp",
            "Configuration Item (CI)": "ci",
            "Hardware CI": "hw",
            "Software CI": "sw",
            "Firmware CI": "fw"
        }
        from app.core.config import settings
        type_code = type_map.get(asset.asset_type.name, "asset")
        safe_name = asset.name.lower().replace(" ", "-").replace("/", "-")
        asset.urn = f"{settings.URN_PREFIX}:{type_code}:{safe_name}"
    
    await db.commit()
    await db.refresh(asset, ["asset_type"])
    
    return asset


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: UUID,
    cascade: bool = Query(default=False, description="Delete child assets"),
    db: AsyncSession = Depends(get_db)
):
    """Delete an asset"""
    # Get asset
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check for children
    if not cascade:
        children_result = await db.execute(
            select(Asset).where(Asset.parent_id == asset_id).limit(1)
        )
        if children_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Asset has children. Use cascade=true to delete all children."
            )
    
    # Delete asset (cascade will handle children due to FK constraint)
    await db.delete(asset)
    await db.commit()
    
    return {"message": "Asset deleted successfully"}