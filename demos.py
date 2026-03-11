#!/usr/bin/env python3
"""LED Matrix Demo - Main application.

This module provides:
- Matrix initialization
- Daemon mode with IPC control
- Web server integration
- CLI argument parsing
- Text effect configuration

Effects are implemented in the effects/ module.
"""

import time
import math
import sys
import os
import argparse
import logging
import socket
import threading
import json
from random import randrange, random, choice, shuffle

# Setup logging (disabled by default)
logger = logging.getLogger('led-demos')
logger.addHandler(logging.NullHandler())

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Import from effects module
from effects import (
    DEMOS, EFFECTS_REGISTRY, EffectContext,
    LOW_POWER_ORDER, HIGH_POWER_ORDER, NIGHT_MODE, DEFAULT_ORDER,
    hsv_to_rgb
)

ROWS = 32
COLS = 64

options = RGBMatrixOptions()
options.hardware_mapping = 'adafruit-hat'
options.rows = ROWS
options.cols = COLS
options.parallel = 1

# Matrix will be initialized later (after fork in daemon mode, or now in normal mode)
matrix = None

def get_network_info():
    """Get network information: IP addresses and hostnames"""
    import subprocess
    import re

    info = []

    # Get hostname
    try:
        hostname = socket.gethostname()
        info.append(f"Host: {hostname}")
        info.append(f"  pi.local: http://{hostname}.jevin")
    except Exception as e:
        logger.warning(f"Could not get hostname: {e}")

    # Get IP addresses using multiple methods
    ip_addresses = []

    # Method 1: socket.gethostbyname_ex
    try:
        hostname = socket.gethostname()
        _, _, ip_list = socket.gethostbyname_ex(hostname)
        ip_addresses.extend(ip_list)
    except Exception as e:
        logger.debug(f"Could not get IP via gethostbyname_ex: {e}")

    # Method 2: socket.getaddrinfo
    try:
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                addrs = socket.getaddrinfo(hostname, None, family, socket.SOCK_DGRAM)
                for addr in addrs:
                    ip = addr[4][0]
                    if ip not in ip_addresses and not ip.startswith('127.'):
                        ip_addresses.append(ip)
            except:
                pass
    except Exception as e:
        logger.debug(f"Could not get IP via getaddrinfo: {e}")

    # Method 3: Try ip command (Linux/Raspberry Pi)
    try:
        result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/', line)
                if match:
                    ip = match.group(1)
                    if not ip.startswith('127.') and ip not in ip_addresses:
                        ip_addresses.append(ip)
    except (subprocess.SubprocessError, FileNotFoundError, TimeoutError) as e:
        logger.debug(f"Could not get IP via ip command: {e}")

    # Method 4: Try ifconfig command (older systems)
    try:
        result = subprocess.run(['ifconfig', '-a'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    if not ip.startswith('127.') and ip not in ip_addresses:
                        ip_addresses.append(ip)
    except (subprocess.SubprocessError, FileNotFoundError, TimeoutError) as e:
        logger.debug(f"Could not get IP via ifconfig: {e}")

    # Filter and deduplicate IPs
    unique_ips = []
    for ip in ip_addresses:
        if ip not in unique_ips and not ip.startswith('127.'):
            unique_ips.append(ip)

    # Add IP addresses to info
    for ip in unique_ips:
        info.append(f"IP: {ip}")
        info.append(f"  http://{ip}")

    # If no IPs found, add a message
    if not unique_ips and not info:
        info.append("No network found")
        info.append("Connect to network")

    return info


def init_matrix(for_daemon=False):
    """Initialize or reinitialize the matrix"""
    global matrix

    if for_daemon:
        daemon_options = RGBMatrixOptions()
        daemon_options.hardware_mapping = 'adafruit-hat'
        daemon_options.rows = ROWS
        daemon_options.cols = COLS
        daemon_options.parallel = 1
        daemon_options.drop_privileges = False
        daemon_options.disable_hardware_pulsing = True
        matrix = RGBMatrix(options=daemon_options)
    else:
        matrix = RGBMatrix(options=options)


# Effect options storage
EFFECT_OPTIONS = {}


def validate_effect_option(effect_name, key, value):
    """Validate effect option value to prevent crashes"""
    # Skip validation for non-numeric values
    if not isinstance(value, (int, float)):
        return True

    # Critical parameters that must be positive non-zero
    if key in ['rings', 'bars', 'vortices', 'sources', 'count', 'size', 'length', 'wave_count', 'intensity', 'cooling', 'frequency']:
        if value <= 0:
            return False

    # Additional specific validations
    if key == 'rings' and value > 100:
        return False
    if key == 'bars' and value > 64:
        return False
    if key == 'vortices' and value > 10:
        return False
    if key == 'sources' and value > 10:
        return False
    if key == 'scroll_speed' and value > 500:
        return False

    # Positive-only parameters (can be zero)
    if key in ['particles', 'density', 'drop_rate', 'spawn_rate', 'scroll_speed']:
        if value < 0:
            return False

    return True


def parse_effect_opts(opts_string):
    """Parse effect options string like 'fireworks:particles=50,gravity=0.2;balls:count=8'"""
    if not opts_string:
        return {}

    result = {}
    for effect_opts in opts_string.split(";"):
        if ":" not in effect_opts:
            continue
        effect_name, opts = effect_opts.split(":", 1)
        effect_name = effect_name.strip()
        if effect_name not in DEMOS:
            print(f"Warning: Unknown effect '{effect_name}' in options, skipping")
            continue

        result[effect_name] = {}
        for opt in opts.split(","):
            if "=" not in opt:
                continue
            key, value = opt.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Try to convert to appropriate type
            try:
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass

            # Validate value
            if not validate_effect_option(effect_name, key, value):
                print(f"Warning: Invalid value '{value}' for {effect_name}.{key}, skipping")
                continue

            result[effect_name][key] = value

    return result


# Text display configuration
TEXT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'text_config.json')

def load_text_config():
    """Load custom text from config file, or return default"""
    if os.path.exists(TEXT_CONFIG_FILE):
        try:
            with open(TEXT_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('text', 'Hello World')
        except Exception as e:
            logger.warning(f"Failed to load text config: {e}")
    return 'Hello World'

def save_text_config(text):
    """Save custom text to config file"""
    try:
        config = {}
        if os.path.exists(TEXT_CONFIG_FILE):
            try:
                with open(TEXT_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            except:
                pass
        config['text'] = text
        with open(TEXT_CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        logger.info(f"Saved text config: {text}")
    except Exception as e:
        logger.error(f"Failed to save text config: {e}")

def load_text_effect_config():
    """Load all text effect configuration from config file"""
    defaults = {
        'text': 'Hello World',
        'font_name': '6x10.bdf',
        'color_hue': 200,
        'scroll_speed': 2.0
    }
    if os.path.exists(TEXT_CONFIG_FILE):
        try:
            with open(TEXT_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return {**defaults, **config}
        except Exception as e:
            logger.warning(f"Failed to load text effect config: {e}")
    return defaults

def save_text_effect_option(key, value):
    """Save a text effect option to config file"""
    try:
        config = {}
        if os.path.exists(TEXT_CONFIG_FILE):
            try:
                with open(TEXT_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            except:
                pass
        config[key] = value
        with open(TEXT_CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        logger.info(f"Saved text effect option: {key}={value}")
    except Exception as e:
        logger.error(f"Failed to save text effect option: {e}")


def get_effect_options(effect_name):
    """Get merged options for an effect (defaults + custom)"""
    if effect_name not in DEMOS:
        return {}

    defaults = {k: v[0] for k, v in DEMOS[effect_name][2].items()}
    custom = EFFECT_OPTIONS.get(effect_name, {})
    return {**defaults, **custom}


def run_effect(effect_key, ctx, duration, frequency, opts=None):
    """Run an effect with the given context and parameters."""
    if effect_key not in DEMOS:
        logger.error(f"Unknown effect: {effect_key}")
        return

    name, func, _ = DEMOS[effect_key]
    effect_opts = opts or {}

    # Special handling for text effect - pass config loaders
    if effect_key == 'text':
        effect_opts['config_loader'] = load_text_effect_config
        effect_opts['config_saver'] = save_text_effect_option
        effect_opts['project_dir'] = os.path.dirname(__file__)

    # Run the effect
    func(
        ctx,
        duration=duration,
        frequency=frequency,
        check_interrupt=ctx._check_interrupt,
        **effect_opts
    )


class DaemonController:
    """Controls daemon mode with threading and Unix socket IPC"""

    def __init__(self, socket_path, args, effect_keys, webserver_enabled=False, webserver_port=80):
        self.socket_path = socket_path
        self.args = args
        self.effect_keys = effect_keys
        self.running = True
        self.effects_running = True
        self.paused = False
        self.current_effect = None
        self.effect_index = 0
        self.skip_to_next = False
        self.skip_to_prev = False
        self.jump_to_effect = False
        self.start_time = time.time()

        # Adjustable parameters
        self.frequency = args.frequency
        self.brightness = 100
        self.speed = 1.0
        self.duration = args.duration
        self.effect_options = EFFECT_OPTIONS.copy()

        # Playback mode
        self.playback_mode = 'playlist'

        # Playlist state
        self.current_playlist_name = None
        self.playlist_data = None
        self.effect_durations = {}
        self.effect_params = {}

        # Web server options
        self.webserver_enabled = webserver_enabled
        self.webserver_port = webserver_port

        if self.webserver_enabled:
            try:
                import flask
            except ImportError:
                print("ERROR: Flask is not importable. Web server will be disabled.")
                self.webserver_enabled = False

        # Threading
        self.effect_thread = None
        self.ipc_thread = None
        self.webserver_thread = None
        self.flask_server = None
        self.cond = threading.Condition()

    def should_interrupt(self):
        """Called by effect functions to check for commands"""
        with self.cond:
            if not self.running or not self.effects_running or self.skip_to_next or self.skip_to_prev or self.jump_to_effect:
                return True

        while True:
            with self.cond:
                if not self.paused or not self.running or not self.effects_running:
                    break
            time.sleep(0.1)

        with self.cond:
            return not self.running or not self.effects_running

    def apply_brightness(self, r, g, b):
        """Scale RGB values by brightness percentage"""
        factor = self.brightness / 100.0
        return int(r * factor), int(g * factor), int(b * factor)

    def effect_worker(self):
        """Run effects in a loop"""
        logger.info("Effect worker thread started")

        # Display network info on startup
        ctx = EffectContext(matrix, ROWS, COLS, check_interrupt=self.should_interrupt)
        display_startup_info(ctx)

        loop_count = 0

        try:
            while self.running and self.effects_running and (self.args.loops == 0 or loop_count < self.args.loops):
                with self.cond:
                    mode = self.playback_mode
                    start_idx = self.effect_index
                    if mode == 'single':
                        effects_to_play = [(start_idx, self.effect_keys[start_idx])]
                    else:
                        num_effects = len(self.effect_keys)
                        effects_to_play = [
                            ((start_idx + i) % num_effects, self.effect_keys[(start_idx + i) % num_effects])
                            for i in range(num_effects)
                        ]

                for idx, key in effects_to_play:
                    with self.cond:
                        if not self.running or not self.effects_running:
                            break
                        self.effect_index = idx
                        self.current_effect = key
                        self.skip_to_next = False
                        self.skip_to_prev = False
                        self.jump_to_effect = False

                        # Get per-effect parameters
                        if key == "text" and mode == 'single':
                            effect_duration = 0
                        else:
                            effect_duration = self.effect_durations.get(key, self.duration)

                        effect_params = self.effect_params.get(key, {})
                        effect_brightness = effect_params.get('brightness') if effect_params.get('brightness') is not None else self.brightness
                        effect_frequency = effect_params.get('frequency') if effect_params.get('frequency') is not None else self.frequency
                        effect_speed = effect_params.get('speed') if effect_params.get('speed') is not None else self.speed

                        opts = get_effect_options(key)
                        playlist_opts = effect_params.get('options', {})
                        opts.update(playlist_opts)
                        opts.update(self.effect_options.get(key, {}))

                        if 'speed' not in opts:
                            opts['speed'] = effect_speed

                    name, func, _ = DEMOS[key]
                    logger.info(f"Starting effect '{key}': {name}")

                    # Create context for this effect
                    ctx = EffectContext(matrix, ROWS, COLS, check_interrupt=self.should_interrupt)

                    duration = effect_duration if effect_duration > 0 else 999999
                    run_effect(key, ctx, duration, effect_frequency, opts)

                    with self.cond:
                        if not self.running or not self.effects_running:
                            break
                        if self.jump_to_effect:
                            break
                        if self.skip_to_prev:
                            self.effect_index = (idx - 1) % len(self.effect_keys)
                            self.playback_mode = 'playlist'
                            break
                        if self.skip_to_next:
                            self.effect_index = (idx + 1) % len(self.effect_keys)
                            self.playback_mode = 'playlist'
                            break

                        if mode == 'playlist':
                            self.effect_index = (idx + 1) % len(self.effect_keys)

                    matrix.Clear()
                    time.sleep(self.args.pause)

                loop_count += 1

                if self.args.shuffle and self.running and self.effects_running and (self.args.loops == 0 or loop_count < self.args.loops):
                    shuffle(self.effect_keys)

        except Exception as e:
            logger.error(f"Effect worker error: {e}", exc_info=True)
        finally:
            logger.info("Effect worker thread exiting")
            matrix.Clear()

    def handle_command(self, cmd):
        """Process a command and return JSON response"""
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        with self.cond:
            if command == "status":
                uptime = int(time.time() - self.start_time)
                return {
                    "status": "ok",
                    "effect": self.current_effect,
                    "effect_name": DEMOS[self.current_effect][0] if self.current_effect else None,
                    "index": self.effect_index,
                    "total": len(self.effect_keys),
                    "paused": self.paused,
                    "uptime": uptime,
                    "frequency": self.frequency,
                    "brightness": self.brightness,
                    "speed": self.speed,
                    "duration": self.duration,
                    "playback_mode": self.playback_mode,
                    "playlist": self.current_playlist_name,
                    "playlist_effect_count": len(self.effect_keys) if self.current_playlist_name else None,
                    "effects_running": self.effects_running
                }

            elif command == "next":
                self.skip_to_next = True
                return {"status": "ok", "message": "Skipping to next effect"}

            elif command == "prev":
                self.skip_to_prev = True
                return {"status": "ok", "message": "Going to previous effect"}

            elif command == "pause":
                self.paused = True
                return {"status": "ok", "message": "Paused"}

            elif command == "resume":
                self.paused = False
                return {"status": "ok", "message": "Resumed"}

            elif command == "set":
                if not arg or arg not in DEMOS:
                    return {"status": "error", "message": f"Unknown effect: {arg}"}
                if arg in self.effect_keys:
                    target_idx = self.effect_keys.index(arg)
                    self.effect_index = target_idx
                    self.playback_mode = 'single'
                    self.duration = 0  # Run forever in single mode
                    self.jump_to_effect = True
                    return {"status": "ok", "message": f"Locked on {arg}"}
                else:
                    self.effect_keys.append(arg)
                    self.effect_index = len(self.effect_keys) - 1
                    self.playback_mode = 'single'
                    self.duration = 0  # Run forever in single mode
                    self.jump_to_effect = True
                    return {"status": "ok", "message": f"Locked on {arg} (special effect)"}

            elif command == "playlist":
                self.playback_mode = 'playlist'
                self.skip_to_next = True
                return {"status": "ok", "message": "Playlist mode enabled"}

            elif command == "stop":
                self.effects_running = False
                self.cond.notify_all()
                return {"status": "ok", "message": "Stopping effects"}

            elif command == "start":
                if not self.effects_running:
                    self.effects_running = True
                    self.cond.notify_all()
                    self.effect_thread = threading.Thread(target=self.effect_worker, daemon=False)
                    self.effect_thread.start()
                    return {"status": "ok", "message": "Effects started"}
                else:
                    return {"status": "ok", "message": "Effects already running"}

            elif command == "list":
                effects = [{"key": k, "name": DEMOS[k][0]} for k in self.effect_keys]
                return {"status": "ok", "effects": effects}

            elif command == "frequency":
                if not arg:
                    return {"status": "error", "message": "Missing frequency value"}
                try:
                    freq = int(arg)
                    if 1 <= freq <= 10:
                        self.frequency = freq
                        return {"status": "ok", "frequency": freq, "message": f"Frequency set to {freq}"}
                    else:
                        return {"status": "error", "message": "Frequency must be 1-10"}
                except ValueError:
                    return {"status": "error", "message": "Invalid frequency value"}

            elif command == "brightness":
                if not arg:
                    return {"status": "error", "message": "Missing brightness value"}
                try:
                    bright = int(arg)
                    if 0 <= bright <= 100:
                        self.brightness = bright
                        return {"status": "ok", "brightness": bright, "message": f"Brightness set to {bright}%"}
                    else:
                        return {"status": "error", "message": "Brightness must be 0-100"}
                except ValueError:
                    return {"status": "error", "message": "Invalid brightness value"}

            elif command == "speed":
                if not arg:
                    return {"status": "error", "message": "Missing speed value"}
                try:
                    spd = float(arg)
                    if 0.1 <= spd <= 5.0:
                        self.speed = spd
                        return {"status": "ok", "speed": spd, "message": f"Speed set to {spd}x"}
                    else:
                        return {"status": "error", "message": "Speed must be 0.1-5.0"}
                except ValueError:
                    return {"status": "error", "message": "Invalid speed value"}

            elif command == "duration":
                if not arg:
                    return {"status": "error", "message": "Missing duration value"}
                try:
                    dur = int(arg)
                    if dur >= 0:
                        self.duration = dur
                        if dur == 0:
                            return {"status": "ok", "duration": dur, "message": "Duration set to forever"}
                        else:
                            return {"status": "ok", "duration": dur, "message": f"Duration set to {dur}s"}
                    else:
                        return {"status": "error", "message": "Duration must be >= 0"}
                except ValueError:
                    return {"status": "error", "message": "Invalid duration value"}

            elif command == "opt":
                if not arg or "=" not in arg:
                    return {"status": "error", "message": "Usage: opt key=value"}
                key, value = arg.split("=", 1)
                if self.current_effect:
                    if self.current_effect not in self.effect_options:
                        self.effect_options[self.current_effect] = {}
                    try:
                        if value.lower() in ("true", "false"):
                            value = value.lower() == "true"
                        elif "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass

                    if not validate_effect_option(self.current_effect, key, value):
                        return {"status": "error", "message": f"Invalid value '{value}' for {key}. Must be positive."}

                    if self.current_effect == "text" and key == "font_name":
                        font_path = os.path.join(os.path.dirname(__file__), 'fonts', value)
                        if not os.path.exists(font_path):
                            return {"status": "error", "message": f"Font file not found: {value}"}
                        try:
                            font = graphics.Font()
                            font.LoadFont(font_path)
                        except Exception as e:
                            return {"status": "error", "message": f"Font '{value}' cannot be loaded: {str(e)}"}

                    self.effect_options[self.current_effect][key] = value

                    if self.current_effect == "text":
                        save_text_effect_option(key, value)

                    self.jump_to_effect = True
                    return {"status": "ok", "message": f"Set {key}={value} for {self.current_effect}"}
                else:
                    return {"status": "error", "message": "No effect currently running"}

            elif command == "load_playlist":
                if not arg:
                    return {"status": "error", "message": "Missing playlist name"}

                try:
                    import playlist_manager
                    playlist_data = playlist_manager.load_playlist(arg)
                    self.effect_keys = [e['key'] for e in playlist_data['effects']]
                    self.playlist_data = playlist_data
                    self.current_playlist_name = arg

                    self.effect_durations = {}
                    self.effect_params = {}

                    for effect in playlist_data['effects']:
                        key = effect['key']
                        if 'duration' in effect and effect['duration'] > 0:
                            self.effect_durations[key] = effect['duration']
                        if 'params' in effect or 'options' in effect:
                            self.effect_params[key] = {
                                'brightness': effect.get('params', {}).get('brightness'),
                                'frequency': effect.get('params', {}).get('frequency'),
                                'speed': effect.get('params', {}).get('speed'),
                                'options': effect.get('options', {})
                            }

                    self.playback_mode = 'playlist'
                    self.effect_index = 0
                    self.skip_to_next = False
                    self.skip_to_prev = False
                    self.jump_to_effect = True

                    return {
                        "status": "ok",
                        "message": f"Loaded playlist '{arg}' with {len(self.effect_keys)} effects",
                        "effect_count": len(self.effect_keys)
                    }

                except FileNotFoundError:
                    return {"status": "error", "message": f"Playlist '{arg}' not found"}
                except ValueError as e:
                    return {"status": "error", "message": f"Invalid playlist: {str(e)}"}
                except Exception as e:
                    return {"status": "error", "message": f"Error loading playlist: {str(e)}"}

            elif command == "list_playlists":
                try:
                    import playlist_manager
                    playlists = playlist_manager.list_playlists()
                    return {"status": "ok", "playlists": playlists}
                except Exception as e:
                    return {"status": "error", "message": f"Error listing playlists: {str(e)}"}

            elif command == "save_playlist":
                if not arg:
                    return {"status": "error", "message": "Missing playlist name"}

                try:
                    import playlist_manager
                    playlist_data = playlist_manager.create_playlist(arg, "Saved from daemon")

                    for key in self.effect_keys:
                        effect = {
                            'key': key,
                            'duration': self.effect_durations.get(key, self.duration),
                            'params': {},
                            'options': {}
                        }
                        if key in self.effect_params:
                            params = self.effect_params[key]
                            if params.get('brightness') is not None:
                                effect['params']['brightness'] = params['brightness']
                            if params.get('frequency') is not None:
                                effect['params']['frequency'] = params['frequency']
                            if params.get('speed') is not None:
                                effect['params']['speed'] = params['speed']
                            if params.get('options'):
                                effect['options'] = params['options']
                        if key in self.effect_options:
                            effect['options'].update(self.effect_options[key])
                        playlist_data['effects'].append(effect)

                    playlist_manager.save_playlist(arg, playlist_data)
                    return {
                        "status": "ok",
                        "message": f"Saved playlist '{arg}' with {len(self.effect_keys)} effects"
                    }

                except Exception as e:
                    return {"status": "error", "message": f"Error saving playlist: {str(e)}"}

            elif command == "current_playlist":
                if self.current_playlist_name:
                    return {
                        "status": "ok",
                        "playlist": self.current_playlist_name,
                        "effect_count": len(self.effect_keys)
                    }
                else:
                    return {
                        "status": "ok",
                        "playlist": None,
                        "message": "No playlist loaded"
                    }

            else:
                return {"status": "error", "message": f"Unknown command: {command}"}

    def ipc_worker(self):
        """Listen for commands on Unix socket"""
        logger.info(f"IPC worker starting on {self.socket_path}")

        try:
            os.unlink(self.socket_path)
        except OSError:
            if os.path.exists(self.socket_path):
                raise

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.socket_path)
        sock.listen(1)
        sock.settimeout(1.0)

        logger.info(f"Listening on {self.socket_path}")

        try:
            while self.running:
                try:
                    conn, _ = sock.accept()
                    try:
                        data = conn.recv(1024).decode('utf-8').strip()
                        if data:
                            logger.debug(f"Received command: {data}")
                            response = self.handle_command(data)
                            conn.sendall((json.dumps(response) + "\n").encode('utf-8'))
                    finally:
                        conn.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"IPC error: {e}", exc_info=True)
        finally:
            sock.close()
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass
            logger.info("IPC worker exiting")

    def webserver_worker(self):
        """Run Flask web server"""
        logger.info(f"Web server starting on port {self.webserver_port}")

        try:
            import flask
        except ImportError:
            logger.error("Flask is not importable. Web server disabled.")
            return

        try:
            import webserver
            from werkzeug.serving import make_server
            import logging as flask_logging
            flask_log = flask_logging.getLogger('werkzeug')
            flask_log.setLevel(flask_logging.ERROR)

            self.flask_server = make_server(
                '0.0.0.0',
                self.webserver_port,
                webserver.app,
                threaded=True
            )

            logger.info(f"Web server listening on port {self.webserver_port}")
            self.flask_server.serve_forever()

        except ImportError:
            logger.error("Failed to import webserver module. Check Flask installation.")
        except Exception as e:
            logger.error(f"Web server error: {e}", exc_info=True)
        finally:
            logger.info("Web server exiting")

    def start(self, fork=True):
        """Start daemon threads"""
        pid_file = "/tmp/led-matrix.pid"
        log_path = "/tmp/led-matrix.log"

        for f in [pid_file, log_path]:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except OSError:
                pass

        if fork:
            pid = os.fork()
            if pid > 0:
                with open(pid_file, "w") as f:
                    f.write(str(pid))
                print(f"Daemon started with PID {pid}")
                sys.exit(0)

            os.setsid()
            log_file = open(log_path, 'a')
            os.dup2(log_file.fileno(), sys.stdout.fileno())
            os.dup2(log_file.fileno(), sys.stderr.fileno())

            try:
                logger.info("Initializing matrix after fork...")
                init_matrix(for_daemon=True)
                logger.info("Matrix initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize matrix: {e}", exc_info=True)
                sys.exit(1)
        else:
            with open(pid_file, "w") as f:
                f.write(str(os.getpid()))
            logger.info(f"PID file written: {pid_file}")

        self.effect_thread = threading.Thread(target=self.effect_worker, daemon=False)
        self.ipc_thread = threading.Thread(target=self.ipc_worker, daemon=False)

        self.effect_thread.start()
        self.ipc_thread.start()

        if self.webserver_enabled:
            self.webserver_thread = threading.Thread(target=self.webserver_worker, daemon=False)
            self.webserver_thread.start()
            logger.info(f"Daemon started with web server on port {self.webserver_port}")
        else:
            logger.info("Daemon started")

    def wait(self):
        """Wait for threads to finish"""
        try:
            self.ipc_thread.join()
            if self.webserver_thread:
                self.webserver_thread.join()
        except KeyboardInterrupt:
            logger.info("Interrupted, shutting down...")
            self.running = False
            self.effects_running = False

            if self.flask_server:
                try:
                    logger.info("Shutting down web server...")
                    self.flask_server.shutdown()
                except Exception as e:
                    logger.error(f"Error shutting down web server: {e}")

            self.ipc_thread.join(timeout=2)
            if self.webserver_thread:
                self.webserver_thread.join(timeout=2)
        finally:
            if self.flask_server:
                try:
                    self.flask_server.shutdown()
                except Exception as e:
                    logger.debug(f"Web server already shut down: {e}")

            pid_file = "/tmp/led-matrix.pid"
            try:
                os.unlink(pid_file)
                logger.info("PID file removed")
            except OSError:
                pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="LED Matrix Demo - Colorful animations for RGB LED matrix",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demos.py                      # Run all demos in a loop
  python demos.py --list               # List available effects
  python demos.py --list-opts          # List effect options
  python demos.py --night              # Night mode (darker effects)
  python demos.py -e fireworks         # Run only fireworks
  python demos.py -e matrix,starfield  # Run specific effects
  python demos.py -d 15 --shuffle      # 15 sec each, random order
  python demos.py -e fire -d 0         # Run fire effect forever
  python demos.py --loops 2            # Run through all effects twice
  python demos.py -f 10                # Max spawn frequency (intense!)
  python demos.py -e lightning -f 8    # Frequent lightning storms

Effect-specific options (use --list-opts to see all):
  python demos.py -e balls --opts "balls:count=8,size=2"
  python demos.py -e fireworks --opts "fireworks:particles=50,gravity=0.2"
  python demos.py --opts "balls:count=3;starfield:count=200"
        """
    )
    parser.add_argument("-l", "--list", action="store_true",
                        help="List all available effects and exit")
    parser.add_argument("--list-opts", action="store_true",
                        help="List all effect-specific options and exit")
    parser.add_argument("-n", "--night", action="store_true",
                        help="Night mode: darker effects only")
    parser.add_argument("-p", "--low-power", action="store_true",
                        help="Low power mode: use only Pi Zero optimized effects (12 effects)")
    parser.add_argument("--high-power", action="store_true",
                        help="High power mode: use only Pi 3/4 optimized effects (10 effects)")
    parser.add_argument("-o", "--opts", type=str, default=None,
                        help="Effect-specific options (e.g., 'balls:count=8,size=2;fireworks:particles=50')")
    parser.add_argument("-e", "--effects", type=str, default=None,
                        help="Comma-separated list of effects to run (e.g., fireworks,matrix,starfield)")
    parser.add_argument("--playlist", type=str, default=None,
                        help="Load custom playlist (e.g., 'my-custom')")
    parser.add_argument("-d", "--duration", type=float, default=8,
                        help="Duration of each effect in seconds (0 = run forever, default: 8)")
    parser.add_argument("-s", "--shuffle", action="store_true",
                        help="Randomize the order of effects")
    parser.add_argument("--loops", type=int, default=0,
                        help="Number of loops (0 = infinite, default: 0)")
    parser.add_argument("-f", "--frequency", type=int, default=5, choices=range(1, 11),
                        metavar="1-10", help="Spawn frequency for effects like fireworks/lightning (1=rare, 10=frequent, default: 5)")
    parser.add_argument("--pause", type=float, default=0.5,
                        help="Pause between effects in seconds (default: 0.5)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose logging for troubleshooting")
    parser.add_argument("--daemon", action="store_true",
                        help="Run as a daemon with IPC control socket")
    parser.add_argument("--socket", type=str, default="/tmp/led-matrix.sock",
                        help="Unix socket path for daemon mode (default: /tmp/led-matrix.sock)")
    parser.add_argument("--webserver", action="store_true",
                        help="Run web server for browser-based control (requires Flask)")
    parser.add_argument("--port", type=int, default=80,
                        help="Port for web server (default: 80, requires sudo)")
    return parser.parse_args()


def setup_logging(verbose):
    """Configure logging based on verbose flag"""
    if verbose:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")


def display_startup_info(ctx, duration=15):
    """Display network information on startup"""
    try:
        network_info = get_network_info()
        if not network_info:
            network_info = ["No network", "info"]

        # Show at most 2 lines: prefer IP and URL
        # Pick the first IP line and the first http:// line
        ip_line = next((l for l in network_info if l.startswith("IP:")), None)
        url_line = next((l.strip() for l in network_info if "http://" in l and not "jevin" in l), None)
        if ip_line and url_line:
            display_lines = [ip_line, url_line]
        else:
            display_lines = [l.strip() for l in network_info[:2]]

        text = "\n".join(display_lines)
        logger.info(f"Displaying startup network info")

        config = load_text_effect_config()
        font_name = config.get('font_name', '6x10.bdf')
        color_hue = config.get('color_hue', 200)

        if ctx.matrix:
            run_effect('text', ctx, duration, 5, {
                'text': text,
                'font_name': font_name,
                'scroll_speed': 0,
                'color_hue': color_hue
            })
            ctx.matrix.Clear()
    except Exception as e:
        logger.error(f"Failed to display startup info: {e}")


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)

    logger.debug(f"Arguments: {vars(args)}")

    # List effects and exit
    if args.list:
        print("Available effects:")
        for key, (name, _, _) in DEMOS.items():
            print(f"  {key:12} - {name}")
        sys.exit(0)

    # List effect options and exit
    if args.list_opts:
        print("Effect-specific options:")
        print("Use with: --opts 'effect:option=value,option2=value2'")
        print()
        for key, (name, _, opts) in DEMOS.items():
            print(f"  {key}:")
            for opt_name, (default, desc) in opts.items():
                print(f"    {opt_name:12} = {default!r:8} - {desc}")
        sys.exit(0)

    # Parse effect-specific options
    if args.opts:
        EFFECT_OPTIONS.update(parse_effect_opts(args.opts))
        logger.debug(f"Custom effect options: {EFFECT_OPTIONS}")

    # Ensure playlists directory exists and migrate built-in playlists
    import playlist_manager
    playlists_dir = os.path.join(os.path.dirname(__file__), 'playlists')
    if not os.path.exists(playlists_dir):
        os.makedirs(playlists_dir)

    builtin_playlists = ['low-power', 'high-power', 'night', 'all']
    missing_playlists = [p for p in builtin_playlists
                         if not os.path.exists(os.path.join(playlists_dir, f'{p}.json'))]

    if missing_playlists:
        logger.info(f"Creating missing built-in playlists: {', '.join(missing_playlists)}")
        playlist_manager.migrate_builtin_playlists()
        logger.info("Built-in playlists created")

    # Determine which effects to run
    loaded_playlist_data = None
    if args.playlist:
        try:
            playlist_data = playlist_manager.load_playlist(args.playlist)
            loaded_playlist_data = playlist_data
            effect_keys = [e['key'] for e in playlist_data['effects']]
            logger.debug(f"Loaded playlist '{args.playlist}' with {len(effect_keys)} effects")
        except FileNotFoundError:
            print(f"Error: Playlist '{args.playlist}' not found")
            print(f"Use 'bin/led-playlist list' to see available playlists")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: Invalid playlist '{args.playlist}': {e}")
            sys.exit(1)
    elif args.effects:
        effect_keys = [e.strip() for e in args.effects.split(",")]
        for key in effect_keys:
            if key not in DEMOS:
                print(f"Error: Unknown effect '{key}'")
                print(f"Use --list to see available effects")
                sys.exit(1)
    elif args.low_power:
        try:
            playlist_data = playlist_manager.load_playlist('low-power')
            loaded_playlist_data = playlist_data
            effect_keys = [e['key'] for e in playlist_data['effects']]
        except (FileNotFoundError, ValueError):
            effect_keys = LOW_POWER_ORDER.copy()
    elif args.high_power:
        try:
            playlist_data = playlist_manager.load_playlist('high-power')
            loaded_playlist_data = playlist_data
            effect_keys = [e['key'] for e in playlist_data['effects']]
        except (FileNotFoundError, ValueError):
            effect_keys = HIGH_POWER_ORDER.copy()
    elif args.night:
        try:
            playlist_data = playlist_manager.load_playlist('night')
            loaded_playlist_data = playlist_data
            effect_keys = [e['key'] for e in playlist_data['effects']]
        except (FileNotFoundError, ValueError):
            effect_keys = NIGHT_MODE.copy()
    else:
        try:
            playlist_data = playlist_manager.load_playlist('all')
            loaded_playlist_data = playlist_data
            effect_keys = [e['key'] for e in playlist_data['effects']]
        except (FileNotFoundError, ValueError):
            effect_keys = DEFAULT_ORDER.copy()

    # Extract per-effect parameters from playlist
    effect_durations = {}
    effect_params = {}
    if loaded_playlist_data is not None:
        for effect in loaded_playlist_data['effects']:
            key = effect['key']
            if 'duration' in effect and effect['duration'] > 0:
                effect_durations[key] = effect['duration']
            if 'params' in effect or 'options' in effect:
                effect_params[key] = {
                    'brightness': effect.get('params', {}).get('brightness'),
                    'frequency': effect.get('params', {}).get('frequency'),
                    'speed': effect.get('params', {}).get('speed'),
                    'options': effect.get('options', {})
                }

    if args.shuffle:
        shuffle(effect_keys)
        logger.debug("Effect order shuffled")

    logger.info(f"Running effects: {effect_keys}")
    logger.info(f"Duration: {args.duration}s, Frequency: {args.frequency}, Pause: {args.pause}s")

    # Web server mode (standalone, without daemon)
    if args.webserver and not args.daemon:
        print("LED Matrix Web Server (Standalone Mode)")
        print(f"Port: {args.port}")
        print("Open your browser to control the LED matrix")
        print(f"Make sure daemon is running: sudo python demos.py --daemon")
        print()

        try:
            import flask
        except ImportError:
            print("Error: Flask is not importable.")
            print()
            print("Flask is required for the web server. Possible solutions:")
            print()
            print("1. Activate your virtual environment and install Flask:")
            print("   source /path/to/venv/bin/activate")
            print("   pip install flask")
            print()
            print("2. Use your virtual environment's Python interpreter directly:")
            print("   sudo /path/to/venv/bin/python demos.py --webserver")
            print()
            sys.exit(1)

        try:
            import webserver
            webserver.app.run(host='0.0.0.0', port=args.port, debug=False)
        except ImportError as e:
            print(f"Error: Failed to import webserver module: {e}")
            sys.exit(1)
        except PermissionError:
            print(f"Error: Permission denied. Port {args.port} requires sudo.")
            sys.exit(1)
        sys.exit(0)

    # Initialize matrix for normal mode
    if not args.daemon:
        logger.debug(f"Initializing matrix: {ROWS}x{COLS}, mapping={options.hardware_mapping}")
        init_matrix(for_daemon=False)
        logger.debug("Matrix initialized successfully")

    # Daemon mode
    if args.daemon:
        print("LED Matrix Daemon")
        print(f"Socket: {args.socket}")
        print(f"PID file: /tmp/led-matrix.pid")
        print(f"Log file: /tmp/led-matrix.log")
        print(f"Effects: {', '.join(effect_keys)}")
        if args.webserver:
            print(f"Web server: http://0.0.0.0:{args.port}")
        print()

        if not args.verbose:
            setup_logging(True)

        daemon = DaemonController(
            args.socket,
            args,
            effect_keys,
            webserver_enabled=args.webserver,
            webserver_port=args.port
        )
        daemon.start(fork=True)
        daemon.wait()
        logger.info("Daemon finished")
    else:
        # Normal mode
        print("LED Matrix Demo - Press Ctrl+C to exit")
        print(f"Effects: {', '.join(effect_keys)}")
        print(f"Duration: {'forever' if args.duration == 0 else f'{args.duration}s'} each")
        if args.loops > 0:
            print(f"Loops: {args.loops}")
        print()

        # Create context for normal mode
        ctx = EffectContext(matrix, ROWS, COLS, check_interrupt=lambda: False)

        # Display network info on startup
        display_startup_info(ctx)

        try:
            loop_count = 0
            while args.loops == 0 or loop_count < args.loops:
                for key in effect_keys:
                    name, func, _ = DEMOS[key]
                    effect_duration = effect_durations.get(key, args.duration)
                    effect_param = effect_params.get(key, {})
                    effect_frequency = effect_param.get('frequency', args.frequency)
                    effect_speed = effect_param.get('speed', 1.0)
                    playlist_opts = effect_param.get('options', {})

                    opts = get_effect_options(key)
                    opts.update(playlist_opts)
                    if 'speed' not in opts:
                        opts['speed'] = effect_speed

                    logger.debug(f"Starting effect '{key}' with options: {opts}")
                    print(f"Now showing: {name}")

                    start = time.time()
                    duration = effect_duration if effect_duration > 0 else 999999
                    run_effect(key, ctx, duration, effect_frequency, opts)

                    elapsed = time.time() - start
                    logger.debug(f"Effect '{key}' finished after {elapsed:.2f}s")

                    matrix.Clear()
                    time.sleep(args.pause)

                loop_count += 1
                logger.debug(f"Completed loop {loop_count}")
                if args.shuffle and (args.loops == 0 or loop_count < args.loops):
                    shuffle(effect_keys)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            print("\nExiting...")
            matrix.Clear()

        logger.info("Demo finished")
