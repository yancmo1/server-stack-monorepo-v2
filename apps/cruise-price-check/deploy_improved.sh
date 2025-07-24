#!/bin/bash

# Deploy script for improved cruise price tracker
echo "🚢 Deploying Improved Carnival Cruise Price Tracker"
echo "================================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.improved.yml" ]; then
    echo "❌ Error: Please run this script from the cruise-price-check directory"
    exit 1
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.improved.yml down

# Remove old images (optional)
read -p "Remove old images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing old images..."
    docker image prune -f
    docker rmi cruise-price-check_cruise-tracker 2>/dev/null || true
fi

# Build new image
echo "🔨 Building improved cruise tracker image..."
docker-compose -f docker-compose.improved.yml build

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

# Start the service
echo "🚀 Starting improved cruise tracker..."
docker-compose -f docker-compose.improved.yml up -d

# Wait for service to be ready
echo "⏳ Waiting for service to start..."
sleep 10

# Check if service is running
if docker-compose -f docker-compose.improved.yml ps | grep -q "Up"; then
    echo "✅ Service started successfully!"
    echo ""
    echo "🌐 Web Interface: http://localhost:5003"
    echo "📊 API Endpoints:"
    echo "   GET  /api/status           - Get monitoring status"
    echo "   POST /api/check-price      - Run single price check"
    echo "   POST /api/monitoring/start - Start continuous monitoring"
    echo "   POST /api/monitoring/stop  - Stop monitoring"
    echo "   GET  /api/history/30       - Get 30-day price history"
    echo "   GET  /health               - Health check"
    echo ""
    echo "📋 Your cruise being monitored:"
    echo "   Ship JB, Western Caribbean, November 8, 2025"
    echo "   Baseline: \$1,462 (Interior Early Saver Sale)"
    echo "   Alerts: Price drops of \$50+"
    echo ""
    echo "🔧 Management Commands:"
    echo "   docker-compose -f docker-compose.improved.yml logs -f    # View logs"
    echo "   docker-compose -f docker-compose.improved.yml down       # Stop service"
    echo "   docker-compose -f docker-compose.improved.yml restart    # Restart service"
    echo ""
    
    # Test health endpoint
    echo "🏥 Testing health endpoint..."
    sleep 5
    if curl -f http://localhost:5003/health >/dev/null 2>&1; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check failed - service may still be starting"
    fi
    
else
    echo "❌ Service failed to start!"
    echo "📋 Checking logs..."
    docker-compose -f docker-compose.improved.yml logs --tail=20
    exit 1
fi