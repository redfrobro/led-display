# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python project for controlling a 32x64 RGB LED matrix display using an Adafruit HAT on Raspberry Pi. Features 22 animated effects optimized for different Pi models (Pi Zero for low-power, Pi 3/4 for high-power effects).

## Running

```bash
# Run all 22 effects in a loop (Pi 3/4)
sudo -E env PATH=$PATH python demos.py

# Run low-power effects only (Pi Zero compatible)
sudo -E env PATH=$PATH python demos.py --low-power

# Run high-power effects only (Pi 3/4)
sudo -E env PATH=$PATH python demos.py --high-power

# Run as daemon (background service with remote control)
sudo -E env PATH=$PATH python demos.py --daemon

# Run original animations
sudo -E env PATH=$PATH python blink.py
```

Requires sudo for GPIO access. No build, lint, or test commands are configured.

### Daemon Mode

Run LED effects as a background service with IPC control. The daemon forks to the background and returns control to the shell.

```bash
# Start daemon (runs in background)
sudo python demos.py --daemon
# Or use the convenience script
bin/led-daemon

# Check daemon status
bin/led-control check               # Check if daemon is running
bin/led-control logs                # Show last 20 lines of daemon log
bin/led-control logs 50             # Show last 50 lines of daemon log

# Control the daemon
bin/led-control status              # Show current effect and stats
bin/led-control next                # Skip to next effect
bin/led-control prev                # Go to previous effect
bin/led-control pause               # Pause display
bin/led-control resume              # Resume display
bin/led-control set fireworks       # Switch to specific effect
bin/led-control frequency 8         # Adjust spawn rate (1-10)
bin/led-control brightness 50       # Adjust brightness (0-100)
bin/led-control speed 2.0           # Adjust animation speed (0.1-5.0)
bin/led-control stop                # Stop daemon gracefully
bin/led-control kill                # Force-stop daemon (SIGTERM)

# Daemon files
# Socket: /tmp/led-matrix.sock
# PID file: /tmp/led-matrix.pid
# Log file: /tmp/led-matrix.log
```

The daemon mode supports all regular command-line options (`--effects`, `--night`, `--duration`, `--low-power`, etc.) and can be controlled in real-time via the `led-control` client.

### Web Server Mode

Control the LED matrix through a browser interface. Requires Flask (`pip install flask`). The web server runs as part of the daemon.

```bash
# Start daemon with web server
sudo python demos.py --daemon --webserver
# Or use the convenience script
bin/led-webserver

# Use custom port
sudo python demos.py --daemon --webserver --port 8080

# Access the web interface
# Open browser to: http://raspberry-pi-ip:80
```

The web interface provides:
- Real-time status display (current effect, brightness, speed, frequency, mode)
- Effect control buttons (next, previous, pause, resume)
- Effect selector dropdown (locks in single effect mode)
- Playlist mode toggle button
- Global sliders for brightness, speed, and frequency
- Effect-specific parameter controls in single mode
- Daemon control (stop - shuts down both daemon and web server)

**Playback Modes:**
- **Playlist mode**: Cycles through all effects automatically
- **Single mode**: Locks on one effect with customizable parameters
- Selecting from dropdown switches to single mode
- Next/Previous buttons switch to playlist mode
- Playlist button returns to playlist mode

**Note:** The `bin/led-webserver` script starts the daemon with the web server enabled. Stopping the daemon automatically stops the web server. You can also run `--webserver` standalone (without `--daemon`) to start only the web interface if a daemon is already running separately.

## demos.py Command-Line Options

```
-l, --list              List all available effects
-n, --night             Night mode: darker effects only
-p, --low-power         Low power mode: Pi Zero optimized effects (12 effects)
--high-power            High power mode: Pi 3/4 effects only (10 effects)
-e, --effects EFFECTS   Comma-separated effects (e.g., fireworks,matrix)
-d, --duration SECS     Duration per effect (0 = forever, default: 8)
-s, --shuffle           Randomize effect order
-f, --frequency 1-10    Spawn rate for particle effects (default: 5)
--loops N               Number of loops (0 = infinite)
--pause SECS            Pause between effects (default: 0.5)
-v, --verbose           Enable verbose logging for troubleshooting
--daemon                Run as daemon with IPC control socket
--socket PATH           Unix socket path (default: /tmp/led-matrix.sock)
--webserver             Run web server for browser-based control (requires Flask)
--port PORT             Port for web server (default: 80, requires sudo)
```

### Examples

```bash
python demos.py --list               # See available effects
python demos.py --low-power          # Run Pi Zero optimized effects
python demos.py --high-power         # Run Pi 3/4 effects
python demos.py --night              # Night mode (darker effects)
python demos.py -e fireworks         # Run only fireworks
python demos.py -e matrix,aurora     # Run specific effects
python demos.py -d 15 --shuffle      # 15 sec each, random order
python demos.py -e lightning -f 8    # Frequent lightning storms
python demos.py -f 10                # Max spawn frequency
```

### Effect Names

**Low Power (Pi Zero compatible):**
`plasma`, `fire`, `matrix`, `sparkle`, `meteor`, `spiral`, `balls`, `lightning`, `fireworks`, `starfield`, `bubbles`, `comet`

**High Power (Pi 3/4 recommended):**
`waves`, `rain`, `life`, `tunnel`, `pulse`, `warp`, `aurora`, `spectrum`, `swirl`, `ripple`

### Night Mode Effects

`matrix`, `sparkle`, `balls`, `lightning`, `fireworks`, `starfield`, `aurora`, `ripple`

## Dependencies

- **rgbmatrix** - Adafruit RGB LED Matrix library (rpi-rgb-led-matrix)
- **Pillow** - Image processing

## Architecture

Two standalone scripts with shared matrix initialization pattern:

- **demos.py** - 22 colorful animations split into low-power (12) and high-power (10) categories. Each runs 8 seconds by default, Ctrl+C to exit. Supports daemon mode for background operation.
- **blink.py** - Original animations (`rainbow_fill`, `rand_fill`, `drop_fill`, `fill`, `show_image`)

Both use `hsv_to_rgb()` for color generation. Hardware config: 32 rows × 64 columns, `adafruit-hat` mapping, single parallel chain.
