# AssetDNA Templates

This directory contains template files for various AssetDNA operations.

## Import Templates

### import_template.csv
A CSV template for importing assets into AssetDNA.

#### Required Fields:
- **name**: Asset name (must be unique within the same parent)
- **asset_type**: Must match one of the existing asset types:
  - "Domain / System of Systems" 
  - "System / Environment"
  - "Subsystem / Service"
  - "Component / Segment"
  - "Configuration Item (CI)"
  - "Software CI"
  - "Hardware CI"
  - "Firmware CI"
- **parent_name**: Name of the parent asset (leave empty for root-level assets)

#### Optional Fields:
- **status**: Asset status (active/inactive/deprecated) - defaults to "active"
- **description**: Asset description
- **version**: Version number (e.g., "1.0.0")
- **external_id**: ID from external system
- **properties**: JSON object as string for custom properties (use {} for empty)
- **tags**: Comma-separated list of tags

#### Fields NOT to Include (auto-generated):
- **id**: System generates UUID automatically
- **urn**: Auto-generated based on asset type and name
- **created_at**: System sets to current timestamp
- **updated_at**: System sets to current timestamp
- **lifecycle_stage**: Optional, can be omitted
- **external_system**: Defaults to "OTOBO" if not specified

## Usage

1. Copy the template file
2. Edit with your asset data
3. Import via the web interface (Asset Import/Export tab)
4. Select CSV format and upload your file

## Notes

- Assets are imported in order, so ensure parents are listed before their children
- If an asset with the same name and parent already exists, it will be updated
- BOMs (Bill of Materials) are not included in import/export - they must be managed separately
- The import process will validate asset types and create proper hierarchy relationships