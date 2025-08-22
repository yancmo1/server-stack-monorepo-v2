#!/bin/bash

# Deploy Database Upload Functionality to Raspberry Pi
# This script deploys the completed upload/download database sync system

set -e

echo "🔄 Deploying Database Upload Functionality to Pi"
echo "================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PI_HOST="100.88.190.68"
PI_USER="pi"
LOCAL_DIR="/Users/yancyshepherd/Library/CloudStorage/OneDrive-GCGLLC/Yancy/Home/PythonProjects/QSL Card Creator/QSL-Card-Creator-MAC/w5xy-qsl-card-creator"
PI_DIR="~/w5xy-qsl-card-creator"

echo -e "${BLUE}📁 Working from: ${LOCAL_DIR}${NC}"
cd "${LOCAL_DIR}"

# Step 1: Verify files are ready
echo -e "\n${YELLOW}✅ Step 1: Verifying updated files...${NC}"

if [ ! -f "web_app.py" ]; then
    echo -e "${RED}❌ web_app.py not found${NC}"
    exit 1
fi

if [ ! -f "qsl_settings.json" ]; then
    echo -e "${RED}❌ qsl_settings.json not found${NC}"
    exit 1
fi

if [ ! -f "web_requirements.txt" ]; then
    echo -e "${RED}❌ web_requirements.txt not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required files found${NC}"

# Step 2: Check settings configuration
echo -e "\n${YELLOW}🔧 Step 2: Checking upload configuration...${NC}"

if grep -q '"enable_database_upload": true' qsl_settings.json; then
    echo -e "${GREEN}✅ Upload functionality enabled in settings${NC}"
else
    echo -e "${RED}❌ Upload functionality not enabled in settings${NC}"
    exit 1
fi

if grep -q '"auto_download_database": false' qsl_settings.json; then
    echo -e "${GREEN}✅ Auto-download disabled (manual only)${NC}"
else
    echo -e "${YELLOW}⚠️ Auto-download still enabled${NC}"
fi

# Step 3: Stop QSL application on Pi
echo -e "\n${YELLOW}⏹️  Step 3: Stopping QSL Card Creator on Pi...${NC}"
ssh ${PI_USER}@${PI_HOST} "pkill -f w5xy_qsl_web_app.py; exit 0" || echo "No QSL app processes to stop"

# Step 4: Deploy files to Pi
echo -e "\n${YELLOW}🚚 Step 4: Deploying files to Pi...${NC}"
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.DS_Store' \
    --exclude='*.log' --exclude='backup_files' \
    "${LOCAL_DIR}/" "${PI_USER}@${PI_HOST}:${PI_DIR}/"

echo -e "${GREEN}✅ Files deployed successfully${NC}"

# Step 5: Start QSL application
echo -e "\n${YELLOW}▶️  Step 5: Starting QSL Card Creator...${NC}"
ssh ${PI_USER}@${PI_HOST} << 'EOF'
    cd ~/w5xy-qsl-card-creator
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    # Start the application in the background
    nohup python web_app.py > logs/app.log 2>&1 &
    
    echo "✅ QSL Card Creator started"
    
    # Wait a moment and check if it's running
    sleep 3
    if pgrep -f "python.*web_app.py" > /dev/null; then
        echo "✅ Application is running (PID: $(pgrep -f 'python.*web_app.py'))"
    else
        echo "❌ Application may not have started properly"
        echo "Last few lines of log:"
        tail -n 10 logs/app.log || echo "No log file found"
    fi
EOF

# Step 6: Test the deployment
echo -e "\n${YELLOW}🔍 Step 6: Testing deployment...${NC}"
sleep 5

# Test HTTP endpoint
if ssh ${PI_USER}@${PI_HOST} "curl -s -f http://localhost:5001 > /dev/null"; then
    echo -e "${GREEN}✅ HTTP endpoint responsive${NC}"
else
    echo -e "${RED}❌ Application not responding${NC}"
    echo -e "${YELLOW}Checking logs...${NC}"
    ssh ${PI_USER}@${PI_HOST} "cd ~/w5xy-qsl-card-creator && tail -n 20 logs/app.log"
    exit 1
fi

# Step 7: Display access information
echo -e "\n${GREEN}🎉 Database Upload Functionality Deployed Successfully!${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo ""
echo -e "${BLUE}📱 Access URLs:${NC}"
echo "   • Local Pi HTTP: http://100.88.190.68:5001"
echo ""
echo -e "${BLUE}🔧 New Functionality:${NC}"
echo "   • ✅ Manual database download from PC (Download button)"
echo "   • ✅ Database upload to PC (Upload button)"
echo "   • ✅ Auto-download disabled by default"
echo "   • ✅ Network mount path configuration"
echo "   • ✅ Backup before upload/download"
echo ""
echo -e "${BLUE}📋 Usage Workflow:${NC}"
echo "   1. Download database from PC when starting QSL work"
echo "   2. Create/update QSL cards and mark as sent"
echo "   3. Upload database back to PC when finished"
echo ""
echo -e "${GREEN}Database upload functionality is now live!${NC}"
