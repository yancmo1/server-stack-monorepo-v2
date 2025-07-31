import os
import json
import time
import psutil
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    print("Warning: Docker module not available. Container monitoring disabled.")

app = Flask(__name__, template_folder="/app/shared_templates")

# Load environment variables
load_dotenv('/Users/yancyshepherd/MEGA/PythonProjects/YANCY/shared/config/.env')

# Configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "apps_config.json")
DOCKER_CLIENT = None

if DOCKER_AVAILABLE:
    try:
        DOCKER_CLIENT = docker.from_env()
    except Exception as e:
        print(f"Warning: Could not connect to Docker: {e}")
        DOCKER_AVAILABLE = False

def load_config():
    """Load application configuration"""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"applications": {}, "system": {}, "monitoring": {}}

def get_system_info():
    """Get real system information"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 1),
            "uptime": str(uptime).split('.')[0],
            "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        }
    except Exception as e:
        print(f"Error getting system info: {e}")
        return {
            "cpu_percent": 0,
            "memory_used_gb": 0,
            "memory_total_gb": 0,
            "memory_percent": 0,
            "disk_used_gb": 0,
            "disk_total_gb": 0,
            "disk_percent": 0,
            "uptime": "Unknown",
            "load_avg": [0, 0, 0]
        }

def check_docker_container(container_name):
    """Check Docker container status"""
    if not DOCKER_CLIENT or not DOCKER_AVAILABLE:
        return {"status": "docker_unavailable", "error": "Docker not available"}
    
    try:
        container = DOCKER_CLIENT.containers.get(container_name)
        stats = container.stats(stream=False)
        
        # Calculate memory usage
        memory_usage = 0
        memory_limit = 0
        if 'memory' in stats and 'usage' in stats['memory']:
            memory_usage = stats['memory']['usage'] / (1024 * 1024)  # MB
            memory_limit = stats['memory']['limit'] / (1024 * 1024)  # MB
        
        return {
            "status": container.status,
            "id": container.short_id,
            "created": container.attrs['Created'],
            "memory_mb": round(memory_usage, 1),
            "memory_limit_mb": round(memory_limit, 1),
            "cpu_usage": stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
        }
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return {"status": "not_found", "error": "Container not found"}
        else:
            return {"status": "error", "error": error_msg}

def check_app_health(app_config):
    """Check application health via HTTP endpoint"""
    if not app_config.get('port') or not app_config.get('health_endpoint'):
        return {"status": "no_health_check", "response_time": None}
    
    url = f"http://localhost:{app_config['port']}{app_config['health_endpoint']}"
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        response_time = round((time.time() - start_time) * 1000, 2)  # ms
        
        if response.status_code == 200:
            return {
                "status": "healthy",
                "response_time": response_time,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        else:
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "error": f"HTTP {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {"status": "connection_refused", "response_time": None}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "response_time": None}
    except Exception as e:
        return {"status": "error", "response_time": None, "error": str(e)}

def check_port_listening(port):
    """Check if a port is listening"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except:
        return False

@app.route("/")
def dashboard():
    """Main dashboard page"""
    config = load_config()
    apps = {}
    
    # Check each application
    for app_id, app_cfg in config["applications"].items():
        container_info = check_docker_container(app_cfg.get('container_name', app_id))
        health_info = check_app_health(app_cfg)
        port_listening = check_port_listening(app_cfg['port']) if app_cfg.get('port') else False
        
        apps[app_id] = {
            "config": app_cfg,
            "container": container_info,
            "health": health_info,
            "port_listening": port_listening,
            "last_checked": datetime.now().isoformat()
        }
    
    # Get system information
    system = get_system_info()
    
    # Get monitoring configuration
    monitoring = config.get("monitoring", {})
    stable_apps = monitoring.get("stable_apps", [])
    development_apps = monitoring.get("development_apps", [])
    
    base_url = config.get("system", {}).get("base_url", "http://localhost")
    return render_template(
        "dashboard.html",
        apps=apps,
        system=system,
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        stable_apps=stable_apps,
        development_apps=development_apps,
        config=config,
        base_url=base_url,
        request=request
    )

@app.route("/api/health")
def health_check():
    """Dashboard health check endpoint"""
    return jsonify({
        "service": "dashboard",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    })

@app.route("/api/apps")
def api_apps():
    """API endpoint for application status"""
    config = load_config()
    apps_status = {}
    
    for app_id, app_cfg in config["applications"].items():
        container_info = check_docker_container(app_cfg.get('container_name', app_id))
        health_info = check_app_health(app_cfg)
        
        apps_status[app_id] = {
            "status": container_info.get("status", "unknown"),
            "health": health_info.get("status", "unknown"),
            "response_time": health_info.get("response_time"),
            "port_listening": check_port_listening(app_cfg['port']) if app_cfg.get('port') else False
        }
    
    return jsonify(apps_status)

@app.route("/api/system")
def api_system():
    """API endpoint for system information"""
    return jsonify(get_system_info())

@app.route("/debug/template")
def debug_template():
    """Debug template loading"""
    import os
    template_path = app.template_folder
    templates_exist = os.path.exists(template_path) if template_path else False
    dashboard_template_exists = False
    
    if template_path:
        dashboard_template_path = os.path.join(template_path, "dashboard.html") 
        dashboard_template_exists = os.path.exists(dashboard_template_path)
    
    return jsonify({
        "template_folder": template_path,
        "templates_exist": templates_exist,
        "dashboard_template_exists": dashboard_template_exists,
        "files_in_template_folder": os.listdir(template_path) if template_path and templates_exist else []
    })

if __name__ == "__main__":
    print("🏠 Starting Enhanced Dashboard...")
    print("📊 Features: Real-time monitoring, Docker integration, Health checks")
    app.run(host="0.0.0.0", port=5550, debug=True)
