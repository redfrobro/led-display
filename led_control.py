"""
LED Matrix Control Client Module
Sends commands to the LED matrix daemon via Unix socket
"""

import socket
import sys
import json
import os
import signal


SOCKET_PATH = "/tmp/led-matrix.sock"
PID_FILE = "/tmp/led-matrix.pid"
LOG_FILE = "/tmp/led-matrix.log"


def is_daemon_running():
    """Check if daemon is running by checking PID file and process"""
    if not os.path.exists(PID_FILE):
        return False

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        # Check if process is running
        try:
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks if process exists
            return True
        except PermissionError:
            # Process exists but we don't have permission to signal it (daemon running as root)
            # Fall back to checking if socket exists and is connectable
            return os.path.exists(SOCKET_PATH)
        except ProcessLookupError:
            # Process doesn't exist
            return False
    except (OSError, ValueError):
        return False


def send_command(cmd):
    """Send command to daemon and return response"""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(SOCKET_PATH)
            sock.sendall((cmd + "\n").encode('utf-8'))
            sock.settimeout(2.0)  # Timeout for reading response

            # Read response until newline (daemon sends JSON lines)
            response_data = b""
            max_response_size = 65536  # 64KB maximum response size
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response_data += chunk
                    if len(response_data) > max_response_size:
                        raise ValueError("Response too large")
                    if b'\n' in response_data:
                        # Extract up to newline
                        response_data = response_data.split(b'\n')[0]
                        break
                except socket.timeout:
                    break

            if not response_data:
                return {"status": "error", "message": "No response from daemon (timeout or empty)"}
            response = response_data.decode('utf-8', errors='ignore').strip()
            return json.loads(response)
        finally:
            sock.close()
    except FileNotFoundError:
        return {"status": "error", "message": f"Cannot connect to daemon socket: {SOCKET_PATH}. Start it with: bin/led-daemon"}
    except ConnectionRefusedError:
        return {"status": "error", "message": f"Connection refused to {SOCKET_PATH}. Is the daemon running?"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def format_response(response):
    """Format JSON response for display"""
    if response.get("status") == "error":
        print(f"Error: {response.get('message', 'Unknown error')}")
        return

    if "message" in response:
        print(response["message"])

    # Special formatting for status command
    if "effect" in response and "uptime" in response:
        print(f"Current Effect: {response['effect_name']} ({response['effect']})")
        print(f"Progress: {response['index'] + 1}/{response['total']}")
        print(f"Status: {'PAUSED' if response['paused'] else 'RUNNING'}")
        print(f"Uptime: {response['uptime']}s")
        print(f"Frequency: {response['frequency']}")
        print(f"Brightness: {response['brightness']}%")
        print(f"Speed: {response['speed']}x")
        duration = response.get('duration', 0)
        print(f"Duration: {'forever' if duration == 0 else f'{duration}s'}")

    # Special formatting for list command
    if "effects" in response:
        print("Available effects:")
        for effect in response["effects"]:
            print(f"  {effect['key']:12} - {effect['name']}")


def kill_daemon():
    """Force kill the daemon process"""
    if not os.path.exists(PID_FILE):
        print("Error: PID file not found. Daemon may not be running.")
        return False

    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to daemon process {pid}")

        # Clean up PID file
        try:
            os.unlink(PID_FILE)
        except OSError:
            pass

        return True
    except (ValueError, ProcessLookupError, OSError) as e:
        print(f"Error: {e}")
        return False


def check_daemon():
    """Check if daemon is running"""
    if is_daemon_running():
        print("Daemon is running")
        return True
    else:
        print("Daemon is not running")
        return False


def show_logs(lines=20):
    """Show last N lines of daemon log"""
    if not os.path.exists(LOG_FILE):
        print(f"Log file not found: {LOG_FILE}")
        return False

    try:
        with open(LOG_FILE, 'r') as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                print(line.rstrip())
        return True
    except Exception as e:
        print(f"Error reading log: {e}")
        return False


def print_usage():
    """Print usage information"""
    print("LED Matrix Control Client")
    print()
    print("Usage: led-control <command> [args]")
    print()
    print("Commands:")
    print("  status              Get current effect and daemon status")
    print("  next                Skip to next effect")
    print("  prev                Go to previous effect")
    print("  pause               Pause current effect")
    print("  resume              Resume paused effect")
    print("  set <effect>        Switch to specific effect (single mode)")
    print("  playlist            Switch to playlist mode")
    print("  stop                Stop the daemon gracefully")
    print("  kill                Force-stop the daemon (SIGTERM)")
    print("  check               Check if daemon is running")
    print("  logs [N]            Show last N lines of daemon log (default: 20)")
    print("  list                List available effects")
    print("  frequency <1-10>    Adjust spawn frequency")
    print("  brightness <0-100>  Adjust brightness level")
    print("  speed <0.1-5.0>     Adjust animation speed")
    print("  duration <seconds>  Set effect duration (0 = forever)")
    print("  opt <key>=<value>   Set effect-specific option")
    print()
    print("Playlist Commands:")
    print("  load_playlist <name>    Load and play a custom playlist")
    print("  list_playlists          List all available playlists")
    print("  save_playlist <name>    Save current state as a new playlist")
    print("  current_playlist        Show currently loaded playlist")
    print()
    print("Examples:")
    print("  led-control check")
    print("  led-control logs")
    print("  led-control logs 50")
    print("  led-control status")
    print("  led-control next")
    print("  led-control set fireworks")
    print("  led-control playlist")
    print("  led-control frequency 8")
    print("  led-control brightness 50")
    print("  led-control speed 2.0")
    print("  led-control duration 15")
    print("  led-control opt particles=50")
    print("  led-control load_playlist my-favorites")
    print("  led-control list_playlists")
    print("  led-control save_playlist my-custom")
    print("  led-control stop")
    print("  led-control kill")


def main(args=None):
    """Main entry point for led-control"""
    if args is None:
        args = sys.argv[1:]

    if len(args) < 1 or args[0] in ("-h", "--help", "help"):
        print_usage()
        return 0

    command = args[0].lower()

    # Handle special commands
    if command == "kill":
        return 0 if kill_daemon() else 1

    elif command == "check":
        return 0 if check_daemon() else 1

    elif command == "logs":
        lines = 20
        if len(args) > 1:
            try:
                lines = int(args[1])
            except ValueError:
                print(f"Error: Invalid line count '{args[1]}'")
                return 1
        return 0 if show_logs(lines) else 1

    # Build command from arguments
    cmd = " ".join(args)

    # Check if daemon is running before sending command
    if not is_daemon_running():
        print("Error: Daemon is not running")
        print("Start it with: bin/led-daemon")
        return 1

    # Send command and display response
    response = send_command(cmd)
    format_response(response)

    return 0 if response.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
