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
        .debouncing {
            opacity: 0.7;
            pointer-events: none;
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
            <div class="status-item">
                <span class="status-label">Mode:</span>
                <span class="status-value" id="mode-display">-</span>
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

            <div class="button-grid" style="margin-top: 15px;">
                <button onclick="sendCommand('playlist')">🎵 Playlist Mode</button>
                <button onclick="sendCommand('set', 'text')">📝 Text Mode</button>
            </div>
        </div>

        <div id="effect-options-section" class="control-section" style="display: none;">
            <h2>Effect Options</h2>
            <div id="effect-options-container">
                <!-- Effect-specific options will be dynamically loaded here -->
            </div>
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
        let currentEffectKey = null;
        let debounceTimers = {};
        let isUpdatingFromStatus = false;
        let lastSentValues = {
            brightness: 50,
            speed: 1.0,
            frequency: 5
        };

        // Debounce function to prevent rapid firing of commands
        function debounce(func, wait) {
            return function(...args) {
                const context = this;
                clearTimeout(debounceTimers[func.name]);
                debounceTimers[func.name] = setTimeout(() => {
                    func.apply(context, args);
                }, wait);
            };
        }

        // Throttle function for slider updates
        function throttle(func, wait) {
            let inThrottle;
            return function(...args) {
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, wait);
                }
            };
        }

        function updateStatus() {
            fetch('/api/status')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'offline') {
                        document.getElementById('offline-warning').style.display = 'block';
                        document.getElementById('controls').style.display = 'none';
                        return;
                    }
                    
                    document.getElementById('offline-warning').style.display = 'none';
                    document.getElementById('controls').style.display = 'block';

                    // Prevent slider updates from triggering commands while we update from status
                    isUpdatingFromStatus = true;

                    // Update display values
                    document.getElementById('current-effect').textContent = data.effect || '-';
                    document.getElementById('state').textContent = data.state || '-';
                    document.getElementById('brightness-display').textContent = data.brightness || '-';
                    document.getElementById('speed-display').textContent = data.speed || '-';
                    document.getElementById('frequency-display').textContent = data.frequency || '-';

                    // Update mode display
                    const mode = data.mode || 'playlist';
                    document.getElementById('mode-display').textContent = mode.charAt(0).toUpperCase() + mode.slice(1);

                    // Update dropdown to match current effect
                    const effectKey = data.effect_key;
                    const dropdown = document.getElementById('effect-select');
                    if (effectKey && dropdown.value !== effectKey) {
                        dropdown.value = effectKey;
                    }

                    // Only update sliders if values differ significantly from what we last sent
                    const brightness = parseInt(data.brightness) || 50;
                    const speed = parseFloat(data.speed) || 1.0;
                    const frequency = parseInt(data.frequency) || 5;

                    if (Math.abs(brightness - lastSentValues.brightness) > 5) {
                        document.getElementById('brightness').value = brightness;
                        document.getElementById('brightness-value').textContent = brightness;
                        lastSentValues.brightness = brightness;
                    }

                    if (Math.abs(speed - lastSentValues.speed) > 0.5) {
                        document.getElementById('speed').value = Math.round(speed * 10);
                        document.getElementById('speed-value').textContent = speed.toFixed(1);
                        lastSentValues.speed = speed;
                    }

                    if (Math.abs(frequency - lastSentValues.frequency) > 1) {
                        document.getElementById('frequency').value = frequency;
                        document.getElementById('frequency-value').textContent = frequency;
                        lastSentValues.frequency = frequency;
                    }

                    // Load effect options if effect changed or mode is single
                    if (mode === 'single' && effectKey && effectKey !== currentEffectKey) {
                        loadEffectOptions(effectKey);
                        currentEffectKey = effectKey;
                    } else if (mode !== 'single') {
                        // Hide effect options in playlist mode
                        document.getElementById('effect-options-section').style.display = 'none';
                        currentEffectKey = null;
                    }

                    // Re-enable slider updates
                    setTimeout(() => {
                        isUpdatingFromStatus = false;
                    }, 100);
                })
                .catch(err => {
                    console.error('Status update failed:', err);
                    // If we can't reach the server, show offline warning
                    document.getElementById('offline-warning').style.display = 'block';
                    document.getElementById('controls').style.display = 'none';
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
            
            // Show loading state
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = 'Sending command...';
            messageDiv.className = 'message';
            messageDiv.style.display = 'block';

            fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    messageDiv.textContent = data.message || 'Command sent successfully';
                    messageDiv.className = 'message success';
                    setTimeout(updateStatus, 300); // Wait a bit before updating status
                } else {
                    messageDiv.textContent = data.message || 'Command failed';
                    messageDiv.className = 'message error';
                }
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 3000);
            })
            .catch(err => {
                messageDiv.textContent = 'Command failed: ' + err.message;
                messageDiv.className = 'message error';
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 3000);
                console.error('Command error:', err);
            });
        }

        // Debounced version of sendCommand for sliders
        const debouncedSendCommand = debounce(sendCommand, 300);

        function selectEffect() {
            const effect = document.getElementById('effect-select').value;
            if (effect) {
                sendCommand('set', effect);
            }
        }

        function updateSlider(type) {
            if (isUpdatingFromStatus) return;
            
            const slider = document.getElementById(type);
            const value = slider.value;
            const valueSpan = document.getElementById(type + '-value');
            
            if (type === 'speed') {
                const speedValue = (value / 10).toFixed(1);
                valueSpan.textContent = speedValue;
                lastSentValues.speed = parseFloat(speedValue);
            } else {
                valueSpan.textContent = value;
                if (type === 'brightness') {
                    lastSentValues.brightness = parseInt(value);
                } else if (type === 'frequency') {
                    lastSentValues.frequency = parseInt(value);
                }
            }
        }

        function setBrightness() {
            if (isUpdatingFromStatus) return;
            const value = document.getElementById('brightness').value;
            debouncedSendCommand('brightness', value);
        }

        function setSpeed() {
            if (isUpdatingFromStatus) return;
            const value = (document.getElementById('speed').value / 10).toFixed(1);
            debouncedSendCommand('speed', value);
        }

        function setFrequency() {
            if (isUpdatingFromStatus) return;
            const value = document.getElementById('frequency').value;
            debouncedSendCommand('frequency', value);
        }

        function loadEffectOptions(effectKey) {
            fetch(`/api/effect/${effectKey}/options`)
                .then(response => response.json())
                .then(data => {
                    if (!data.options || data.options.length === 0) {
                        document.getElementById('effect-options-section').style.display = 'none';
                        return;
                    }

                    document.getElementById('effect-options-section').style.display = 'block';
                    const container = document.getElementById('effect-options-container');
                    container.innerHTML = '';

                    data.options.forEach(option => {
                        const optDiv = document.createElement('div');
                        optDiv.className = 'slider-container';

                        if (option.type === 'boolean') {
                            optDiv.innerHTML = `
                                <div class="slider-label">
                                    <span>${option.description}</span>
                                    <span id="${option.key}-value">${option.default ? 'On' : 'Off'}</span>
                                </div>
                                <button id="${option.key}-toggle" onclick="toggleEffectOption('${option.key}')"
                                        style="width: 100%;">${option.default ? 'On' : 'Off'}</button>
                            `;
                        } else if (option.type === 'enum') {
                            // Dropdown for enum types (e.g., font selection)
                            optDiv.innerHTML = `
                                <div class="slider-label">
                                    <span>${option.description}</span>
                                </div>
                                <select id="${option.key}" class="effect-selector" onchange="setEnumEffectOption('${option.key}')">
                                    <option value="">Loading...</option>
                                </select>
                            `;
                            // Populate dropdown based on the key
                            if (option.key === 'font_name') {
                                fetch('/api/fonts')
                                    .then(response => response.json())
                                    .then(fontData => {
                                        const select = document.getElementById(option.key);
                                        select.innerHTML = '';
                                        fontData.fonts.forEach(font => {
                                            const opt = document.createElement('option');
                                            opt.value = font;
                                            opt.textContent = font;
                                            if (font === option.default) {
                                                opt.selected = true;
                                            }
                                            select.appendChild(opt);
                                        });
                                    })
                                    .catch(err => {
                                        console.error('Failed to load fonts:', err);
                                        const select = document.getElementById(option.key);
                                        select.innerHTML = '<option value="6x10.bdf">6x10.bdf</option>';
                                    });
                            }
                        } else if (option.type === 'number') {
                            // Determine appropriate min/max based on default value
                            let min = 0;
                            let max = 100;
                            let step = 1;

                            if (typeof option.default === 'number') {
                                if (option.default <= 1) {
                                    min = 0;
                                    max = 1;
                                    step = 0.1;
                                } else if (option.default <= 10) {
                                    min = 0;
                                    max = Math.max(20, option.default * 2);
                                } else if (option.default <= 100) {
                                    min = 0;
                                    max = Math.max(200, option.default * 2);
                                } else {
                                    min = 0;
                                    max = Math.max(500, option.default * 2);
                                }

                                // Special handling for known option ranges
                                if (option.key === 'intensity' || option.key === 'cooling') {
                                    min = 1;
                                    max = 10;
                                } else if (option.key === 'frequency') {
                                    min = 1;
                                    max = 10;
                                } else if (option.key === 'speed') {
                                    min = 0.1;
                                    max = 5.0;
                                    step = 0.1;
                                } else if (option.key === 'saturation') {
                                    min = 0;
                                    max = 1;
                                    step = 0.1;
                                } else if (option.key === 'gravity') {
                                    min = 0.01;
                                    max = 0.5;
                                    step = 0.01;
                                } else if (option.key === 'color_hue') {
                                    // Color hue uses full 0-360 range
                                    min = 0;
                                    max = 360;
                                    step = 1;
                                }
                            }

                            optDiv.innerHTML = `
                                <div class="slider-label">
                                    <span>${option.description}</span>
                                    <span id="${option.key}-value">${option.default}</span>
                                </div>
                                <input type="range" id="${option.key}"
                                       min="${min}" max="${max}" step="${step}" value="${option.default}"
                                       oninput="updateEffectOption('${option.key}')"
                                       onchange="setEffectOption('${option.key}')">
                            `;
                        } else if (option.type === 'text') {
                            optDiv.innerHTML = `
                                <div class="slider-label">
                                    <span>${option.description}</span>
                                </div>
                                <div style="display: flex; gap: 10px;">
                                    <input type="text" id="${option.key}" value="${option.default}"
                                           style="flex: 1; padding: 10px; border-radius: 5px; border: 2px solid #00ff88; background: #1a1a1a; color: #e0e0e0; font-size: 14px;"
                                           placeholder="Enter text to display"
                                           onkeypress="if(event.key==='Enter') setTextEffectOption('${option.key}')">
                                    <button onclick="setTextEffectOption('${option.key}')"
                                            style="padding: 10px 20px; min-width: 100px;">
                                        💾 Save
                                    </button>
                                </div>
                            `;
                        }
                        container.appendChild(optDiv);
                    });
                })
                .catch(err => {
                    console.error('Failed to load effect options:', err);
                    document.getElementById('effect-options-section').style.display = 'none';
                });
        }

        function updateEffectOption(key) {
            const value = document.getElementById(key).value;
            document.getElementById(key + '-value').textContent = value;
        }

        function setEffectOption(key) {
            if (isUpdatingFromStatus) return;
            const value = document.getElementById(key).value;
            debouncedSendCommand('opt', `${key}=${value}`);
        }

        function setTextEffectOption(key) {
            if (isUpdatingFromStatus) return;
            const value = document.getElementById(key).value;
            if (!value.trim()) {
                showMessage('Please enter some text', 'error');
                return;
            }
            // Show immediate feedback
            showMessage('Saving text...', 'success');
            sendCommand('opt', `${key}=${value}`);
        }

        function setEnumEffectOption(key) {
            if (isUpdatingFromStatus) return;
            const value = document.getElementById(key).value;
            if (!value) {
                showMessage('Please select a value', 'error');
                return;
            }
            // Show immediate feedback
            showMessage(`Updating ${key}...`, 'success');
            sendCommand('opt', `${key}=${value}`);
        }

        function toggleEffectOption(key) {
            if (isUpdatingFromStatus) return;
            const button = document.getElementById(key + '-toggle');
            const valueSpan = document.getElementById(key + '-value');
            const currentValue = button.textContent === 'On';
            const newValue = !currentValue;

            button.textContent = newValue ? 'On' : 'Off';
            valueSpan.textContent = newValue ? 'On' : 'Off';
            sendCommand('opt', `${key}=${newValue}`);
        }

        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message ' + type;
            msg.style.display = 'block';
            setTimeout(() => {
                msg.style.display = 'none';
            }, 3000);
        }

        // Initialize
        function init() {
            updateStatus();
            loadEffects();
            setInterval(updateStatus, 2000);
        }

        // Start when DOM is loaded
        document.addEventListener('DOMContentLoaded', init);
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
            # Get effect key and name
            effect_key = response.get('effect', 'Unknown')
            effect_name = response.get('effect_name') or effect_key
            state = 'PAUSED' if response.get('paused', False) else 'RUNNING'

            return jsonify({
                'status': 'online',
                'effect': effect_name,
                'effect_key': effect_key,
                'state': state,
                'brightness': response.get('brightness', 100),
                'speed': response.get('speed', 1.0),
                'frequency': response.get('frequency', 5),
                'mode': response.get('playback_mode', 'playlist')
            })
        else:
            return jsonify({'status': 'offline'})
    except Exception as e:
        print(f"Error getting status: {e}")
        return jsonify({'status': 'offline'})

@app.route('/api/effects')
def get_effects():
    """Get list of available effects"""
    try:
        from demos import DEMOS
        return jsonify({'effects': list(DEMOS.keys())})
    except Exception as e:
        print(f"Error getting effects: {e}")
        # Fallback list
        effects = ['plasma', 'fire', 'matrix', 'sparkle', 'meteor', 'spiral',
                   'balls', 'lightning', 'fireworks', 'starfield', 'bubbles', 'comet',
                   'waves', 'rain', 'life', 'tunnel', 'pulse', 'warp',
                   'aurora', 'spectrum', 'swirl', 'ripple']
        return jsonify({'effects': effects})

@app.route('/api/fonts')
def get_fonts():
    """Get list of available font files"""
    try:
        fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        if os.path.exists(fonts_dir):
            font_files = [f for f in os.listdir(fonts_dir) if f.endswith('.bdf')]
            font_files.sort()
            return jsonify({'fonts': font_files})
    except Exception as e:
        print(f"Error getting fonts: {e}")
    return jsonify({'fonts': ['6x10.bdf']})  # Fallback to default

@app.route('/api/effect/<effect_key>/options')
def get_effect_options(effect_key):
    """Get customizable options for a specific effect"""
    try:
        from demos import DEMOS, load_text_effect_config
        if effect_key in DEMOS:
            _, _, options = DEMOS[effect_key]
            # Convert options dict to a list with metadata
            options_list = []

            # Load current text effect config if this is the text effect
            text_config = {}
            if effect_key == 'text':
                text_config = load_text_effect_config()

            for key, (default, description) in options.items():
                # Special handling for text effect - load current values from config
                if effect_key == 'text' and key in text_config:
                    default = text_config[key]

                if isinstance(default, bool):
                    option_type = 'boolean'
                elif isinstance(default, (int, float)):
                    option_type = 'number'
                elif key == 'font_name':
                    # Special handling for font_name - use enum type
                    option_type = 'enum'
                else:
                    option_type = 'text'
                options_list.append({
                    'key': key,
                    'default': default,
                    'description': description,
                    'type': option_type
                })
            return jsonify({'options': options_list})
    except Exception as e:
        print(f"Error getting effect options: {e}")
    return jsonify({'options': []})

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
        # Validate and sanitize input
        if cmd in ['brightness', 'frequency']:
            try:
                value = int(args)
                if cmd == 'brightness' and (value < 0 or value > 100):
                    return jsonify({'success': False, 'message': 'Brightness must be between 0 and 100'})
                elif cmd == 'frequency' and (value < 1 or value > 10):
                    return jsonify({'success': False, 'message': 'Frequency must be between 1 and 10'})
            except ValueError:
                return jsonify({'success': False, 'message': f'Invalid value for {cmd}'})
        elif cmd == 'speed':
            try:
                value = float(args)
                if value < 0.1 or value > 5.0:
                    return jsonify({'success': False, 'message': 'Speed must be between 0.1 and 5.0'})
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid speed value'})
        elif cmd == 'opt':
            if not args or '=' not in args:
                return jsonify({'success': False, 'message': 'Invalid option format. Use key=value'})
            
            # Basic validation for opt command
            key, value = args.split('=', 1)
            # Remove any whitespace
            key = key.strip()
            value = value.strip()
            
            # Validate the value based on key
            if key in ['intensity', 'cooling', 'frequency']:
                try:
                    int_val = int(value)
                    if int_val < 1 or int_val > 10:
                        return jsonify({'success': False, 'message': f'{key} must be between 1 and 10'})
                except ValueError:
                    return jsonify({'success': False, 'message': f'Invalid value for {key}'})
            elif key in ['speed', 'gravity']:
                try:
                    float_val = float(value)
                    if key == 'speed' and (float_val < 0.1 or float_val > 5.0):
                        return jsonify({'success': False, 'message': 'Speed must be between 0.1 and 5.0'})
                except ValueError:
                    return jsonify({'success': False, 'message': f'Invalid value for {key}'})
            elif key == 'saturation':
                try:
                    float_val = float(value)
                    if float_val < 0 or float_val > 1:
                        return jsonify({'success': False, 'message': 'Saturation must be between 0 and 1'})
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid saturation value'})

        # Send command to daemon
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
            error_msg = response.get('message', 'Command failed') if response else 'No response from daemon'
            return jsonify({'success': False, 'message': error_msg})
    except Exception as e:
        print(f"Error sending command {cmd}: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

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
        app.run(host=args.host, port=args.port, debug=False, threaded=True)
    except PermissionError:
        print(f"Error: Permission denied. Port {args.port} requires sudo.")
        sys.exit(1)

if __name__ == '__main__':
    main()