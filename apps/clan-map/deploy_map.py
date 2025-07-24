#!/usr/bin/env python3
"""
Deploy only the clan-map service using Docker Compose (production).
"""
import subprocess
import sys
from datetime import datetime

def run_command(command, description, check=True):
    print(f"[EXEC] {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error {description}: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return None

def deploy_on_server():
    print("🚀 Deploying clan-map on remote server...")
    ssh_cmd = (
        'ssh yancmo@ubuntumac "cd /home/yancmo/apps/coc-stack-monorepo && '
        'git pull && '
        'docker compose -f docker-compose.yml build clan-map && '
        'docker compose -f docker-compose.yml up -d clan-map && '
        'docker compose -f docker-compose.yml ps"'
    )
    run_command(ssh_cmd, 'deploying map on server')

def monitor_map_logs():
    print("📋 Tailing map logs for 60 seconds...")
    ssh_cmd = (
        'ssh yancmo@ubuntumac "cd /home/yancmo/apps/coc-stack-monorepo && '
        'timeout 60 docker compose -f docker-compose.yml logs -f clan-map"'
    )
    run_command(ssh_cmd, 'monitoring map logs')

def main():
    print("🐳 Deploying clan-map only")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    deploy_on_server()
    monitor_map_logs()
    print("✅ clan-map deployed successfully!")
    print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
