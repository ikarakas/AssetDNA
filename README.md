# AssetDNA

A modern web application for managing and organizing infrastructure assets with an interactive topology view.

## Features

- **Interactive Asset Management**: Add, edit, and delete assets with drag-and-drop functionality
- **Topology View**: Visual representation of assets organized by environment and CIS groups
- **Search & Filter**: Advanced search capabilities across all asset properties
- **Export Functionality**: Export data in JSON and JSONL formats
- **Responsive Design**: Modern UI that works on desktop and mobile devices

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with modern gradients and animations

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. **Clone the repository** (if using git):
   ```bash
   git clone <repository-url>
   cd AssetDNA
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Activate the virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the application**:
   ```bash
   python app.py
   ```

3. **Access the application**:
   Open your web browser and navigate to `http://localhost:5050`

## Usage

### Adding Assets
1. Fill out the asset form in the sidebar
2. Click "Add Asset" to create a new asset
3. The asset will appear in the topology view

### Edit Mode
1. Click "Enable Edit Mode" to activate editing features
2. Drag and drop assets between environments and CIS groups
3. Click on assets to edit their properties

### Exporting Data
- Use the "Export JSON" or "Export JSONL" buttons in the topology view
- Files will be downloaded to your default download folder

### Search and Filter
- Use the "Asset List" tab for basic search
- Use the "Search" tab for advanced filtering by environment, CIS group, and asset type

## Project Structure

```
AssetDNA/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── .gitignore         # Git ignore rules
└── templates/
    └── index.html     # Main web interface
```

## API Endpoints

- `GET /api/assets` - Get all assets (with optional filters)
- `POST /api/assets` - Create a new asset
- `PUT /api/assets/<id>` - Update an asset
- `DELETE /api/assets/<id>` - Delete an asset
- `POST /api/assets/move` - Move an asset to different environment/CIS group
- `GET /api/topology` - Get organized topology data
- `GET /api/export/json` - Export as JSON
- `GET /api/export/jsonl` - Export as JSONL

## Development

The application includes sample data that will be automatically created when you first run it. The database file (`asset_topology.db`) will be created in the project root directory.

## License

This project is open source and available under the MIT License.