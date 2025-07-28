import os
import json
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__, template_folder="/app/shared_templates")

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "apps_config.json")

with open(CONFIG_PATH) as f:
    config = json.load(f)

@app.route("/")
def dashboard():
    # Build the apps dict for the template
    apps = {}
    for app_id, app_cfg in config["applications"].items():
        apps[app_id] = {
            "config": app_cfg,
            "process": {"status": "running", "pid": 1234, "memory_mb": 100},
            "port_listening": True
        }
    system = {
        "cpu_percent": 10.0,
        "memory_used_gb": 1.2,
        "memory_total_gb": 4.0,
        "memory_percent": 30.0,
        "disk_used_gb": 10.0,
        "disk_total_gb": 32.0,
        "disk_percent": 31.0,
        "uptime": "1 day, 2:34:56"
    }
    return render_template(
        "dashboard.html",
        apps=apps,
        system=system,
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        request=request
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5550, debug=True)
