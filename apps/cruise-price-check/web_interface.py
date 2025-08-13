#!/usr/bin/env python3
"""
Web interface for the improved Carnival cruise price tracker
Provides a web UI to manage monitoring, view history, and configure alerts
"""

from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
import json
import threading
import time
import logging
from datetime import datetime
import os
import sqlite3


# Import our improved tracker
from improved_price_tracker import CruisePriceTracker

# Use environment variable for DB path
CRUISE_DB_PATH = os.environ.get('CRUISE_DB_PATH', '/app/data/cruise_prices.db')

CENTRAL_ENV_PATH = '/Users/yancyshepherd/MEGA/PythonProjects/YANCY/shared/config/.env'
load_dotenv(CENTRAL_ENV_PATH)
app = Flask(__name__)
CORS(app)

# Add Prometheus metrics
metrics = PrometheusMetrics(app)

# Global tracking state
tracker_instance = None
monitoring_thread = None
monitoring_active = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/web_interface.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_tracker():
    """Get or create tracker instance"""
    global tracker_instance
    if tracker_instance is None:
        tracker_instance = CruisePriceTracker('/app/cruise_config.json')
    return tracker_instance

def monitoring_loop():
    """Background monitoring loop"""
    global monitoring_active
    tracker = get_tracker()
    
    while monitoring_active:
        try:
            logger.info("Running scheduled price check...")
            results = tracker.check_price()
            # Detailed fields (engine, raw_price_text, snapshot_path) already included in results
            logger.info(f"Price check completed: {len(results['results'])} checks")
            
            # Sleep for configured interval
            check_interval = tracker.config["monitoring"]["check_interval_hours"]
            sleep_seconds = check_interval * 3600
            
            for _ in range(int(sleep_seconds)):
                if not monitoring_active:
                    break
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            time.sleep(300)  # Wait 5 minutes on error

@app.route('/')
def home():
    """Main dashboard"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>🚢 Carnival Cruise Price Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #0066cc; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .card { background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 20px 0; }
        .button { 
            background: #0066cc; color: white; padding: 12px 24px; 
            border: none; border-radius: 5px; cursor: pointer; 
            text-decoration: none; display: inline-block; margin: 5px;
        }
        .button:hover { background: #0052a3; }
        .button.danger { background: #dc3545; }
        .button.danger:hover { background: #c82333; }
        .button.success { background: #28a745; }
        .button.success:hover { background: #218838; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .status.active { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .status.inactive { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .price-history { max-height: 400px; overflow-y: auto; }
        .price-item { padding: 10px; border-bottom: 1px solid #eee; }
        .price-success { color: #28a745; }
        .price-error { color: #dc3545; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .form-row { display: flex; gap: 20px; margin-bottom: 10px; }
        .form-row label { min-width: 120px; }
        .form-row input, .form-row select { flex: 1; padding: 6px; border-radius: 4px; border: 1px solid #ccc; }
        .form-section { background: #f1f7ff; border: 1px solid #cce1ff; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚢 Carnival Cruise Price Tracker</h1>
        <p class="subtitle">Monitoring your November 8, 2025 Western Caribbean cruise</p>

        <div class="form-section">
            <h3>🔎 Search for a Cruise</h3>
            <form id="cruise-search-form" onsubmit="submitCruiseForm(event)">
                <div class="form-row">
                    <label for="ship">Ship:</label>
                    <input type="text" id="ship" name="ship" placeholder="e.g. Jubilee" required>
                </div>
                <div class="form-row">
                    <label for="date">Date:</label>
                    <input type="date" id="date" name="date" required>
                </div>
                <div class="form-row">
                    <label for="people">People:</label>
                    <input type="number" id="people" name="people" min="1" value="2" required>
                </div>
                <div class="form-row">
                    <label for="sail_from">Sail From:</label>
                    <input type="text" id="sail_from" name="sail_from" placeholder="e.g. Galveston" required>
                </div>
                <div class="form-row">
                    <label for="sail_to">Sail To:</label>
                    <input type="text" id="sail_to" name="sail_to" placeholder="e.g. The Bahamas" required>
                </div>
                <div class="form-row">
                    <label for="cabin_number">Cabin Number:</label>
                    <input type="text" id="cabin_number" name="cabin_number" placeholder="Optional">
                </div>
                <div class="form-row">
                    <label for="room_type">Room Type:</label>
                    <select id="room_type" name="room_type">
                        <option value="Interior" selected>Interior</option>
                        <option value="Oceanview">Oceanview</option>
                        <option value="Balcony">Balcony</option>
                        <option value="Suite">Suite</option>
                    </select>
                </div>
                <div class="form-row">
                    <label for="floor">Floor:</label>
                    <input type="text" id="floor" name="floor" placeholder="Optional">
                </div>
                <button type="submit" class="button success">🔍 Search & Check Price</button>
            </form>
            <div id="form-result"></div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📋 Cruise Details</h3>
                <div id="cruise-details">Loading...</div>
            </div>
            
            <div class="card">
                <h3>⚡ Quick Actions</h3>
                <button onclick="checkPrice()" class="button">🔍 Check Price Now</button>
                <button onclick="toggleMonitoring()" class="button" id="monitoring-btn">▶️ Start Monitoring</button>
                <button onclick="viewHistory()" class="button">📊 View History</button>
                <button onclick="checkStatus()" class="button">🔄 Refresh Status</button>
            </div>
        </div>
        
        <div class="card">
            <h3>📈 Monitoring Status</h3>
            <div id="monitoring-status" class="status inactive">
                Monitoring: Stopped
            </div>
            <div id="last-check">Last check: Never</div>
        </div>
        
        <div class="card">
            <h3>💰 Latest Prices</h3>
            <div id="latest-prices">
                <p>No recent price checks. Click "Check Price Now" to start.</p>
            </div>
        </div>
        
        <div class="card">
            <h3>📊 Price History</h3>
            <div id="price-history" class="price-history">
                <p>Loading price history...</p>
            </div>
        </div>
    </div>

    <script>
        let monitoringActive = false;
        
        function checkStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    updateUI(data);
                })
                .catch(error => console.error('Error:', error));
        }
        
        function checkPrice() {
            document.getElementById('latest-prices').innerHTML = '<p>🔍 Checking prices...</p>';
            
            fetch('/api/check-price', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    displayLatestPrices(data);
                    loadHistory();
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('latest-prices').innerHTML = '<p class="price-error">❌ Error checking prices</p>';
                });
        }
        
        function toggleMonitoring() {
            const action = monitoringActive ? 'stop' : 'start';
            
            fetch(`/api/monitoring/${action}`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    monitoringActive = data.monitoring_active;
                    updateMonitoringUI();
                })
                .catch(error => console.error('Error:', error));
        }
        
        function viewHistory() {
            loadHistory();
        }
        
        function loadHistory() {
            fetch('/api/history/30')
                .then(response => response.json())
                .then(data => {
                    displayHistory(data);
                })
                .catch(error => console.error('Error:', error));
        }
        
        function updateUI(data) {
            // Update cruise details
            const cruise = data.cruise_details;
            const target = data.target_price;
            
            document.getElementById('cruise-details').innerHTML = `
                <p><strong>Ship:</strong> ${cruise.ship_code} (Carnival)</p>
                <p><strong>Route:</strong> ${cruise.itinerary_code} - Western Caribbean</p>
                <p><strong>Departure:</strong> ${cruise.departure_port} (Galveston)</p>
                <p><strong>Date:</strong> November 8, 2025</p>
                <p><strong>Guests:</strong> ${cruise.num_guests}</p>
                <p><strong>Baseline Price:</strong> $${target.baseline_price}</p>
                <p><strong>Alert Threshold:</strong> $${target.alert_threshold} drop</p>
            `;
            
            // Update monitoring status
            monitoringActive = data.monitoring_active;
            updateMonitoringUI();
            
            if (data.last_check) {
                document.getElementById('last-check').innerHTML = `Last check: ${new Date(data.last_check).toLocaleString()}`;
            }
        }
        
        function updateMonitoringUI() {
            const statusDiv = document.getElementById('monitoring-status');
            const button = document.getElementById('monitoring-btn');
            
            if (monitoringActive) {
                statusDiv.className = 'status active';
                statusDiv.innerHTML = '✅ Monitoring: Active (checking every 6 hours)';
                button.innerHTML = '⏹️ Stop Monitoring';
                button.className = 'button danger';
            } else {
                statusDiv.className = 'status inactive';
                statusDiv.innerHTML = '⏸️ Monitoring: Stopped';
                button.innerHTML = '▶️ Start Monitoring';
                button.className = 'button success';
            }
        }
        
        function displayLatestPrices(data) {
            const results = data.results || [];
            let html = '<h4>Latest Price Check Results:</h4>';
            
            if (results.length === 0) {
                html += '<p>No results found.</p>';
            } else {
                results.forEach((result, index) => {
                    const status = result.success ? '✅' : '❌';
                    const priceText = result.price ? `$${result.price}` : 'N/A';
                    const baseline = data.baseline_price;
                    const savings = result.price ? baseline - result.price : 0;
                    const savingsText = savings > 0 ? ` (💰 Save $${savings})` : '';
                    
                    html += `
                        <div class="price-item">
                            <strong>${status} ${result.rate_code}/${result.meta_code}:</strong> 
                            ${priceText}${savingsText}
                            ${result.error ? `<br><small class="price-error">Error: ${result.error}</small>` : ''}
                        </div>
                    `;
                });
            }
            
            document.getElementById('latest-prices').innerHTML = html;
        }
        
        function displayHistory(history) {
            let html = '';
            
            if (history.length === 0) {
                html = '<p>No price history available.</p>';
            } else {
                history.forEach(record => {
                    const status = record.success ? '✅' : '❌';
                    const priceText = record.price ? `$${record.price}` : 'N/A';
                    const date = new Date(record.timestamp).toLocaleString();
                    
                    html += `
                        <div class="price-item">
                            ${status} ${date} - ${record.rate_code}/${record.meta_code}: ${priceText}
                            ${record.error ? `<br><small class="price-error">${record.error}</small>` : ''}
                        </div>
                    `;
                });
            }
            
            document.getElementById('price-history').innerHTML = html;
        }
        
        // Load initial data
        checkStatus();
        loadHistory();
        
        // Auto-refresh every 30 seconds
        setInterval(checkStatus, 30000);

        // Cruise form submission handler
        function submitCruiseForm(event) {
            event.preventDefault();
            const form = document.getElementById('cruise-search-form');
            const data = Object.fromEntries(new FormData(form).entries());
            document.getElementById('form-result').innerHTML = '<p>🔍 Checking price...</p>';
            fetch('/api/check-custom', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.error) {
                    document.getElementById('form-result').innerHTML = `<p class="price-error">❌ ${result.error}</p>`;
                } else {
                    let html = '<h4>Custom Price Check Results:</h4>';
                    if (result.results && result.results.length > 0) {
                        result.results.forEach(r => {
                            html += `<div class="price-item"><strong>${r.success ? '✅' : '❌'} ${r.rate_code || ''}/${r.meta_code || ''}:</strong> $${r.price || 'N/A'}${r.error ? `<br><small class='price-error'>${r.error}</small>` : ''}</div>`;
                        });
                    } else {
                        html += '<p>No results found.</p>';
                    }
                    document.getElementById('form-result').innerHTML = html;
                }
            })
            .catch(error => {
                document.getElementById('form-result').innerHTML = `<p class="price-error">❌ ${error}</p>`;
            });
        }
    </script>
</body>
</html>
    ''')

@app.route('/api/status')
def api_status():
    """Get current status"""
    tracker = get_tracker()
    
    # Get last check from database
    last_check = None
    try:
        with sqlite3.connect(CRUISE_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp FROM price_history ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                last_check = row[0]
    except:
        pass
    
    return jsonify({
        'monitoring_active': monitoring_active,
        'cruise_details': tracker.config['cruise_details'],
        'target_price': tracker.config['target_price'],
        'monitoring_config': tracker.config['monitoring'],
        'last_check': last_check
    })

@app.route('/api/check-price', methods=['POST'])
def api_check_price():
    """Run a single price check"""
    try:
        tracker = get_tracker()
        results = tracker.check_price()
        # results already contains engine, raw_price_text, price_hash, snapshot_path
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in price check: {e}")
        return jsonify({'error': str(e)}), 500

# New: Custom price check from form
@app.route('/api/check-custom', methods=['POST'])
def api_check_custom():
    try:
        data = request.get_json(force=True)
        # For now, just log and echo back
        logger.info(f"Custom price check requested: {data}")
        # TODO: Use form data to build config and run check
        tracker = get_tracker()
        # Optionally override tracker.config with form data here
        results = tracker.check_price()
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in custom price check: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/<action>', methods=['POST'])
def api_monitoring(action):
    """Start or stop monitoring"""
    global monitoring_active, monitoring_thread
    
    if action == 'start' and not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info("Monitoring started")
        
    elif action == 'stop' and monitoring_active:
        monitoring_active = False
        logger.info("Monitoring stopped")
    
    return jsonify({'monitoring_active': monitoring_active})

@app.route('/api/history/<int:days>')
def api_history(days):
    """Get price history"""
    try:
        tracker = get_tracker()
        # Attempt to include extended columns if present
        rows = []
        with sqlite3.connect(CRUISE_DB_PATH) as conn:
            cursor = conn.cursor()
            # Check available columns
            cursor.execute("PRAGMA table_info(price_history)")
            cols = {r[1] for r in cursor.fetchall()}
            extended = ['engine','raw_price_text','price_hash']
            select_cols = ['timestamp','price','rate_code','meta_code','success','error_message'] + [c for c in extended if c in cols]
            col_string = ",".join(select_cols)
            cursor.execute(f"SELECT {col_string} FROM price_history WHERE timestamp >= datetime('now', '-{days} days') ORDER BY timestamp DESC")
            for row in cursor.fetchall():
                base_keys = ['timestamp','price','rate_code','meta_code','success','error_message']
                data = {k: row[i] for i,k in enumerate(select_cols)}
                # Normalize success to bool
                if 'success' in data:
                    data['success'] = bool(data['success'])
                rows.append(data)
        return jsonify(rows)
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/cruise/health')
def cruise_health():
    return jsonify({"service": "cruise-price-check", "status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('/app/data', exist_ok=True)
    os.makedirs('/app/logs', exist_ok=True)
    
    # Update database path in tracker
    import sys
    sys.path.append('/app')
    
    logger.info("Starting Cruise Price Tracker Web Interface on port 5551")
    app.run(host='0.0.0.0', port=5551, debug=False)