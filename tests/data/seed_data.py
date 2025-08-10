#!/usr/bin/env python3
"""
Seed the AssetDNA database with initial data for testing and development
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the path (go up two levels from tests/data to reach the root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import get_db, engine
from app.models.asset import Asset, AssetType, AssetTypeEnum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_asset_types(session):
    """Seed the asset types"""
    logger.info("Seeding asset types...")
    
    # Asset types with their hierarchy levels
    asset_types = [
        ("Domain / System of Systems", 0),
        ("System / Environment", 1),
        ("Subsystem / Service", 2),
        ("Component / Segment", 3), 
        ("Configuration Item (CI)", 4),
        ("Software CI", 4),
        ("Hardware CI", 4),
        ("Firmware CI", 4)
    ]
    
    for name, level in asset_types:
        # Check if already exists
        result = await session.execute(
            select(AssetType).where(AssetType.name == name)
        )
        if not result.scalar_one_or_none():
            # Create AssetType with name and level
            asset_type = AssetType(name=name, level=level, can_have_bom=1)
            session.add(asset_type)
            logger.info(f"  Added asset type: {name} (level {level})")
        else:
            logger.info(f"  Asset type already exists: {name}")
    
    await session.commit()
    logger.info("Asset types seeded successfully")

async def seed_sample_assets(session):
    """Seed sample assets"""
    logger.info("Seeding sample assets...")
    
    # Get asset types
    result = await session.execute(select(AssetType))
    asset_types = {at.name: at for at in result.scalars().all()}
    
    # Check if we already have assets
    existing = await session.execute(select(Asset))
    if existing.scalars().first():
        logger.info("  Assets already exist, skipping sample data")
        return
    
    # Create sample hierarchy
    assets_data = [
        # Root level
        ("Enterprise Systems", "Domain / System of Systems", None, "Top level enterprise systems"),
        ("Uncategorized", "Domain / System of Systems", None, "Uncategorized assets"),
        
        # Under Enterprise Systems
        ("Production Environment", "System / Environment", "Enterprise Systems", "Production systems"),
        ("Test Environment", "System / Environment", "Enterprise Systems", "Test and development systems"),
        
        # Under Production
        ("Web Application", "Subsystem / Service", "Production Environment", "Main web application"),
        ("Database Cluster", "Subsystem / Service", "Production Environment", "Database systems"),
        ("API Gateway", "Software CI", "Web Application", "API gateway service"),
        ("Frontend", "Software CI", "Web Application", "React frontend"),
        
        # Under Test
        ("Development Server", "System / Environment", "Test Environment", "Development server"),
        ("QA Environment", "System / Environment", "Test Environment", "QA testing environment"),
        
        # Some items under Uncategorized
        ("MPDS", "System / Environment", "Uncategorized", "MPDS system"),
        ("GEP", "Subsystem / Service", "Uncategorized", "GEP subsystem"),
        ("GEP Module 1", "Component / Segment", "GEP", "First module"),
        ("GEP Module 2", "Component / Segment", "GEP", "Second module"),
    ]
    
    # Create assets
    created_assets = {}
    for name, type_name, parent_name, description in assets_data:
        asset_type = asset_types[type_name]
        parent = created_assets.get(parent_name) if parent_name else None
        
        asset = Asset(
            name=name,
            description=description,
            asset_type_id=asset_type.id,
            parent_id=parent.id if parent else None,
            status="active"
        )
        asset.asset_type = asset_type  # Set for URN generation
        asset.urn = asset.generate_urn()
        
        session.add(asset)
        await session.flush()  # Get the ID
        created_assets[name] = asset
        logger.info(f"  Added asset: {name} ({type_name})")
    
    await session.commit()
    logger.info("Sample assets seeded successfully")

async def main():
    """Main function to seed the database"""
    logger.info("Starting database seeding...")
    
    async with async_session() as session:
        try:
            await seed_asset_types(session)
            await seed_sample_assets(session)
            logger.info("Database seeding completed successfully!")
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(main())
