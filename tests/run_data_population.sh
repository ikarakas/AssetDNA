#!/bin/bash

echo "================================================"
echo "NATO AWACS Test Data Population"
echo "================================================"
echo ""

# Check if API is running
echo "Checking if API is accessible..."
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:10001/api/v1/system/info | grep -q "200"; then
    echo "❌ Error: API is not accessible at http://localhost:10001"
    echo "Please ensure the AssetDNA application is running."
    exit 1
fi
echo "✓ API is accessible"
echo ""

# Install requirements if needed
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing required Python packages..."
    pip3 install -r requirements.txt
fi

# Clear existing data (optional - commented out for safety)
# echo "Clearing existing data..."
# curl -X DELETE http://localhost:10001/api/v1/assets/all 2>/dev/null

# Run the population script
echo "Starting data population..."
echo ""
python3 populate_nato_awacs_data.py

echo ""
echo "================================================"
echo "Data population complete!"
echo "You can now view the assets at http://localhost:10001"
echo "================================================"