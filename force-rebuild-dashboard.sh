#!/bin/bash
# Force rebuild dashboard with no cache

cd /Users/yancyshepherd/MEGA/PythonProjects/YANCY/deploy

echo "🛑 Stopping dashboard container..."
docker compose -f docker-compose.dev.yml stop dashboard

echo "🗑️ Removing dashboard container..."
docker compose -f docker-compose.dev.yml rm -f dashboard

echo "🏗️ Building dashboard with no cache..."
docker compose -f docker-compose.dev.yml build --no-cache dashboard

echo "🚀 Starting dashboard..."
docker compose -f docker-compose.dev.yml up -d dashboard

echo "⏳ Waiting for dashboard..."
sleep 8

echo "📊 Checking dashboard status..."
docker compose -f docker-compose.dev.yml ps dashboard

echo "✅ Dashboard rebuilt! Check: http://localhost:5550"
