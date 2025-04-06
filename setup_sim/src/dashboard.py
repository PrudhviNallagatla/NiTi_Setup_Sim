# Monitoring dashboard for nitinol nanoparticle simulation
# Creates a lightweight web server to track simulation progress
# Access from mobile devices or any web browser - with secure access

import os
import sys
import glob
import json
import time
import socket
import threading
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, session
from flask_socketio import SocketIO
import pandas as pd
import logging
import argparse
import requests
import secrets
import hashlib
import qrcode
from io import BytesIO
import base64

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("dashboard.log"),
                              logging.StreamHandler()])
logger = logging.getLogger("NiTi-Dashboard")

# Command line arguments
parser = argparse.ArgumentParser(description='NiTi Nanoparticle Simulation Dashboard')
parser.add_argument('--local-only', action='store_true', help='Run in local mode only (no remote access)')
parser.add_argument('--remote-url', type=str, help='Custom ngrok URL if you have a paid account')
parser.add_argument('--secure-key', type=str, help='Provide a custom secure key for dashboard access')
args = parser.parse_args()

# Generate a secure access key if not provided
ACCESS_KEY = args.secure_key if args.secure_key else secrets.token_urlsafe(16)

# Get local IP for display
def get_local_ip():
    try:
        # Get the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nitinol_nanoparticle_sim_' + secrets.token_hex(16)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
socketio = SocketIO(app)

# Global variables
WORKSPACE_DIR = "/home/rimuru/workspace"
DATA_DIR = os.path.join(WORKSPACE_DIR, "setup_sim/data")
PHASE_DIRS = [os.path.join(DATA_DIR, f"phase{i}") for i in range(1, 5)]
LOG_DIRS = [os.path.join(dir_path, "logs") for dir_path in PHASE_DIRS]
PLOT_DIR = os.path.join(DATA_DIR, "dashboard_plots")
KEY_HASH = hashlib.sha256(ACCESS_KEY.encode()).hexdigest()
running_sims = {}
last_update = {}
remote_url = None

# Ensure plot directory exists
os.makedirs(PLOT_DIR, exist_ok=True)

# Helper functions to set up remote access via ngrok
def setup_ngrok():
    global remote_url

    # If a custom URL was provided, use it
    if args.remote_url:
        remote_url = args.remote_url
        logger.info(f"Using custom remote URL: {remote_url}")
        return True

    try:
        # Check if ngrok is installed
        ngrok_present = subprocess.run(["which", "ngrok"],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE).returncode == 0

        if not ngrok_present:
            logger.info("Installing ngrok for remote access...")
            # Install ngrok
            subprocess.run([
                "bash", "-c",
                "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | " +
                "sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && " +
                "echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | " +
                "sudo tee /etc/apt/sources.list.d/ngrok.list && " +
                "sudo apt update && sudo apt install -y ngrok"
            ], check=True)

        # Start ngrok tunnel
        logger.info("Starting ngrok tunnel for remote access...")
        port = 8087
        process = subprocess.Popen(
            ["ngrok", "http", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for ngrok to start up
        time.sleep(3)

        # Get the public URL
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            data = response.json()
            remote_url = data["tunnels"][0]["public_url"]
            logger.info(f"Remote access URL (base): {remote_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to get ngrok URL: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Failed to set up remote access: {str(e)}")
        return False

# Helper function to generate a QR code for the access URL
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# Authentication decorator
def require_auth(f):
    def decorated(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            # If accessing via API endpoint, return 401
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized access"}), 401
            # Otherwise redirect to login page
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Same helper functions as before
def parse_lammps_log(log_file):
    """Parse a LAMMPS log file and extract time series data"""
    try:
        with open(log_file, 'r') as f:
            content = f.readlines()

        data_sections = []
        in_data_section = False
        headers = []
        current_section = []

        for line in content:
            line = line.strip()
            if 'Step' in line and 'Temp' in line:  # Typical header line
                if in_data_section and current_section:
                    data_sections.append((headers, current_section))
                in_data_section = True
                headers = line.split()
                current_section = []
            elif in_data_section:
                if line and not line.startswith('Loop') and not line.startswith('#'):
                    try:
                        # Convert line to numeric values
                        values = [float(x) for x in line.split()]
                        if len(values) == len(headers):
                            current_section.append(values)
                    except ValueError:
                        in_data_section = False

        # Add the last section
        if in_data_section and current_section:
            data_sections.append((headers, current_section))

        return data_sections
    except Exception as e:
        logger.error(f"Error parsing log file {log_file}: {str(e)}")
        return []

def create_plot(data, headers, title, filename):
    """Create a plot from the parsed log data"""
    try:
        df = pd.DataFrame(data, columns=headers)

        # Plot typical LAMMPS quantities
        plot_types = [
            {'col': 'Temp', 'ylabel': 'Temperature (K)', 'color': 'red'},
            {'col': 'PotEng', 'ylabel': 'Potential Energy', 'color': 'blue'},
            {'col': 'KinEng', 'ylabel': 'Kinetic Energy', 'color': 'green'},
            {'col': 'Press', 'ylabel': 'Pressure (bar)', 'color': 'purple'}
        ]

        for plot_type in plot_types:
            col = plot_type['col']
            if col in df.columns:
                plt.figure(figsize=(10, 6))
                plt.plot(df['Step'], df[col], color=plot_type['color'])
                plt.xlabel('Step')
                plt.ylabel(plot_type['ylabel'])
                plt.title(f"{title} - {plot_type['col']}")
                plt.grid(True)
                plot_path = os.path.join(PLOT_DIR, f"{filename}_{col}.png")
                plt.savefig(plot_path)
                plt.close()

        return True
    except Exception as e:
        logger.error(f"Error creating plot: {str(e)}")
        return False

def get_simulation_status():
    """Get the status of all simulation phases"""
    status = {
        "phases": [],
        "overall_progress": 0
    }

    # Check if pipeline is running
    pipeline_running = False
    try:
        result = subprocess.run(["pgrep", "-f", "pipeline.sh"], capture_output=True, text=True)
        pipeline_running = result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking pipeline status: {str(e)}")

    status["pipeline_running"] = pipeline_running

    # Get active LAMMPS processes
    active_lammps = []
    try:
        result = subprocess.run(["pgrep", "-f", "lmp"], capture_output=True, text=True)
        if result.returncode == 0:
            active_lammps = result.stdout.strip().split('\n')
    except Exception as e:
        logger.error(f"Error checking LAMMPS processes: {str(e)}")

    status["active_lammps"] = len(active_lammps)

    # Process each phase
    completed_phases = 0
    for i, phase_dir in enumerate(PHASE_DIRS, 1):
        phase_info = {
            "phase": i,
            "status": "Not Started",
            "progress": 0,
            "log_files": [],
            "plots": []
        }

        # Check if directory exists
        if os.path.exists(phase_dir):
            # Look for log files
            log_dir = os.path.join(phase_dir, "logs")
            if os.path.exists(log_dir):
                log_files = glob.glob(os.path.join(log_dir, "*.log"))
                phase_info["log_files"] = [os.path.basename(f) for f in log_files]

                if log_files:
                    # Check for complete flag or analyze logs
                    complete_flag = os.path.join(phase_dir, "COMPLETE")
                    if os.path.exists(complete_flag):
                        phase_info["status"] = "Complete"
                        phase_info["progress"] = 100
                        completed_phases += 1
                    else:
                        # Analyze the most recent log file
                        latest_log = max(log_files, key=os.path.getmtime)
                        phase_info["current_log"] = os.path.basename(latest_log)

                        # Generate plots for the log file if needed
                        plot_base = f"phase{i}_latest"
                        have_plots = False
                        for plot_type in ['Temp', 'PotEng', 'KinEng', 'Press']:
                            plot_file = f"{plot_base}_{plot_type}.png"
                            if os.path.exists(os.path.join(PLOT_DIR, plot_file)):
                                have_plots = True
                                phase_info["plots"].append(plot_file)

                        if not have_plots:
                            sections = parse_lammps_log(latest_log)
                            if sections:
                                headers, data = sections[-1]  # Use the last section
                                create_plot(data, headers, f"Phase {i}", plot_base)

                                # Update plots list
                                for plot_type in ['Temp', 'PotEng', 'KinEng', 'Press']:
                                    plot_file = f"{plot_base}_{plot_type}.png"
                                    if os.path.exists(os.path.join(PLOT_DIR, plot_file)):
                                        phase_info["plots"].append(plot_file)

                        # Estimate progress
                        try:
                            with open(latest_log, 'r') as f:
                                content = f.read()
                            if "Loop time" in content:  # LAMMPS completion indicator
                                phase_info["status"] = "Complete"
                                phase_info["progress"] = 100
                                completed_phases += 1
                            else:
                                phase_info["status"] = "Running" if str(i) in active_lammps else "Paused"
                                # Parse to estimate progress
                                phase_info["progress"] = min(95, max(10, len(content) / 10000 * 100))
                        except Exception as e:
                            logger.error(f"Error analyzing log file: {str(e)}")
                            phase_info["status"] = "Unknown"
                            phase_info["progress"] = 0

        status["phases"].append(phase_info)

    # Calculate overall progress
    if completed_phases == 4:
        status["overall_progress"] = 100
    else:
        # Weight each phase equally
        status["overall_progress"] = sum(phase["progress"] for phase in status["phases"]) / 4

    return status

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_key = request.form.get('access_key', '')
        if hashlib.sha256(input_key.encode()).hexdigest() == KEY_HASH:
            session['authenticated'] = True
            session.permanent = True
            next_page = request.args.get('next', '/')
            return redirect(next_page)
        return render_template('login.html', error="Invalid access key")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def index():
    return get_dashboard_template()

@app.route('/api/status')
@require_auth
def api_status():
    return jsonify(get_simulation_status())

@app.route('/api/launch', methods=['POST'])
@require_auth
def api_launch():
    """Launch the simulation pipeline"""
    try:
        pipeline_path = os.path.join(WORKSPACE_DIR, "setup_sim/src/pipeline.sh")
        if os.path.exists(pipeline_path):
            # Make sure it's executable
            subprocess.run(["chmod", "+x", pipeline_path])
            # Launch in background
            subprocess.Popen([pipeline_path],
                           stdout=open(os.path.join(DATA_DIR, "pipeline.log"), "w"),
                           stderr=subprocess.STDOUT,
                           start_new_session=True)
            return jsonify({"status": "success", "message": "Pipeline launched"})
        else:
            return jsonify({"status": "error", "message": "Pipeline script not found"})
    except Exception as e:
        logger.error(f"Error launching pipeline: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/plot/<path:filename>')
@require_auth
def get_plot(filename):
    return send_file(os.path.join(PLOT_DIR, filename))

@app.route('/log/<path:filename>')
@require_auth
def get_log(filename):
    # First try to find the log in any of the phases
    for log_dir in LOG_DIRS:
        log_path = os.path.join(log_dir, filename)
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    return jsonify({"content": f.read()})
            except Exception as e:
                return jsonify({"error": str(e)})

    # Try pipeline log
    pipeline_log = os.path.join(DATA_DIR, "pipeline.log")
    if filename == "pipeline.log" and os.path.exists(pipeline_log):
        try:
            with open(pipeline_log, 'r') as f:
                return jsonify({"content": f.read()})
        except Exception as e:
            return jsonify({"error": str(e)})

    return jsonify({"error": "Log file not found"})

# Login template
@app.route('/template/login')
def get_login_template():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NiTi Simulation Dashboard - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background-color: #f5f5f5;
        }
        .login-container {
            max-width: 400px;
            padding: 30px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .form-floating {
            margin-bottom: 20px;
        }
        .error-message {
            color: #dc3545;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h2>NiTi Simulation</h2>
            <p class="text-muted">Nanoparticle Monitoring</p>
        </div>
        <form method="POST">
            <div class="form-floating">
                <input type="password" class="form-control" id="access_key" name="access_key" placeholder="Access Key">
                <label for="access_key">Access Key</label>
            </div>
            {% if error %}
            <div class="error-message">{{ error }}</div>
            {% endif %}
            <button class="w-100 btn btn-lg btn-primary" type="submit">Sign in</button>
            <p class="mt-3 text-muted text-center">Enter the secure access key provided.</p>
        </form>
    </div>
</body>
</html>
    """

# HTML Template for dashboard
def get_dashboard_template():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NiTi Nanoparticle Simulation Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding-top: 20px; }
        .phase-card { margin-bottom: 20px; }
        .progress { height: 25px; }
        .log-window {
            background-color: #000;
            color: #00ff00;
            font-family: monospace;
            height: 300px;
            overflow-y: auto;
            padding: 10px;
            border-radius: 5px;
        }
        .plot-img { max-width: 100%; height: auto; margin-bottom: 10px; }
        .phase-header { cursor: pointer; }
        .logout-link {
            position: absolute;
            top: 10px;
            right: 10px;
        }
        @media (max-width: 768px) {
            .container { max-width: 100%; padding: 0 10px; }
            h1 { font-size: 1.5rem; }
            .btn { padding: 0.25rem 0.5rem; font-size: 0.875rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/logout" class="logout-link btn btn-sm btn-outline-secondary">Logout</a>
        <h1 class="text-center mb-4">NiTi Nanoparticle Simulation Monitor</h1>

        <div class="row mb-4">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        Overall Progress
                    </div>
                    <div class="card-body">
                        <div class="progress mb-3">
                            <div id="overall-progress" class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%">0%</div>
                        </div>
                        <div id="overall-status" class="alert alert-info">Checking status...</div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header bg-dark text-white">
                        Controls
                    </div>
                    <div class="card-body">
                        <button id="refresh-btn" class="btn btn-primary mb-2 w-100">Refresh Status</button>
                        <button id="launch-btn" class="btn btn-success mb-2 w-100">Launch Pipeline</button>
                        <div class="form-check form-switch">
                            <input class="form-check-input" type="checkbox" id="auto-refresh">
                            <label class="form-check-label" for="auto-refresh">Auto-refresh (30s)</label>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div id="phases-container">
            <!-- Phases will be added here dynamically -->
        </div>

        <div class="card mb-4">
            <div class="card-header bg-dark text-white">
                Pipeline Log
            </div>
            <div class="card-body">
                <pre id="pipeline-log" class="log-window">Loading pipeline log...</pre>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Global variables
        let autoRefreshInterval = null;
        const refreshInterval = 30000; // 30 seconds

        // Helper function to update progress bars
        function updateProgressBar(id, value) {
            const progressBar = document.getElementById(id);
            progressBar.style.width = `${value}%`;
            progressBar.textContent = `${Math.round(value)}%`;

            // Update color based on progress
            if (value < 25) {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
            } else if (value < 75) {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
            } else {
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
            }
        }

        // Function to fetch and display status
        async function refreshStatus() {
            try {
                const response = await fetch('/api/status');

                // Check if we got redirected to login page
                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                // Update overall progress
                updateProgressBar('overall-progress', data.overall_progress);

                // Update overall status
                let statusText = data.pipeline_running ?
                    `<strong>Pipeline Running</strong> with ${data.active_lammps} active LAMMPS processes` :
                    'Pipeline not currently running';
                document.getElementById('overall-status').innerHTML = statusText;

                // Update phases
                const phasesContainer = document.getElementById('phases-container');
                phasesContainer.innerHTML = '';

                data.phases.forEach(phase => {
                    const phaseCard = document.createElement('div');
                    phaseCard.className = 'card phase-card';

                    // Set card header color based on status
                    let headerClass = 'bg-secondary';
                    if (phase.status === 'Complete') {
                        headerClass = 'bg-success';
                    } else if (phase.status === 'Running') {
                        headerClass = 'bg-primary';
                    } else if (phase.status === 'Paused') {
                        headerClass = 'bg-warning';
                    }

                    // Create card content
                    phaseCard.innerHTML = `
                        <div class="card-header phase-header ${headerClass} text-white" data-bs-toggle="collapse" data-bs-target="#phase${phase.phase}-collapse">
                            Phase ${phase.phase}: ${phase.status} (${Math.round(phase.progress)}%)
                        </div>
                        <div id="phase${phase.phase}-collapse" class="collapse">
                            <div class="card-body">
                                <div class="progress mb-3">
                                    <div id="phase${phase.phase}-progress" class="progress-bar" role="progressbar" style="width: ${phase.progress}%">${Math.round(phase.progress)}%</div>
                                </div>

                                <div class="row">
                                    <div class="col-md-6">
                                        <h5>Log Files</h5>
                                        <div class="list-group log-files-list">
                                            ${phase.log_files.map(log => `
                                                <button class="list-group-item list-group-item-action view-log-btn" data-log="${log}">
                                                    ${log}
                                                </button>
                                            `).join('')}
                                        </div>
                                        ${phase.log_files.length > 0 ? `
                                            <div class="mt-3">
                                                <h6>Current Log:</h6>
                                                <pre class="log-window" id="phase${phase.phase}-log">Click a log file to view</pre>
                                            </div>
                                        ` : ''}
                                    </div>
                                    <div class="col-md-6">
                                        <h5>Plots</h5>
                                        <div class="plots-container">
                                            ${phase.plots.map(plot => `
                                                <img src="/plot/${plot}" class="plot-img" alt="${plot}">
                                            `).join('')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

                    phasesContainer.appendChild(phaseCard);
                    updateProgressBar(`phase${phase.phase}-progress`, phase.progress);
                });

                // Add event listeners to log buttons
                document.querySelectorAll('.view-log-btn').forEach(button => {
                    button.addEventListener('click', async function() {
                        const logFile = this.getAttribute('data-log');
                        const phaseNumber = this.closest('.phase-card').querySelector('.phase-header').textContent.charAt(6);
                        const logWindow = document.getElementById(`phase${phaseNumber}-log`);

                        logWindow.textContent = 'Loading log...';
                        try {
                            const response = await fetch(`/log/${logFile}`);

                            if (response.redirected) {
                                window.location.href = response.url;
                                return;
                            }

                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }

                            const data = await response.json();
                            if (data.content) {
                                logWindow.textContent = data.content;
                                // Scroll to bottom
                                logWindow.scrollTop = logWindow.scrollHeight;
                            } else {
                                logWindow.textContent = data.error || 'Failed to load log';
                            }
                        } catch (error) {
                            logWindow.textContent = `Error: ${error.message}`;
                        }
                    });
                });

                // Fetch pipeline log
                refreshPipelineLog();

            } catch (error) {
                console.error('Error refreshing status:', error);
                document.getElementById('overall-status').innerHTML =
                    `<div class="alert alert-danger">Error refreshing status: ${error.message}</div>`;
            }
        }

        // Function to fetch pipeline log
        async function refreshPipelineLog() {
            try {
                const response = await fetch('/log/pipeline.log');

                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                const logWindow = document.getElementById('pipeline-log');

                if (data.content) {
                    logWindow.textContent = data.content;
                    // Scroll to bottom
                    logWindow.scrollTop = logWindow.scrollHeight;
                } else {
                    logWindow.textContent = data.error || 'No pipeline log available';
                }
            } catch (error) {
                console.error('Error fetching pipeline log:', error);
                document.getElementById('pipeline-log').textContent = 'Error fetching pipeline log';
            }
        }

        // Function to launch pipeline
        async function launchPipeline() {
            try {
                const button = document.getElementById('launch-btn');
                button.disabled = true;
                button.textContent = 'Launching...';

                const response = await fetch('/api/launch', {
                    method: 'POST'
                });

                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.status === 'success') {
                    document.getElementById('overall-status').innerHTML =
                        `<div class="alert alert-success">${data.message}</div>`;
                } else {
                    document.getElementById('overall-status').innerHTML =
                        `<div class="alert alert-danger">${data.message}</div>`;
                }

                // Re-enable button and refresh status
                button.disabled = false;
                button.textContent = 'Launch Pipeline';
                await refreshStatus();

            } catch (error) {
                console.error('Error launching pipeline:', error);
                document.getElementById('overall-status').innerHTML =
                    `<div class="alert alert-danger">Error launching pipeline: ${error.message}</div>`;

                const button = document.getElementById('launch-btn');
                button.disabled = false;
                button.textContent = 'Launch Pipeline';
            }
        }

        // Function to toggle auto-refresh
        function toggleAutoRefresh() {
            const autoRefreshCheckbox = document.getElementById('auto-refresh');

            if (autoRefreshCheckbox.checked) {
                autoRefreshInterval = setInterval(refreshStatus, refreshInterval);
            } else {
                clearInterval(autoRefreshInterval);
            }
        }

        // Initialize page
        document.addEventListener('DOMContentLoaded', () => {
            // Initial status refresh
            refreshStatus();

            // Set up event listeners
            document.getElementById('refresh-btn').addEventListener('click', refreshStatus);
            document.getElementById('launch-btn').addEventListener('click', launchPipeline);
            document.getElementById('auto-refresh').addEventListener('change', toggleAutoRefresh);

            // Enable auto-refresh by default
            document.getElementById('auto-refresh').checked = true;
            toggleAutoRefresh();
        });
    </script>
</body>
</html>
    """

@app.route('/api/dashboard-url')
def get_dashboard_url():
    """Return the URL for accessing the dashboard"""
    ip = get_local_ip()
    port = 8087

    urls = {
        "local_url": f"http://{ip}:{port}",
        "ip": ip,
        "port": port
    }

    if remote_url:
        secure_url = f"{remote_url}?key={ACCESS_KEY}"
        urls["remote_url"] = secure_url
        urls["qr_code"] = generate_qr_code(secure_url)

    return jsonify(urls)

# Render templates with proper Flask functionality
@app.route('/template')
def render_login_template():
    return render_template('login.html')

# Main function
if __name__ == '__main__':
    # Setup templates
    from flask import render_template_string
    app.jinja_env.globals.update(render_template=render_template_string)

    # Setup remote access if enabled
    if not args.local_only:
        remote_access_success = setup_ngrok()
        if remote_access_success:
            secure_url = f"{remote_url}?key={ACCESS_KEY}"
            qr_code = generate_qr_code(secure_url)

            print("\n" + "="*80)
            print(f"🔐 SECURE REMOTE ACCESS ENABLED!")
            print(f"Access your simulation from anywhere with this URL and key:")
            print(f"{secure_url}")
            print("\nThis URL contains your secure access key. DO NOT share it with others.")
            print("="*80 + "\n")

            # Also save to a file for reference
            with open(os.path.join(DATA_DIR, "dashboard_access.txt"), "w") as f:
                f.write(f"SECURE ACCESS URL: {secure_url}\n")
                f.write(f"ACCESS KEY: {ACCESS_KEY}\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            print(f"Access details saved to: {os.path.join(DATA_DIR, 'dashboard_access.txt')}")
            print("="*80 + "\n")
        else:
            print("\n" + "="*50)
            print(f"Remote access setup FAILED")
            print(f"Dashboard will only be available on your local network")
            print("="*50 + "\n")
    else:
        print("\n" + "="*50)
        print(f"Running in local-only mode (no remote access)")
        print("="*50 + "\n")

    # Print local access information
    ip = get_local_ip()
    port = 8087
    print("\n" + "="*50)
    print(f"NiTi Nanoparticle Simulation Dashboard")
    print("="*50)
    print(f"Access the dashboard from your local network at:")
    print(f"http://{ip}:{port}")
    print(f"\nSECURE ACCESS KEY: {ACCESS_KEY}")
    print("Save this key - you'll need it to log in!")
    print("="*50 + "\n")

    # Start background thread for updates
    update_thread = threading.Thread(target=background_updates)
    update_thread.daemon = True
    update_thread.start()

    # Start the web server
    socketio.run(app, host='0.0.0.0', port=port)
