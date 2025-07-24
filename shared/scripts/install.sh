#!/bin/bash

# Pi Application Dashboard - Professional Installation Script
# Automated setup for Raspberry Pi systems

set -e

# Configuration
DASHBOARD_NAME="Pi Application Dashboard"
REPO_URL="https://github.com/yourusername/pi-application-dashboard.git"
INSTALL_DIR="/home/pi/pi-dashboard"
SERVICE_NAME="pi-dashboard"
DASHBOARD_PORT="8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="/tmp/pi-dashboard-install.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 Pi Application Dashboard                     ║"
    echo "║                Professional Installation                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${PURPLE}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_system() {
    print_step "Checking system requirements..."
    
    # Check if running on Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "This script is designed for Raspberry Pi, but will continue anyway"
    fi
    
    # Check Python version
    if ! python3 --version | grep -E "3\.[7-9]|3\.1[0-9]" >/dev/null; then
        print_error "Python 3.7+ required"
        exit 1
    fi
    
    # Check if systemd is available
    if ! command -v systemctl >/dev/null; then
        print_error "systemd is required for service management"
        exit 1
    fi
    
    print_success "System requirements met"
}

install_dependencies() {
    print_step "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install required packages
    sudo apt install -y python3-pip python3-venv git curl
    
    print_success "Dependencies installed"
}

setup_directory() {
    print_step "Setting up installation directory..."
    
    # Remove existing installation if present
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Existing installation found, backing up..."
        sudo mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%s)"
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    print_success "Directory setup complete"
}

copy_files() {
    print_step "Copying dashboard files..."
    
    # Copy all files from current directory to installation directory
    cp -r "$PWD"/* "$INSTALL_DIR/" 2>/dev/null || true
    
    # Create necessary directories
    mkdir -p "$INSTALL_DIR"/{logs,backups,tmp}
    
    # Set proper permissions
    chmod +x "$INSTALL_DIR"/scripts/*.sh 2>/dev/null || true
    
    print_success "Files copied successfully"
}

setup_python_environment() {
    print_step "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv dashboard_venv
    
    # Activate virtual environment and install dependencies
    source dashboard_venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Python environment configured"
}

configure_application() {
    print_step "Configuring application..."
    
    # Create default configuration if not exists
    if [ ! -f "$INSTALL_DIR/config/apps_config.json" ]; then
        print_warning "No application configuration found, creating default..."
        # Configuration will be created by the application on first run
    fi
    
    # Set ownership
    sudo chown -R pi:pi "$INSTALL_DIR"
    
    print_success "Application configured"
}

create_systemd_service() {
    print_step "Creating systemd service..."
    
    sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null << EOF
[Unit]
Description=${DASHBOARD_NAME}
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${INSTALL_DIR}/dashboard_venv/bin
Environment=PYTHONPATH=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/dashboard_venv/bin/python dashboard.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${INSTALL_DIR}

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    
    print_success "Systemd service created"
}

configure_firewall() {
    print_step "Configuring firewall..."
    
    # Check if ufw is installed and active
    if command -v ufw >/dev/null && sudo ufw status | grep -q "Status: active"; then
        print_step "Configuring UFW firewall rules..."
        sudo ufw allow "$DASHBOARD_PORT/tcp" comment "Pi Dashboard"
        print_success "Firewall configured"
    else
        print_warning "UFW firewall not active, skipping firewall configuration"
    fi
}

start_service() {
    print_step "Starting dashboard service..."
    
    sudo systemctl start "$SERVICE_NAME"
    sleep 3
    
    # Check if service started successfully
    if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Dashboard service started successfully"
    else
        print_error "Failed to start dashboard service"
        sudo systemctl status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

test_installation() {
    print_step "Testing installation..."
    
    # Wait for service to be ready
    sleep 5
    
    # Test if dashboard is responding
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$DASHBOARD_PORT" | grep -q "200"; then
        print_success "Dashboard is responding on port $DASHBOARD_PORT"
    else
        print_warning "Dashboard may not be fully ready yet"
    fi
}

print_completion() {
    local_ip=$(hostname -I | awk '{print $1}')
    
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 Installation Complete!                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo
    echo -e "${BLUE}🌐 Access your dashboard at:${NC}"
    echo -e "   Local:     http://localhost:$DASHBOARD_PORT"
    echo -e "   Network:   http://$local_ip:$DASHBOARD_PORT"
    echo
    echo -e "${BLUE}🔧 Management commands:${NC}"
    echo -e "   Status:    sudo systemctl status $SERVICE_NAME"
    echo -e "   Restart:   sudo systemctl restart $SERVICE_NAME"
    echo -e "   Stop:      sudo systemctl stop $SERVICE_NAME"
    echo -e "   Logs:      sudo journalctl -u $SERVICE_NAME -f"
    echo
    echo -e "${BLUE}📁 Installation directory: $INSTALL_DIR${NC}"
    echo -e "${BLUE}📋 Log file: $LOG_FILE${NC}"
    echo
    echo -e "${YELLOW}Note: Configure your applications in $INSTALL_DIR/config/apps_config.json${NC}"
}

# Main installation process
main() {
    print_header
    
    print_step "Starting installation of $DASHBOARD_NAME..."
    
    check_system
    install_dependencies
    setup_directory
    copy_files
    setup_python_environment
    configure_application
    create_systemd_service
    configure_firewall
    start_service
    test_installation
    
    print_completion
}

# Run installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
