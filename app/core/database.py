"""
Database connection and initialization
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.models.base import Base
from app.models.asset import AssetType, AssetTypeEnum
import uuid

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database and create tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed asset types
    await seed_asset_types()


async def seed_asset_types():
    """Seed the fixed asset types"""
    async with AsyncSessionLocal() as session:
        # Check if types already exist
        from sqlalchemy import select
        result = await session.execute(select(AssetType))
        if result.scalars().first():
            return  # Already seeded
        
        # Define asset types with hierarchy levels
        asset_types = [
            {
                "name": AssetTypeEnum.DOMAIN_SYSTEM_OF_SYSTEMS,
                "description": "Highest level grouping of multiple systems",
                "level": 1,
                "can_have_bom": 0
            },
            {
                "name": AssetTypeEnum.SYSTEM_ENVIRONMENT,
                "description": "Complete system or environment",
                "level": 2,
                "can_have_bom": 1
            },
            {
                "name": AssetTypeEnum.SUBSYSTEM,
                "description": "Major functional component of a system",
                "level": 3,
                "can_have_bom": 1
            },
            {
                "name": AssetTypeEnum.COMPONENT_SEGMENT,
                "description": "Discrete component or segment",
                "level": 4,
                "can_have_bom": 1
            },
            {
                "name": AssetTypeEnum.CONFIGURATION_ITEM,
                "description": "Generic configuration item",
                "level": 5,
                "can_have_bom": 1
            },
            {
                "name": AssetTypeEnum.HARDWARE_CI,
                "description": "Hardware configuration item",
                "level": 5,
                "can_have_bom": 1
            },
            {
                "name": AssetTypeEnum.SOFTWARE_CI,
                "description": "Software configuration item",
                "level": 5,
                "can_have_bom": 1
            },
            {
                "name": AssetTypeEnum.FIRMWARE_CI,
                "description": "Firmware configuration item",
                "level": 5,
                "can_have_bom": 1
            }
        ]
        
        # Add asset types to database
        for type_data in asset_types:
            asset_type = AssetType(
                id=uuid.uuid4(),
                **type_data
            )
            session.add(asset_type)
        
        await session.commit()