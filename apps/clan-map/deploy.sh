#!/bin/bash

# Simple deployment script for clan-map
echo "Deploying clan-map updates..."

# Try to copy files to Pi
PI_HOST="192.168.50.100"
PI_USER="pi"
PI_PATH="/home/pi/clan-map"

echo "Copying updated files to Pi..."

# Try each file individually and report status
files_to_copy=("app.py" "clan_data.json" "templates/submit.html" "templates/members.html")

for file in "${files_to_copy[@]}"; do
    echo "Copying $file..."
    if scp "$file" "$PI_USER@$PI_HOST:$PI_PATH/$file" 2>/dev/null; then
        echo "✅ $file copied successfully"
    else
        echo "❌ Failed to copy $file"
    fi
done

echo "Attempting to restart clan-map service..."
if ssh "$PI_USER@$PI_HOST" 'sudo systemctl restart clan-map' 2>/dev/null; then
    echo "✅ Service restarted successfully"
else
    echo "❌ Failed to restart service"
fi

echo "Deployment attempt complete."
echo "You can test the application at: https://map.yancmo.xyz"
