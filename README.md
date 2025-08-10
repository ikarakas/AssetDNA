# AssetDNA - BOM Tracking & Historical Analysis System

## Overview
AssetDNA is a Bill of Materials (BOM) management system designed to track and analyze the evolution of complex technical systems over time. It provides historical tracking of Software Bills of Materials (SBOMs) and enables change analysis reporting.

## Key Features
- **Asset Hierarchy Management**: Fixed taxonomy of asset types from System of Systems down to Configuration Items
- **Historical BOM Tracking**: Store and version BOMs for each asset over time
- **Import/Export**: Support for CSV, JSON, and XML formats for OTOBO integration
- **Tabular Editing**: Excel-like interface for asset management
- **Change Analysis**: Generate reports showing how assets evolved over time
- **Unique Identification**: Assets use both UUIDs and URNs

## Asset Types
1. Domain / System of Systems
2. System / Environment  
3. Subsystem
4. Component / Segment
5. Configuration Item (CI)
6. Hardware CI
7. Software CI
8. Firmware CI

## Technology Stack
- **Database**: PostgreSQL 15+
- **Backend**: Python 3.11+ with FastAPI
- **ORM**: SQLAlchemy 2.0
- **Data Validation**: Pydantic
- **Web Server**: Uvicorn
- **Frontend**: HTML5 + Vanilla JS (tabular interface)

## Version Management
AssetDNA uses a centralized version management system:

- **Current Version**: 0.1.1
- **Primary Source**: `app/core/config.py` → `APP_VERSION`
- **Git Tags**: Version tags are created for each release (e.g., `v0.1.0`, `v0.1.1`)
- **Automatic Updates**: All parts of the application automatically use the version from config
- **API Integration**: System endpoint returns current version via `/api/v1/system/info`

**Version Update Process:**
1. Update `APP_VERSION` in `app/core/config.py`
2. Commit changes: `git commit -m "Update version to X.Y.Z"`
3. Create local tag: `git tag vX.Y.Z`
4. Push remote tag: `git push origin vX.Y.Z`

**Version Display:**
- API Documentation: Shows in FastAPI docs
- System Info: Available via `/api/v1/system/info`
- Export Files: Included in CSV, JSON, and XML exports

## Installation

### Using Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# Or use the Makefile for easier management
make up
```

**Available Makefile Commands:**
```bash
make up          # Start all services
make down        # Stop all services
make restart     # Restart all services
make build       # Build containers
make logs        # View logs
make shell       # Open shell in app container
make migrate     # Run database migrations
make status      # Show service status
make seed        # Seed database with test data
make test        # Run tests
make help        # Show all available commands
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
alembic upgrade head

# Run application
uvicorn main:app --host 0.0.0.0 --port 10001 --reload
```

## API Documentation
Once running, API documentation is available at:
- http://localhost:10001/docs (Swagger UI)
- http://localhost:10001/redoc (ReDoc)

**Quick Start:**
```bash
# Start the application
make up

# View logs
make logs

# Check service status
make status
```

## Usage

### Import Assets
```bash
# CSV Import
curl -X POST http://localhost:10001/api/v1/import/csv \
  -F "file=@assets.csv"

# JSON Import  
curl -X POST http://localhost:10001/api/v1/import/json \
  -H "Content-Type: application/json" \
  -d @assets.json
```

### Export Assets
```bash
# Export to CSV
curl http://localhost:10001/api/v1/export/csv > assets.csv

# Export to JSON
curl http://localhost:10001/api/v1/export/json > assets.json

# Export to XML
curl http://localhost:10001/api/v1/export/xml > assets.xml
```

### Change Analysis
```bash
# Get 6-month change report for an asset
curl http://localhost:10001/api/v1/assets/{asset_id}/changes?months=6
```

## Database Schema
- **assets**: Core asset table with hierarchy
- **asset_types**: Fixed asset type definitions
- **bom_history**: Historical BOM snapshots
- **bom_items**: Individual BOM line items
- **audit_log**: Change tracking

## OTOBO Integration
AssetDNA is designed to complement OTOBO for asset structure management. Use the import/export features to synchronize data between systems.

## License
MIT