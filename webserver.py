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
from flask import Flask, render_template, jsonify, request

# Import led_control functions
sys.path.insert(0, os.path.dirname(__file__))
from led_control import send_command, is_daemon_running, SOCKET_PATH

app = Flask(__name__)


@app.route('/')
def index():
    """Serve the main control interface"""
    return render_template('index.html')

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
                'mode': response.get('playback_mode', 'playlist'),
                'effects_running': response.get('effects_running', True)
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
        from effects import DEMOS
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
            # Filter out known problematic fonts
            problematic_fonts = ['tom-thumb.bdf']  # Requires companion .gif/.pbm/.png files
            font_files = [f for f in font_files if f not in problematic_fonts]
            font_files.sort()
            return jsonify({'fonts': font_files})
    except Exception as e:
        print(f"Error getting fonts: {e}")
    return jsonify({'fonts': ['6x10.bdf']})  # Fallback to default

@app.route('/api/effect/<effect_key>/options')
def get_effect_options(effect_key):
    """Get customizable options for a specific effect"""
    try:
        from effects import DEMOS
        from demos import load_text_effect_config
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

@app.route('/api/start', methods=['POST'])
def start_effects():
    """Start/restart the LED effects"""
    if not is_daemon_running():
        return jsonify({'success': False, 'message': 'Daemon process is not running'})

    try:
        response = send_command('start')
        if response and response.get('status') == 'ok':
            return jsonify({'success': True, 'message': response.get('message', 'Effects started')})
        else:
            msg = response.get('message', 'Failed to start effects') if response else 'No response from daemon'
            return jsonify({'success': False, 'message': msg})
    except Exception as e:
        print(f"Error starting effects: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/api/playlists')
def get_playlists():
    """List all playlists"""
    try:
        import playlist_manager
        playlists = playlist_manager.list_playlists()
        return jsonify({'playlists': playlists})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlist/<name>')
def get_playlist(name):
    """Get playlist details"""
    try:
        import playlist_manager
        playlist = playlist_manager.load_playlist(name)
        return jsonify(playlist)
    except FileNotFoundError:
        return jsonify({'error': f"Playlist '{name}' not found"}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlist', methods=['POST'])
def create_playlist():
    """Create new playlist"""
    try:
        import playlist_manager
        data = request.json
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return jsonify({'error': 'Name required'}), 400

        # Check if playlist already exists
        try:
            playlist_manager.load_playlist(name)
            return jsonify({'error': f"Playlist '{name}' already exists"}), 400
        except FileNotFoundError:
            pass  # Good, doesn't exist

        playlist = playlist_manager.create_playlist(name, description)
        playlist_manager.save_playlist(name, playlist)
        return jsonify({'success': True, 'playlist': playlist})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlist/<name>', methods=['PUT'])
def update_playlist(name):
    """Update playlist"""
    try:
        import playlist_manager
        data = request.json

        is_valid, error = playlist_manager.validate_playlist(data)
        if not is_valid:
            return jsonify({'error': error}), 400

        playlist_manager.save_playlist(name, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlist/<name>', methods=['DELETE'])
def delete_playlist(name):
    """Delete playlist"""
    try:
        import playlist_manager

        if name in playlist_manager.BUILTIN_PLAYLISTS:
            return jsonify({'error': 'Cannot delete built-in playlist'}), 403

        success = playlist_manager.delete_playlist(name)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Playlist not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/playlist/<name>/load', methods=['POST'])
def load_playlist(name):
    """Load playlist in daemon"""
    if not is_daemon_running():
        return jsonify({'error': 'Daemon is not running'}), 503

    try:
        response = send_command(f'load_playlist {name}')
        if response and response.get('status') == 'ok':
            return jsonify({'success': True, 'message': response.get('message')})
        return jsonify({'error': response.get('message', 'Failed to load playlist')}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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