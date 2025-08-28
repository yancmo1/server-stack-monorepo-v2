#!/bin/bash

# Upload working database and template to Pi
echo "📤 Uploading working files to Pi..."

PI_HOST="100.88.190.68"
PI_USER="pi"
APP_DIR="w5xy-qsl-card-creator"

# Upload database
echo "📊 Uploading database..."
scp "Log4OM db.SQLite" ${PI_USER}@${PI_HOST}:${APP_DIR}/

# Upload template  
echo "📄 Uploading template..."
scp "W5XY QSL Card Python TEMPLATE.pdf" ${PI_USER}@${PI_HOST}:${APP_DIR}/

echo "✅ Files uploaded successfully!"
