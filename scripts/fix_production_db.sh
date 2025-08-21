#!/bin/bash

# Fix production database by adding missing race_page_url column
echo "Fixing production database - adding race_page_url column..."

# Connect to the production database container and add the column
docker exec -i tracker-db psql -U racetracker -d racetracker << EOF
ALTER TABLE race ADD COLUMN IF NOT EXISTS race_page_url TEXT;
\q
EOF

if [ $? -eq 0 ]; then
    echo "Successfully added race_page_url column to production database!"
else
    echo "Failed to add column. Checking if it already exists..."
    docker exec -i tracker-db psql -U racetracker -d racetracker -c "\d race" | grep race_page_url
fi

echo "Restarting tracker service..."
docker compose restart tracker

echo "Done!"