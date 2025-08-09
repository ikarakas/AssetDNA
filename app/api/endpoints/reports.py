"""
Reporting endpoints for change analysis
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.bom import BOMHistory, BOMItem
from app.models.asset import Asset
from app.schemas.bom import BOMChangeReport

router = APIRouter()


@router.get("/assets/{asset_id}/changes", response_model=BOMChangeReport)
async def get_change_report(
    asset_id: UUID,
    months: int = Query(default=6, ge=1, le=24),
    db: AsyncSession = Depends(get_db)
):
    """Generate a change analysis report for an asset over specified months"""
    
    # Get asset details
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id).options(selectinload(Asset.asset_type))
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Calculate date range
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=months * 30)
    
    # Get BOM history in the period
    query = select(BOMHistory).where(
        and_(
            BOMHistory.asset_id == asset_id,
            BOMHistory.bom_date >= period_start,
            BOMHistory.bom_date <= period_end
        )
    ).order_by(BOMHistory.bom_date)
    
    result = await db.execute(query)
    bom_history = result.scalars().all()
    
    # Build change report
    report = BOMChangeReport(
        asset_id=asset_id,
        asset_name=asset.name,
        asset_urn=asset.urn,
        period_start=period_start,
        period_end=period_end,
        total_bom_versions=len(bom_history)
    )
    
    # Calculate changes
    total_added = 0
    total_removed = 0
    total_updated = 0
    vulnerability_trend = []
    
    for i, bom in enumerate(bom_history):
        change_entry = {
            "date": bom.bom_date.isoformat(),
            "version": bom.bom_version,
            "total_components": bom.total_components,
            "components_added": bom.components_added,
            "components_removed": bom.components_removed,
            "components_updated": bom.components_updated,
            "vulnerabilities": bom.total_vulnerabilities
        }
        report.changes.append(change_entry)
        
        total_added += bom.components_added
        total_removed += bom.components_removed
        total_updated += bom.components_updated
        
        vulnerability_trend.append({
            "date": bom.bom_date.isoformat(),
            "count": bom.total_vulnerabilities
        })
    
    report.total_components_added = total_added
    report.total_components_removed = total_removed
    report.total_components_updated = total_updated
    report.vulnerability_trend = vulnerability_trend
    
    return report


@router.get("/summary")
async def get_system_summary(db: AsyncSession = Depends(get_db)):
    """Get overall system summary statistics"""
    
    # Count assets
    asset_count_result = await db.execute(select(func.count(Asset.id)))
    total_assets = asset_count_result.scalar()
    
    # Count BOMs
    bom_count_result = await db.execute(select(func.count(BOMHistory.id)))
    total_boms = bom_count_result.scalar()
    
    # Get recent changes (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_boms_result = await db.execute(
        select(func.count(BOMHistory.id)).where(BOMHistory.created_at >= week_ago)
    )
    recent_boms = recent_boms_result.scalar()
    
    return {
        "total_assets": total_assets,
        "total_bom_snapshots": total_boms,
        "recent_bom_updates": recent_boms,
        "last_updated": datetime.utcnow().isoformat()
    }