"""
Import/Export endpoints for OTOBO integration
"""

import io
import csv
import json
import xml.etree.ElementTree as ET
from typing import List
from uuid import UUID
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.asset import Asset, AssetType, AssetTypeEnum
from app.schemas.common import ExportFormat, ImportResult

router = APIRouter()


@router.post("/import/csv", response_model=ImportResult)
async def import_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Import assets from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    contents = await file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    
    # Required columns
    required_columns = ['name', 'asset_type', 'parent_name']
    if not all(col in df.columns for col in required_columns):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain columns: {required_columns}"
        )
    
    # Get asset types mapping
    result = await db.execute(select(AssetType))
    asset_types = {at.name: at for at in result.scalars().all()}
    
    imported = 0
    failed = 0
    errors = []
    
    # Process each row
    for idx, row in df.iterrows():
        try:
            # Find asset type
            asset_type = asset_types.get(row['asset_type'])
            if not asset_type:
                errors.append({
                    "row": idx + 1,
                    "error": f"Unknown asset type: {row['asset_type']}"
                })
                failed += 1
                continue
            
            # Find parent if specified
            parent_id = None
            if pd.notna(row.get('parent_name')):
                parent_result = await db.execute(
                    select(Asset).where(Asset.name == row['parent_name'])
                )
                parent = parent_result.scalar_one_or_none()
                if parent:
                    parent_id = parent.id
            
            # Create asset
            asset = Asset(
                name=row['name'],
                description=row.get('description'),
                asset_type_id=asset_type.id,
                parent_id=parent_id,
                status=row.get('status', 'active'),
                external_id=row.get('external_id'),
                external_system=row.get('external_system', 'OTOBO'),
                version=row.get('version'),
                properties=json.loads(row.get('properties', '{}')) if pd.notna(row.get('properties')) else {},
                tags=row.get('tags', '').split(',') if pd.notna(row.get('tags')) else []
            )
            asset.urn = asset.generate_urn()
            
            db.add(asset)
            imported += 1
            
        except Exception as e:
            errors.append({
                "row": idx + 1,
                "error": str(e)
            })
            failed += 1
    
    await db.commit()
    
    return ImportResult(
        success=failed == 0,
        total_records=len(df),
        imported=imported,
        failed=failed,
        errors=errors
    )


@router.post("/import/json", response_model=ImportResult)
async def import_json(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Import assets from JSON file"""
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be JSON")
    
    contents = await file.read()
    data = json.loads(contents)
    
    if not isinstance(data, list):
        data = [data]
    
    # Get asset types mapping
    result = await db.execute(select(AssetType))
    asset_types = {at.name: at for at in result.scalars().all()}
    
    imported = 0
    failed = 0
    errors = []
    
    # Create a mapping of names to IDs for parent resolution
    name_to_id = {}
    
    # First pass: create all assets without parents
    for idx, item in enumerate(data):
        try:
            asset_type = asset_types.get(item['asset_type'])
            if not asset_type:
                errors.append({
                    "index": idx,
                    "error": f"Unknown asset type: {item['asset_type']}"
                })
                failed += 1
                continue
            
            asset = Asset(
                name=item['name'],
                description=item.get('description'),
                asset_type_id=asset_type.id,
                parent_id=None,  # Set in second pass
                status=item.get('status', 'active'),
                external_id=item.get('external_id'),
                external_system=item.get('external_system', 'OTOBO'),
                version=item.get('version'),
                properties=item.get('properties', {}),
                tags=item.get('tags', [])
            )
            asset.urn = asset.generate_urn()
            
            db.add(asset)
            await db.flush()  # Get the ID
            name_to_id[asset.name] = asset.id
            imported += 1
            
        except Exception as e:
            errors.append({
                "index": idx,
                "error": str(e)
            })
            failed += 1
    
    # Second pass: set parent relationships
    for item in data:
        if item.get('parent_name') and item['name'] in name_to_id:
            parent_id = name_to_id.get(item['parent_name'])
            if parent_id:
                result = await db.execute(
                    select(Asset).where(Asset.name == item['name'])
                )
                asset = result.scalar_one_or_none()
                if asset:
                    asset.parent_id = parent_id
    
    await db.commit()
    
    return ImportResult(
        success=failed == 0,
        total_records=len(data),
        imported=imported,
        failed=failed,
        errors=errors
    )


@router.get("/export/{format}")
async def export_assets(
    format: ExportFormat,
    db: AsyncSession = Depends(get_db)
):
    """Export all assets in specified format"""
    # Get all assets with their types
    query = select(Asset).options(selectinload(Asset.asset_type), selectinload(Asset.parent))
    result = await db.execute(query)
    assets = result.scalars().all()
    
    if format == ExportFormat.CSV:
        return export_to_csv(assets)
    elif format == ExportFormat.JSON:
        return export_to_json(assets)
    elif format == ExportFormat.XML:
        return export_to_xml(assets)
    elif format == ExportFormat.EXCEL:
        return export_to_excel(assets)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")


def export_to_csv(assets: List[Asset]) -> Response:
    """Export assets to CSV format"""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            'id', 'urn', 'name', 'description', 'asset_type', 'parent_name',
            'status', 'lifecycle_stage', 'external_id', 'external_system',
            'version', 'properties', 'tags', 'created_at', 'updated_at'
        ]
    )
    writer.writeheader()
    
    for asset in assets:
        writer.writerow({
            'id': str(asset.id),
            'urn': asset.urn,
            'name': asset.name,
            'description': asset.description or '',
            'asset_type': asset.asset_type.name,
            'parent_name': asset.parent.name if asset.parent else '',
            'status': asset.status,
            'lifecycle_stage': asset.lifecycle_stage or '',
            'external_id': asset.external_id or '',
            'external_system': asset.external_system or '',
            'version': asset.version or '',
            'properties': json.dumps(asset.properties),
            'tags': ','.join(asset.tags) if asset.tags else '',
            'created_at': asset.created_at.isoformat(),
            'updated_at': asset.updated_at.isoformat()
        })
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=assets.csv"}
    )


def export_to_json(assets: List[Asset]) -> Response:
    """Export assets to JSON format"""
    data = []
    for asset in assets:
        data.append({
            'id': str(asset.id),
            'urn': asset.urn,
            'name': asset.name,
            'description': asset.description,
            'asset_type': asset.asset_type.name,
            'parent_name': asset.parent.name if asset.parent else None,
            'status': asset.status,
            'lifecycle_stage': asset.lifecycle_stage,
            'external_id': asset.external_id,
            'external_system': asset.external_system,
            'version': asset.version,
            'properties': asset.properties,
            'tags': asset.tags,
            'created_at': asset.created_at.isoformat(),
            'updated_at': asset.updated_at.isoformat()
        })
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=assets.json"}
    )


def export_to_xml(assets: List[Asset]) -> Response:
    """Export assets to XML format"""
    root = ET.Element("assets")
    
    for asset in assets:
        asset_elem = ET.SubElement(root, "asset")
        asset_elem.set("id", str(asset.id))
        asset_elem.set("urn", asset.urn)
        
        ET.SubElement(asset_elem, "name").text = asset.name
        ET.SubElement(asset_elem, "description").text = asset.description or ""
        ET.SubElement(asset_elem, "asset_type").text = asset.asset_type.name
        ET.SubElement(asset_elem, "parent_name").text = asset.parent.name if asset.parent else ""
        ET.SubElement(asset_elem, "status").text = asset.status
        ET.SubElement(asset_elem, "lifecycle_stage").text = asset.lifecycle_stage or ""
        ET.SubElement(asset_elem, "external_id").text = asset.external_id or ""
        ET.SubElement(asset_elem, "external_system").text = asset.external_system or ""
        ET.SubElement(asset_elem, "version").text = asset.version or ""
        
        # Properties
        props_elem = ET.SubElement(asset_elem, "properties")
        for key, value in (asset.properties or {}).items():
            prop_elem = ET.SubElement(props_elem, "property")
            prop_elem.set("key", key)
            prop_elem.text = str(value)
        
        # Tags
        tags_elem = ET.SubElement(asset_elem, "tags")
        for tag in (asset.tags or []):
            ET.SubElement(tags_elem, "tag").text = tag
        
        ET.SubElement(asset_elem, "created_at").text = asset.created_at.isoformat()
        ET.SubElement(asset_elem, "updated_at").text = asset.updated_at.isoformat()
    
    xml_str = ET.tostring(root, encoding='unicode', method='xml')
    
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=assets.xml"}
    )


def export_to_excel(assets: List[Asset]) -> Response:
    """Export assets to Excel format"""
    data = []
    for asset in assets:
        data.append({
            'ID': str(asset.id),
            'URN': asset.urn,
            'Name': asset.name,
            'Description': asset.description or '',
            'Asset Type': asset.asset_type.name,
            'Parent': asset.parent.name if asset.parent else '',
            'Status': asset.status,
            'Lifecycle Stage': asset.lifecycle_stage or '',
            'External ID': asset.external_id or '',
            'External System': asset.external_system or '',
            'Version': asset.version or '',
            'Properties': json.dumps(asset.properties),
            'Tags': ','.join(asset.tags) if asset.tags else '',
            'Created At': asset.created_at,
            'Updated At': asset.updated_at
        })
    
    df = pd.DataFrame(data)
    
    # Write to Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Assets', index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=assets.xlsx"}
    )