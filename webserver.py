#!/usr/bin/env python3
"""
Web server for LED matrix control
Provides a browser-based interface to control the LED daemon
"""

import os
import sys
import socket
import json
import argparse
from flask import Flask, render_template_string, jsonify, request

# Import led_control functions
sys.path.insert(0, os.path.dirname(__file__))
from led_control import send_command, is_daemon_running, SOCKET_PATH

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LED Matrix Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #e0e0e0;
        }
        h1 {
            color: #00ff88;
            text-align: center;
            margin-bottom: 30px;
        }
        .status-box {
            background: #2a2a2a;
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #404040;
        }
        .status-item:last-child {
            border-bottom: none;
        }
        .status-label {
            font-weight: bold;
            color: #00ff88;
        }
        .status-value {
            color: #ffffff;
        }
        .control-section {
            background: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .control-section h2 {
            color: #00ff88;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .button-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }
        button {
            background: #00ff88;
            color: #000;
            border: none;
            padding: 12px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.2s;
        }
        button:hover {
            background: #00cc6a;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 255, 136, 0.3);
        }
        button:active {
            transform: translateY(0);
        }
        button.danger {
            background: #ff4444;
            color: #fff;
        }
        button.danger:hover {
            background: #cc0000;
        }
        .slider-container {
            margin: 15px 0;
        }
        .slider-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            color: #00ff88;
        }
        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #404040;
            outline: none;
            -webkit-appearance: none;
        }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #00ff88;
            cursor: pointer;
        }
        input[type="range"]::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #00ff88;
            cursor: pointer;
            border: none;
        }
        .effect-selector {
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: 2px solid #00ff88;
            background: #1a1a1a;
            color: #e0e0e0;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .message {
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            display: none;
        }
        .message.success {
            background: #00ff8844;
            border: 1px solid #00ff88;
            display: block;
        }
        .message.error {
            background: #ff444444;
            border: 1px solid #ff4444;
            display: block;
        }
        .offline {
            color: #ff4444;
            text-align: center;
            padding: 20px;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <h1>🎨 LED Matrix Control</h1>

    <div id="offline-warning" class="offline" style="display: none;">
        ⚠️ Daemon is not running. Start it with: sudo python demos.py --daemon
    </div>

    <div id="controls" style="display: none;">
        <div class="status-box">
            <h2 style="margin-top: 0; color: #00ff88;">Status</h2>
            <div class="status-item">
                <span class="status-label">Current Effect:</span>
                <span class="status-value" id="current-effect">-</span>
            </div>
            <div class="status-item">
                <span class="status-label">State:</span>
                <span class="status-value" id="state">-</span>
            </div>
            <div class="status-item">
                <span class="status-label">Brightness:</span>
                <span class="status-value" id="brightness-display">-</span>
            </div>
            <div class="status-item">
                <span class="status-label">Speed:</span>
                <span class="status-value" id="speed-display">-</span>
            </div>
            <div class="status-item">
                <span class="status-label">Frequency:</span>
                <span class="status-value" id="frequency-display">-</span>
            </div>
        </div>

        <div class="control-section">
            <h2>Effect Control</h2>
            <div class="button-grid">
                <button onclick="sendCommand('prev')">⬅️ Previous</button>
                <button onclick="sendCommand('next')">Next ➡️</button>
                <button onclick="sendCommand('pause')">⏸️ Pause</button>
                <button onclick="sendCommand('resume')">▶️ Resume</button>
            </div>

            <select id="effect-select" class="effect-selector" onchange="selectEffect()">
                <option value="">Select Effect...</option>
            </select>
        </div>

        <div class="control-section">
            <h2>Settings</h2>

            <div class="slider-container">
                <div class="slider-label">
                    <span>Brightness</span>
                    <span id="brightness-value">50</span>
                </div>
                <input type="range" id="brightness" min="0" max="100" value="50"
                       oninput="updateSlider('brightness')"
                       onchange="setBrightness()">
            </div>

            <div class="slider-container">
                <div class="slider-label">
                    <span>Speed</span>
                    <span id="speed-value">1.0</span>
                </div>
                <input type="range" id="speed" min="1" max="50" value="10"
                       oninput="updateSlider('speed')"
                       onchange="setSpeed()">
            </div>

            <div class="slider-container">
                <div class="slider-label">
                    <span>Frequency</span>
                    <span id="frequency-value">5</span>
                </div>
                <input type="range" id="frequency" min="1" max="10" value="5"
                       oninput="updateSlider('frequency')"
                       onchange="setFrequency()">
            </div>
        </div>

        <div class="control-section">
            <h2>Daemon Control</h2>
            <div class="button-grid">
                <button class="danger" onclick="sendCommand('stop')">⏹️ Stop Daemon</button>
            </div>
        </div>

        <div id="message" class="message"></div>
    </div>

    <script>
        let effectList = [];

        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'offline') {
                        document.getElementById('offline-warning').style.display = 'block';
                        document.getElementById('controls').style.display = 'none';
                    } else {
                        document.getElementById('offline-warning').style.display = 'none';
                        document.getElementById('controls').style.display = 'block';

                        document.getElementById('current-effect').textContent = data.effect || '-';
                        document.getElementById('state').textContent = data.state || '-';
                        document.getElementById('brightness-display').textContent = data.brightness || '-';
                        document.getElementById('speed-display').textContent = data.speed || '-';
                        document.getElementById('frequency-display').textContent = data.frequency || '-';
                    }
                })
                .catch(err => {
                    console.error('Status update failed:', err);
                });
        }

        function loadEffects() {
            fetch('/api/effects')
                .then(response => response.json())
                .then(data => {
                    effectList = data.effects || [];
                    const select = document.getElementById('effect-select');
                    select.innerHTML = '<option value="">Select Effect...</option>';
                    effectList.forEach(effect => {
                        const option = document.createElement('option');
                        option.value = effect;
                        option.textContent = effect;
                        select.appendChild(option);
                    });
                });
        }

        function sendCommand(cmd, args = null) {
            const payload = args ? {command: cmd, args: args} : {command: cmd};
            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                showMessage(data.message || 'Command sent', data.success ? 'success' : 'error');
                if (data.success) {
                    setTimeout(updateStatus, 100);
                }
            })
            .catch(err => {
                showMessage('Command failed: ' + err, 'error');
            });
        }

        function selectEffect() {
            const effect = document.getElementById('effect-select').value;
            if (effect) {
                sendCommand('set', effect);
            }
        }

        function updateSlider(type) {
            const value = document.getElementById(type).value;
            if (type === 'speed') {
                const speedValue = (value / 10).toFixed(1);
                document.getElementById(type + '-value').textContent = speedValue;
            } else {
                document.getElementById(type + '-value').textContent = value;
            }
        }

        function setBrightness() {
            const value = document.getElementById('brightness').value;
            sendCommand('brightness', value);
        }

        function setSpeed() {
            const value = (document.getElementById('speed').value / 10).toFixed(1);
            sendCommand('speed', value);
        }

        function setFrequency() {
            const value = document.getElementById('frequency').value;
            sendCommand('frequency', value);
        }

        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message ' + type;
            setTimeout(() => {
                msg.style.display = 'none';
            }, 3000);
        }

        // Update status every 2 seconds
        updateStatus();
        loadEffects();
        setInterval(updateStatus, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main control interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    """Get current daemon status"""
    if not is_daemon_running():
        return jsonify({'status': 'offline'})

    try:
        response = send_command('status')
        if response and response.get('status') == 'ok':
            return jsonify({
                'status': 'online',
                'effect': response.get('current_effect', 'Unknown'),
                'state': response.get('state', 'Unknown'),
                'brightness': response.get('brightness', 100),
                'speed': response.get('speed', 1.0),
                'frequency': response.get('frequency', 5)
            })
    except Exception as e:
        pass

    return jsonify({'status': 'offline'})

@app.route('/api/effects')
def get_effects():
    """Get list of available effects"""
    # Import effect lists from demos.py
    try:
        from demos import ALL_EFFECTS
        return jsonify({'effects': list(ALL_EFFECTS.keys())})
    except:
        # Fallback list
        effects = ['plasma', 'fire', 'matrix', 'sparkle', 'meteor', 'spiral',
                   'balls', 'lightning', 'fireworks', 'starfield', 'bubbles', 'comet',
                   'waves', 'rain', 'life', 'tunnel', 'pulse', 'warp',
                   'aurora', 'spectrum', 'swirl', 'ripple']
        return jsonify({'effects': effects})

@app.route('/api/command', methods=['POST'])
def send_control_command():
    """Send a command to the daemon"""
    if not is_daemon_running():
        return jsonify({'success': False, 'message': 'Daemon is not running'})

    data = request.json
    cmd = data.get('command')
    args = data.get('args')

    if not cmd:
        return jsonify({'success': False, 'message': 'No command specified'})

    try:
        if args:
            response = send_command(f"{cmd} {args}")
        else:
            response = send_command(cmd)

        if response and response.get('status') == 'ok':
            return jsonify({
                'success': True,
                'message': response.get('message', 'Command executed'),
                'response': response
            })
        else:
            return jsonify({
                'success': False,
                'message': response.get('message', 'Command failed') if response else 'No response'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def main():
    parser = argparse.ArgumentParser(description='LED Matrix Web Control Interface')
    parser.add_argument('-p', '--port', type=int, default=80,
                        help='Port to run web server on (default: 80, requires sudo)')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()

    if args.port < 1024 and os.geteuid() != 0:
        print(f"Warning: Port {args.port} requires root privileges. Run with sudo or use a port >= 1024")

    print(f"Starting LED Matrix Web Server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    try:
        app.run(host=args.host, port=args.port, debug=False)
    except PermissionError:
        print(f"Error: Permission denied. Port {args.port} requires sudo.")
        sys.exit(1)

if __name__ == '__main__':
    main()
