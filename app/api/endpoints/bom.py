"""
BOM management endpoints
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
import json

from app.core.database import get_db
from app.models.bom import BOMHistory, BOMItem
from app.models.asset import Asset

router = APIRouter()


@router.post("/assets/{asset_id}/bom/upload")
async def upload_bom(
    asset_id: UUID,
    file: UploadFile = File(...),
    version: str = Form(...),
    bom_type: str = Form(default="SBOM"),
    source: str = Form(default="Manual Upload"),
    db: AsyncSession = Depends(get_db)
):
    """Upload a BOM file for an asset"""
    
    # Verify asset exists
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check if asset has children (only leaf nodes can have BOMs)
    children_result = await db.execute(
        select(Asset).where(Asset.parent_id == asset_id).limit(1)
    )
    if children_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="BOMs can only be uploaded for leaf-level assets. This asset has child assets."
        )
    
    # Read and parse file
    content = await file.read()
    try:
        if file.filename.endswith('.json'):
            bom_data = json.loads(content)
        else:
            raise HTTPException(status_code=400, detail="Currently only JSON format is supported")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")
    
    # Determine format
    bom_format = "unknown"
    if "bomFormat" in bom_data and "specVersion" in bom_data:
        bom_format = "CycloneDX"
    elif "spdxVersion" in bom_data:
        bom_format = "SPDX"
    else:
        bom_format = "custom"
    
    # Extract components based on format
    components = []
    if bom_format == "CycloneDX":
        components = bom_data.get("components", [])
    elif bom_format == "SPDX":
        components = bom_data.get("packages", [])
    else:
        # Try to find components in custom format
        if "components" in bom_data:
            components = bom_data["components"]
        elif "packages" in bom_data:
            components = bom_data["packages"]
        elif "items" in bom_data:
            components = bom_data["items"]
    
    # Create BOM history entry
    bom_history = BOMHistory(
        asset_id=asset_id,
        bom_version=version,
        bom_date=datetime.utcnow(),
        bom_type=bom_type,
        bom_data=bom_data,
        bom_format=bom_format,
        total_components=len(components),
        source=source,
        import_method="file_upload",
        is_valid=1
    )
    
    db.add(bom_history)
    await db.flush()  # Get the ID for BOM items
    
    # Process components and create BOM items
    bom_items = []
    for comp in components:
        # Extract component details based on format
        if bom_format == "CycloneDX":
            comp_id = comp.get("bom-ref", comp.get("name", "unknown"))
            comp_name = comp.get("name", "Unknown Component")
            comp_version = comp.get("version", "")
            comp_type = comp.get("type", "library")
            comp_license = ""
            if "licenses" in comp and comp["licenses"]:
                comp_license = comp["licenses"][0].get("license", {}).get("id", "")
        elif bom_format == "SPDX":
            comp_id = comp.get("SPDXID", comp.get("name", "unknown"))
            comp_name = comp.get("name", "Unknown Component")
            comp_version = comp.get("versionInfo", "")
            comp_type = "package"
            comp_license = comp.get("licenseConcluded", "")
        else:
            # Custom format - best effort extraction
            comp_id = comp.get("id", comp.get("name", f"comp_{components.index(comp)}"))
            comp_name = comp.get("name", comp.get("title", "Unknown Component"))
            comp_version = comp.get("version", comp.get("ver", ""))
            comp_type = comp.get("type", "component")
            comp_license = comp.get("license", "")
        
        bom_item = BOMItem(
            bom_history_id=bom_history.id,
            component_id=comp_id,
            component_name=comp_name,
            component_type=comp_type,
            version=comp_version,
            license=comp_license,
            properties=comp  # Store full component data
        )
        db.add(bom_item)
        bom_items.append(bom_item)
    
    # Calculate statistics
    unique_licenses = set(item.license for item in bom_items if item.license)
    bom_history.total_licenses = len(unique_licenses)
    
    await db.commit()
    await db.refresh(bom_history)
    
    return {
        "id": bom_history.id,
        "asset_id": asset_id,
        "bom_version": bom_history.bom_version,
        "bom_format": bom_history.bom_format,
        "total_components": bom_history.total_components,
        "message": f"BOM uploaded successfully with {bom_history.total_components} components"
    }


@router.get("/assets/{asset_id}/bom/history")
async def get_bom_history(
    asset_id: UUID,
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get BOM history for an asset"""
    
    # Verify asset exists
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get BOM history
    query = select(BOMHistory).where(
        BOMHistory.asset_id == asset_id
    ).order_by(desc(BOMHistory.bom_date)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    bom_histories = result.scalars().all()
    
    return [
        {
            "id": bom.id,
            "version": bom.bom_version,
            "date": bom.bom_date,
            "type": bom.bom_type,
            "format": bom.bom_format,
            "total_components": bom.total_components,
            "source": bom.source,
            "components_added": bom.components_added,
            "components_removed": bom.components_removed,
            "components_updated": bom.components_updated
        }
        for bom in bom_histories
    ]


@router.get("/assets/{asset_id}/bom/{bom_id}")
async def get_bom_details(
    asset_id: UUID,
    bom_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed BOM information"""
    
    query = select(BOMHistory).where(
        BOMHistory.id == bom_id,
        BOMHistory.asset_id == asset_id
    ).options(selectinload(BOMHistory.bom_items))
    
    result = await db.execute(query)
    bom = result.scalar_one_or_none()
    
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    return {
        "id": bom.id,
        "version": bom.bom_version,
        "date": bom.bom_date,
        "type": bom.bom_type,
        "format": bom.bom_format,
        "total_components": bom.total_components,
        "source": bom.source,
        "bom_data": bom.bom_data,
        "components": [
            {
                "id": item.component_id,
                "name": item.component_name,
                "type": item.component_type,
                "version": item.version,
                "license": item.license
            }
            for item in bom.bom_items
        ]
    }


@router.delete("/assets/{asset_id}/bom/{bom_id}")
async def delete_bom(
    asset_id: UUID,
    bom_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a BOM history entry"""
    
    query = select(BOMHistory).where(
        BOMHistory.id == bom_id,
        BOMHistory.asset_id == asset_id
    )
    
    result = await db.execute(query)
    bom = result.scalar_one_or_none()
    
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    await db.delete(bom)
    await db.commit()
    
    return {"message": "BOM deleted successfully"}