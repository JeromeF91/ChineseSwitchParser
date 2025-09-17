#!/usr/bin/env python3
"""
Web Interface for Chinese Switch Parser

A sleek web interface for the Chinese switch parser with real-time monitoring
and data visualization capabilities.
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import threading
import time
from datetime import datetime
from advanced_parser import AdvancedChineseSwitchParser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'chinese_switch_parser_secret_key'

# Global parser instance
parser = None
last_data = {}
data_lock = threading.Lock()

def update_data_periodically():
    """Update switch data periodically in the background."""
    global parser, last_data
    
    while True:
        try:
            if parser and parser.is_authenticated:
                with data_lock:
                    last_data = parser.get_comprehensive_data()
                    logger.info("Data updated successfully")
        except Exception as e:
            logger.error(f"Error updating data: {str(e)}")
        
        time.sleep(30)  # Update every 30 seconds

# Start background thread
data_thread = threading.Thread(target=update_data_periodically, daemon=True)
data_thread.start()

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    """Connect to switch."""
    global parser
    
    try:
        data = request.get_json()
        url = data.get('url', 'http://10.41.8.33')
        username = data.get('username', '')
        password = data.get('password', '')
        
        parser = AdvancedChineseSwitchParser(url, username, password)
        
        if parser.connect():
            return jsonify({
                'success': True,
                'message': 'Connected successfully',
                'discovered_endpoints': list(parser.discovered_endpoints)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect to switch'
            })
    
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Connection error: {str(e)}'
        })

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from switch."""
    global parser
    
    try:
        parser = None
        with data_lock:
            last_data = {}
        
        return jsonify({
            'success': True,
            'message': 'Disconnected successfully'
        })
    
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Disconnect error: {str(e)}'
        })

@app.route('/data')
def get_data():
    """Get current switch data."""
    global last_data
    
    try:
        with data_lock:
            # Convert dataclasses to dictionaries for JSON serialization
            data = last_data.copy()
            
            if data.get('system_info'):
                data['system_info'] = data['system_info'].__dict__
            
            if data.get('port_status'):
                data['port_status'] = [port.__dict__ for port in data['port_status']]
            
            if data.get('vlan_info'):
                data['vlan_info'] = [vlan.__dict__ for vlan in data['vlan_info']]
            
            return jsonify(data)
    
    except Exception as e:
        logger.error(f"Data retrieval error: {str(e)}")
        return jsonify({
            'error': f'Data retrieval error: {str(e)}'
        })

@app.route('/refresh', methods=['POST'])
def refresh_data():
    """Manually refresh switch data."""
    global parser, last_data
    
    try:
        if parser and parser.is_authenticated:
            with data_lock:
                last_data = parser.get_comprehensive_data()
            
            return jsonify({
                'success': True,
                'message': 'Data refreshed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Not connected to switch'
            })
    
    except Exception as e:
        logger.error(f"Refresh error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Refresh error: {str(e)}'
        })

@app.route('/export')
def export_data():
    """Export data to JSON file."""
    global last_data
    
    try:
        with data_lock:
            data = last_data.copy()
            
            if data.get('system_info'):
                data['system_info'] = data['system_info'].__dict__
            
            if data.get('port_status'):
                data['port_status'] = [port.__dict__ for port in data['port_status']]
            
            if data.get('vlan_info'):
                data['vlan_info'] = [vlan.__dict__ for vlan in data['vlan_info']]
        
        # Create export file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"switch_export_{timestamp}.json"
        filepath = f"/Users/jerome/ChineseSwitchParser/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({
            'error': f'Export error: {str(e)}'
        })

@app.route('/status')
def get_status():
    """Get connection status."""
    global parser
    
    try:
        if parser and parser.is_authenticated:
            return jsonify({
                'connected': True,
                'url': parser.base_url,
                'endpoints': list(parser.discovered_endpoints)
            })
        else:
            return jsonify({
                'connected': False,
                'url': None,
                'endpoints': []
            })
    
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({
            'connected': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the main template
    create_templates()
    
    app.run(debug=True, host='0.0.0.0', port=5000)

def create_templates():
    """Create HTML templates for the web interface."""
    
    # Create index.html
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chinese Switch Parser</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-connected { background-color: #28a745; }
        .status-disconnected { background-color: #dc3545; }
        .card-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .table-responsive { max-height: 400px; overflow-y: auto; }
        .refresh-btn { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
        .loading { opacity: 0.6; pointer-events: none; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-network-wired"></i> Chinese Switch Parser
            </span>
            <span id="connection-status" class="text-light">
                <span class="status-indicator status-disconnected"></span>
                Disconnected
            </span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Connection Panel -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-plug"></i> Connection Settings</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <label for="switch-url" class="form-label">Switch URL</label>
                                <input type="text" class="form-control" id="switch-url" value="http://10.41.8.33">
                            </div>
                            <div class="col-md-3">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="username" placeholder="Optional">
                            </div>
                            <div class="col-md-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" placeholder="Optional">
                            </div>
                            <div class="col-md-2 d-flex align-items-end">
                                <button class="btn btn-primary w-100" id="connect-btn">
                                    <i class="fas fa-link"></i> Connect
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- System Information -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-info-circle"></i> System Information</h5>
                    </div>
                    <div class="card-body">
                        <div id="system-info" class="table-responsive">
                            <p class="text-muted">Connect to switch to view system information</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Port Status -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-ethernet"></i> Port Status</h5>
                    </div>
                    <div class="card-body">
                        <div id="port-status" class="table-responsive">
                            <p class="text-muted">Connect to switch to view port status</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- VLAN Information -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-sitemap"></i> VLAN Information</h5>
                    </div>
                    <div class="card-body">
                        <div id="vlan-info" class="table-responsive">
                            <p class="text-muted">Connect to switch to view VLAN information</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Refresh Button -->
    <button class="btn btn-primary refresh-btn" id="refresh-btn" title="Refresh Data">
        <i class="fas fa-sync-alt"></i>
    </button>

    <!-- Export Button -->
    <button class="btn btn-success refresh-btn" id="export-btn" style="bottom: 80px;" title="Export Data">
        <i class="fas fa-download"></i>
    </button>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let isConnected = false;
        let refreshInterval;

        // DOM elements
        const connectBtn = document.getElementById('connect-btn');
        const refreshBtn = document.getElementById('refresh-btn');
        const exportBtn = document.getElementById('export-btn');
        const statusIndicator = document.getElementById('connection-status');

        // Event listeners
        connectBtn.addEventListener('click', toggleConnection);
        refreshBtn.addEventListener('click', refreshData);
        exportBtn.addEventListener('click', exportData);

        // Auto-refresh every 30 seconds when connected
        function startAutoRefresh() {
            if (refreshInterval) clearInterval(refreshInterval);
            refreshInterval = setInterval(refreshData, 30000);
        }

        function stopAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        }

        async function toggleConnection() {
            if (isConnected) {
                await disconnect();
            } else {
                await connect();
            }
        }

        async function connect() {
            const url = document.getElementById('switch-url').value;
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            connectBtn.disabled = true;
            connectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';

            try {
                const response = await fetch('/connect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url, username, password })
                });

                const result = await response.json();

                if (result.success) {
                    isConnected = true;
                    connectBtn.innerHTML = '<i class="fas fa-unlink"></i> Disconnect';
                    connectBtn.className = 'btn btn-danger w-100';
                    statusIndicator.innerHTML = '<span class="status-indicator status-connected"></span>Connected';
                    startAutoRefresh();
                    await refreshData();
                } else {
                    alert('Connection failed: ' + result.message);
                }
            } catch (error) {
                alert('Connection error: ' + error.message);
            } finally {
                connectBtn.disabled = false;
            }
        }

        async function disconnect() {
            connectBtn.disabled = true;
            connectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Disconnecting...';

            try {
                const response = await fetch('/disconnect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                const result = await response.json();

                if (result.success) {
                    isConnected = false;
                    connectBtn.innerHTML = '<i class="fas fa-link"></i> Connect';
                    connectBtn.className = 'btn btn-primary w-100';
                    statusIndicator.innerHTML = '<span class="status-indicator status-disconnected"></span>Disconnected';
                    stopAutoRefresh();
                    clearData();
                } else {
                    alert('Disconnect failed: ' + result.message);
                }
            } catch (error) {
                alert('Disconnect error: ' + error.message);
            } finally {
                connectBtn.disabled = false;
            }
        }

        async function refreshData() {
            if (!isConnected) return;

            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            try {
                const response = await fetch('/data');
                const data = await response.json();

                if (data.error) {
                    console.error('Data error:', data.error);
                    return;
                }

                displaySystemInfo(data.system_info);
                displayPortStatus(data.port_status);
                displayVlanInfo(data.vlan_info);
            } catch (error) {
                console.error('Refresh error:', error);
            } finally {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
            }
        }

        function displaySystemInfo(systemInfo) {
            const container = document.getElementById('system-info');
            
            if (!systemInfo) {
                container.innerHTML = '<p class="text-muted">No system information available</p>';
                return;
            }

            const table = `
                <table class="table table-striped">
                    <tbody>
                        <tr><td><strong>Model:</strong></td><td>${systemInfo.model || 'Unknown'}</td></tr>
                        <tr><td><strong>Firmware Version:</strong></td><td>${systemInfo.firmware_version || 'Unknown'}</td></tr>
                        <tr><td><strong>Uptime:</strong></td><td>${systemInfo.uptime || 'Unknown'}</td></tr>
                        <tr><td><strong>MAC Address:</strong></td><td>${systemInfo.mac_address || 'Unknown'}</td></tr>
                        <tr><td><strong>IP Address:</strong></td><td>${systemInfo.ip_address || 'Unknown'}</td></tr>
                        <tr><td><strong>Subnet Mask:</strong></td><td>${systemInfo.subnet_mask || 'Unknown'}</td></tr>
                        <tr><td><strong>Gateway:</strong></td><td>${systemInfo.gateway || 'Unknown'}</td></tr>
                        ${systemInfo.cpu_usage ? `<tr><td><strong>CPU Usage:</strong></td><td>${systemInfo.cpu_usage}%</td></tr>` : ''}
                        ${systemInfo.memory_usage ? `<tr><td><strong>Memory Usage:</strong></td><td>${systemInfo.memory_usage}%</td></tr>` : ''}
                        ${systemInfo.temperature ? `<tr><td><strong>Temperature:</strong></td><td>${systemInfo.temperature}°C</td></tr>` : ''}
                    </tbody>
                </table>
            `;
            
            container.innerHTML = table;
        }

        function displayPortStatus(ports) {
            const container = document.getElementById('port-status');
            
            if (!ports || ports.length === 0) {
                container.innerHTML = '<p class="text-muted">No port information available</p>';
                return;
            }

            let table = `
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Port</th>
                            <th>Status</th>
                            <th>Speed</th>
                            <th>Duplex</th>
                            <th>VLAN</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            ports.forEach(port => {
                const statusClass = port.status && (port.status.toLowerCase().includes('up') || port.status.toLowerCase().includes('active')) ? 'text-success' : 'text-danger';
                table += `
                    <tr>
                        <td><strong>${port.port_id || 'Unknown'}</strong></td>
                        <td><span class="${statusClass}">${port.status || 'Unknown'}</span></td>
                        <td>${port.speed || 'Unknown'}</td>
                        <td>${port.duplex || 'Unknown'}</td>
                        <td>${port.vlan || 'Unknown'}</td>
                        <td>${port.description || ''}</td>
                    </tr>
                `;
            });

            table += '</tbody></table>';
            container.innerHTML = table;
        }

        function displayVlanInfo(vlans) {
            const container = document.getElementById('vlan-info');
            
            if (!vlans || vlans.length === 0) {
                container.innerHTML = '<p class="text-muted">No VLAN information available</p>';
                return;
            }

            let table = `
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>VLAN ID</th>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Ports</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            vlans.forEach(vlan => {
                const statusClass = vlan.status && (vlan.status.toLowerCase().includes('active') || vlan.status.toLowerCase().includes('up')) ? 'text-success' : 'text-danger';
                const portsStr = vlan.ports && vlan.ports.length > 0 ? vlan.ports.join(', ') : 'None';
                
                table += `
                    <tr>
                        <td><strong>${vlan.vlan_id || 'Unknown'}</strong></td>
                        <td>${vlan.name || 'Unknown'}</td>
                        <td><span class="${statusClass}">${vlan.status || 'Unknown'}</span></td>
                        <td>${portsStr}</td>
                        <td>${vlan.description || ''}</td>
                    </tr>
                `;
            });

            table += '</tbody></table>';
            container.innerHTML = table;
        }

        function clearData() {
            document.getElementById('system-info').innerHTML = '<p class="text-muted">Connect to switch to view system information</p>';
            document.getElementById('port-status').innerHTML = '<p class="text-muted">Connect to switch to view port status</p>';
            document.getElementById('vlan-info').innerHTML = '<p class="text-muted">Connect to switch to view VLAN information</p>';
        }

        async function exportData() {
            if (!isConnected) {
                alert('Please connect to switch first');
                return;
            }

            try {
                const response = await fetch('/export');
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `switch_export_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    alert('Export failed');
                }
            } catch (error) {
                alert('Export error: ' + error.message);
            }
        }

        // Check initial connection status
        async function checkStatus() {
            try {
                const response = await fetch('/status');
                const status = await response.json();
                
                if (status.connected) {
                    isConnected = true;
                    connectBtn.innerHTML = '<i class="fas fa-unlink"></i> Disconnect';
                    connectBtn.className = 'btn btn-danger w-100';
                    statusIndicator.innerHTML = '<span class="status-indicator status-connected"></span>Connected';
                    startAutoRefresh();
                    await refreshData();
                }
            } catch (error) {
                console.error('Status check error:', error);
            }
        }

        // Initialize
        checkStatus();
    </script>
</body>
</html>'''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

