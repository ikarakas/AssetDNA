"""
Asset operations endpoints (copy, move, etc.)
"""

from typing import Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.asset import Asset, AssetType

import re


class MoveAssetRequest(BaseModel):
    new_parent_id: Optional[UUID] = None


class CopyAssetRequest(BaseModel):
    new_parent_id: Optional[UUID] = None


router = APIRouter()


@router.get("/assets/summary")
async def get_asset_summary(db: AsyncSession = Depends(get_db)):
    """
    Get summary statistics for all assets grouped by type, including BOM information
    """
    from sqlalchemy import func, case, distinct
    from app.models.bom import BOMHistory
    
    # Query to get counts by asset type and status, including BOM counts
    result = await db.execute(
        select(
            AssetType.name.label('type_name'),
            func.count(distinct(Asset.id)).label('total'),
            func.sum(case((Asset.status == 'active', 1), else_=0)).label('active'),
            func.sum(case((Asset.status != 'active', 1), else_=0)).label('inactive'),
            func.count(distinct(BOMHistory.asset_id)).label('with_bom')
        )
        .join(Asset, Asset.asset_type_id == AssetType.id)
        .outerjoin(BOMHistory, BOMHistory.asset_id == Asset.id)
        .group_by(AssetType.name)
        .order_by(func.count(distinct(Asset.id)).desc())
    )
    
    type_summary = result.all()
    
    # Get total counts
    total_result = await db.execute(
        select(
            func.count(distinct(Asset.id)).label('total'),
            func.sum(case((Asset.status == 'active', 1), else_=0)).label('active'),
            func.sum(case((Asset.status != 'active', 1), else_=0)).label('inactive')
        ).select_from(Asset)
    )
    
    totals = total_result.first()
    
    # Get BOM statistics
    bom_result = await db.execute(
        select(
            func.count(distinct(BOMHistory.id)).label('total_boms'),
            func.count(distinct(BOMHistory.asset_id)).label('assets_with_bom')
        ).select_from(BOMHistory)
    )
    
    bom_stats = bom_result.first()
    
    # Get BOM count by asset type
    bom_by_type_result = await db.execute(
        select(
            AssetType.name.label('type_name'),
            func.count(distinct(BOMHistory.id)).label('bom_count'),
            func.count(distinct(BOMHistory.asset_id)).label('assets_with_bom')
        )
        .join(Asset, Asset.asset_type_id == AssetType.id)
        .join(BOMHistory, BOMHistory.asset_id == Asset.id)
        .group_by(AssetType.name)
        .order_by(func.count(distinct(BOMHistory.id)).desc())
    )
    
    bom_by_type = bom_by_type_result.all()
    
    return {
        "total_assets": totals.total or 0,
        "active_assets": totals.active or 0,
        "inactive_assets": totals.inactive or 0,
        "total_boms": bom_stats.total_boms or 0,
        "assets_with_bom": bom_stats.assets_with_bom or 0,
        "assets_without_bom": (totals.total or 0) - (bom_stats.assets_with_bom or 0),
        "by_type": [
            {
                "type": row.type_name,
                "total": row.total,
                "active": row.active or 0,
                "inactive": row.inactive or 0,
                "with_bom": row.with_bom or 0,
                "percentage": round((row.total / totals.total * 100), 1) if totals.total > 0 else 0,
                "bom_percentage": round((row.with_bom / row.total * 100), 1) if row.total > 0 else 0
            }
            for row in type_summary
        ],
        "bom_by_type": [
            {
                "type": row.type_name,
                "bom_count": row.bom_count,
                "assets_with_bom": row.assets_with_bom
            }
            for row in bom_by_type
        ]
    }


async def deep_copy_asset(
    asset: Asset,
    new_parent_id: Optional[UUID],
    db: AsyncSession,
    name_suffix: str = " (Copy)"
) -> Asset:
    """Recursively copy an asset and all its children
    
    Note: BOMs are NOT copied as they are specific to the original asset
    and should be independently managed for each asset instance.
    """
    
    # Load the asset type if not already loaded
    if not asset.asset_type:
        type_result = await db.execute(
            select(AssetType).where(AssetType.id == asset.asset_type_id)
        )
        asset_type = type_result.scalar_one_or_none()
    else:
        asset_type = asset.asset_type
    
    # Create a copy of the asset with a unique name if copying to same parent
    copied_name = asset.name + name_suffix if new_parent_id == asset.parent_id else asset.name
    
    # Check if an asset with this name already exists under the parent
    # and add a number suffix if needed
    existing_check = await db.execute(
        select(Asset).where(
            Asset.parent_id == new_parent_id,
            Asset.name == copied_name
        )
    )
    if existing_check.scalar_one_or_none():
        # Find a unique name by adding a number
        counter = 2
        while True:
            test_name = f"{copied_name} ({counter})"
            check = await db.execute(
                select(Asset).where(
                    Asset.parent_id == new_parent_id,
                    Asset.name == test_name
                )
            )
            if not check.scalar_one_or_none():
                copied_name = test_name
                break
            counter += 1
    
    new_asset = Asset(
        id=uuid4(),
        name=copied_name,
        description=asset.description,
        asset_type_id=asset.asset_type_id,
        parent_id=new_parent_id,
        properties=asset.properties.copy() if asset.properties else {},
        tags=asset.tags.copy() if asset.tags else [],
        status=asset.status,
        lifecycle_stage=asset.lifecycle_stage,
        external_id=None,  # Reset external ID for copy
        external_system=asset.external_system,
        version=asset.version,
        created_by=asset.created_by,
        updated_by=asset.updated_by
    )
    
    # Set the asset type for URN generation
    new_asset.asset_type = asset_type
    
    # Generate URN for the new asset - it will be unique because the name is unique
    # or we add the UUID to ensure uniqueness
    base_urn = new_asset.generate_urn()
    
    # Check if URN already exists and make it unique if needed
    urn_check = await db.execute(
        select(Asset).where(Asset.urn == base_urn)
    )
    if urn_check.scalar_one_or_none():
        # Add a unique identifier to the URN
        import uuid
        new_asset.urn = f"{base_urn}-{str(uuid.uuid4())[:8]}"
    else:
        new_asset.urn = base_urn
    
    # Add to session
    db.add(new_asset)
    await db.flush()  # Get the ID for the new asset
    
    # NOTE: We intentionally do NOT copy BOMs (Bill of Materials)
    # BOMs are specific to each asset instance and should be managed independently
    # This ensures that copied assets start with a clean BOM history
    
    # Copy all children recursively
    children_result = await db.execute(
        select(Asset).where(Asset.parent_id == asset.id).options(selectinload(Asset.asset_type))
    )
    children = children_result.scalars().all()
    
    for child in children:
        await deep_copy_asset(
            child,
            new_asset.id,
            db,
            name_suffix=""  # Don't add suffix to children
        )
    
    return new_asset


@router.post("/assets/{asset_id}/copy")
async def copy_asset(
    asset_id: UUID,
    request: CopyAssetRequest,
    db: AsyncSession = Depends(get_db)
):
    """Copy an asset and all its children to a new parent
    
    Creates a deep copy of the asset including:
    - All asset properties and metadata
    - All child assets recursively
    
    Does NOT copy:
    - BOMs (Bill of Materials) - these remain with the original asset only
    - External IDs - reset to allow new external associations
    """
    
    new_parent_id = request.new_parent_id
    
    # Get the asset to copy
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id).options(selectinload(Asset.asset_type))
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Verify new parent exists if specified
    if new_parent_id:
        parent_result = await db.execute(select(Asset).where(Asset.id == new_parent_id))
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent asset not found")
        
        # Check for circular reference (can't copy to own descendant)
        async def is_descendant(potential_parent_id: UUID, potential_child_id: UUID) -> bool:
            if potential_parent_id == potential_child_id:
                return True
            
            children_result = await db.execute(
                select(Asset.id).where(Asset.parent_id == potential_child_id)
            )
            children_ids = children_result.scalars().all()
            
            for child_id in children_ids:
                if await is_descendant(potential_parent_id, child_id):
                    return True
            return False
        
        if await is_descendant(new_parent_id, asset_id):
            raise HTTPException(
                status_code=400,
                detail="Cannot copy an asset to its own descendant"
            )
    
    # Perform the deep copy
    new_asset = await deep_copy_asset(asset, new_parent_id, db)
    
    await db.commit()
    await db.refresh(new_asset, ["asset_type"])
    
    return {
        "id": new_asset.id,
        "name": new_asset.name,
        "message": f"Asset '{asset.name}' and its children have been copied successfully"
    }


@router.put("/assets/{asset_id}/move")
async def move_asset(
    asset_id: UUID,
    request: MoveAssetRequest,
    db: AsyncSession = Depends(get_db)
):
    """Move an asset to a new parent"""
    
    new_parent_id = request.new_parent_id
    
    # Get the asset
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Verify new parent exists if specified
    if new_parent_id:
        parent_result = await db.execute(select(Asset).where(Asset.id == new_parent_id))
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent asset not found")
        
        # Check for circular reference
        async def is_descendant(potential_parent_id: UUID, potential_child_id: UUID) -> bool:
            if potential_parent_id == potential_child_id:
                return True
            
            children_result = await db.execute(
                select(Asset.id).where(Asset.parent_id == potential_child_id)
            )
            children_ids = children_result.scalars().all()
            
            for child_id in children_ids:
                if await is_descendant(potential_parent_id, child_id):
                    return True
            return False
        
        if await is_descendant(new_parent_id, asset_id):
            raise HTTPException(
                status_code=400,
                detail="Cannot move an asset to its own descendant"
            )
    
    # Check if an asset with the same name already exists under the new parent
    if new_parent_id != asset.parent_id:  # Only check if actually moving
        name_check = await db.execute(
            select(Asset).where(
                Asset.parent_id == new_parent_id,
                Asset.name == asset.name
            )
        )
        if name_check.scalar_one_or_none():
            # Find a unique name by adding a number suffix
            base_name = asset.name
            counter = 1
            
            # Check if the name already has a number suffix pattern
            match = re.match(r'^(.*?)\s*\((\d+)\)$', base_name)
            if match:
                # Extract base name without the number
                base_name = match.group(1).strip()
                counter = int(match.group(2)) + 1
            
            # Find the next available unique name
            while counter <= 1000:  # Prevent infinite loops
                new_name = f"{base_name} ({counter})"
                check = await db.execute(
                    select(Asset).where(
                        Asset.parent_id == new_parent_id,
                        Asset.name == new_name
                    )
                )
                if not check.scalar_one_or_none():
                    asset.name = new_name
                    break
                counter += 1
            else:
                # If we can't find a unique name after 1000 attempts, use timestamp
                import time
                timestamp = int(time.time())
                asset.name = f"{base_name} ({timestamp})"
    
    # Update the parent
    asset.parent_id = new_parent_id
    
    await db.commit()
    
    return {
        "id": asset.id,
        "name": asset.name,
        "message": f"Asset '{asset.name}' has been moved successfully"
    }