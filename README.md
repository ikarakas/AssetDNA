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

## Installation

### Using Docker (Recommended)
```bash
docker-compose up -d
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
python main.py
```

## API Documentation
Once running, API documentation is available at:
- http://localhost:10001/docs (Swagger UI)
- http://localhost:10001/redoc (ReDoc)

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