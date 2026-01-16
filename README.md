# LED Matrix Display

A Python project for controlling a 32x64 RGB LED matrix display using an Adafruit HAT on Raspberry Pi. Features 22 colorful animated effects with both interactive and daemon modes, optimized for both Pi Zero (low power) and Pi 3/4 (high power).

## Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Software Dependencies](#software-dependencies)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Normal Mode](#normal-mode)
  - [Power Modes](#power-modes)
  - [Daemon Mode](#daemon-mode)
- [Effects](#effects)
  - [Low Power Effects](#low-power-effects-pi-zero-compatible)
  - [High Power Effects](#high-power-effects-pi-34-recommended)
- [Command-Line Options](#command-line-options)
- [Daemon Control Commands](#daemon-control-commands)
- [Effect Customization](#effect-customization)
- [Troubleshooting](#troubleshooting)

## Hardware Requirements

- Raspberry Pi (Pi Zero for low-power effects, Pi 3/4 for all effects)
- 32x64 RGB LED Matrix Panel (HUB75 interface)
- Adafruit RGB Matrix HAT or Bonnet
- 5V power supply (capable of supplying enough current for the matrix)

## Software Dependencies

- Python 3.7+
- [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) - Adafruit RGB LED Matrix library
- Pillow (PIL) - Image processing (optional, for image display)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd led-display
   ```

2. **Install the RGB Matrix library:**
   Follow the installation instructions at [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix).

   Quick install:
   ```bash
   curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh > rgb-matrix.sh
   sudo bash rgb-matrix.sh
   ```

3. **Install Python dependencies:**
   ```bash
   pip install Pillow
   ```

4. **Make scripts executable:**
   ```bash
   chmod +x bin/led-daemon bin/led-control
   ```

## Quick Start

```bash
# Run all 22 effects in a loop (Pi 3/4)
sudo python demos.py

# Run only low-power effects (Pi Zero compatible)
sudo python demos.py --low-power

# Run only high-power effects (Pi 3/4)
sudo python demos.py --high-power

# Run specific effects
sudo python demos.py -e fireworks,matrix,aurora

# Run as a background daemon
sudo python demos.py --daemon

# Control the daemon
bin/led-control status
bin/led-control next
bin/led-control set plasma
```

## Usage

### Normal Mode

Run effects directly in the terminal. Press `Ctrl+C` to exit.

```bash
# Run all 22 effects (8 seconds each, infinite loop)
sudo python demos.py

# Run specific effects
sudo python demos.py -e fireworks
sudo python demos.py -e matrix,aurora,warp

# Night mode (darker effects only)
sudo python demos.py --night

# Run effects for 15 seconds each in random order
sudo python demos.py -d 15 --shuffle

# Run a single effect forever
sudo python demos.py -e fire -d 0

# Run through all effects twice
sudo python demos.py --loops 2

# Increase spawn frequency for particle effects
sudo python demos.py -f 10
```

### Power Modes

The effects are optimized for different Raspberry Pi models:

```bash
# Low power mode - 12 effects optimized for Pi Zero
# Uses lookup tables and simplified calculations
sudo python demos.py --low-power

# High power mode - 10 effects that utilize more CPU
# Features complex simulations like Game of Life, water physics, etc.
sudo python demos.py --high-power

# Default - All 22 effects (recommended for Pi 3/4)
sudo python demos.py
```

### Daemon Mode

Run effects as a background service with remote control via Unix socket.

**Starting the daemon:**
```bash
# Start daemon (forks to background, returns to shell)
sudo python demos.py --daemon

# Or use the convenience script
bin/led-daemon

# Start with low-power effects only
sudo python demos.py --daemon --low-power

# Start with specific effects
sudo python demos.py --daemon -e fireworks,matrix,lightning

# Start in night mode
sudo python demos.py --daemon --night
```

**Controlling the daemon:**
```bash
# Check if daemon is running
bin/led-control check

# Get current status
bin/led-control status

# Navigate effects
bin/led-control next
bin/led-control prev

# Switch to specific effect
bin/led-control set fireworks

# Pause/resume
bin/led-control pause
bin/led-control resume

# Adjust parameters
bin/led-control frequency 8      # Spawn rate (1-10)
bin/led-control brightness 50    # Brightness (0-100)
bin/led-control speed 2.0        # Animation speed (0.1-5.0)

# View logs
bin/led-control logs
bin/led-control logs 50          # Last 50 lines

# Stop the daemon
bin/led-control stop             # Graceful shutdown
bin/led-control kill             # Force stop (SIGTERM)
```

**Daemon files:**
| File | Description |
|------|-------------|
| `/tmp/led-matrix.sock` | Unix socket for IPC |
| `/tmp/led-matrix.pid` | Process ID file |
| `/tmp/led-matrix.log` | Daemon log file |

## Effects

### Low Power Effects (Pi Zero Compatible)

These 12 effects are optimized for Pi Zero with lookup tables and efficient algorithms:

| Effect | Description | Best Settings |
|--------|-------------|---------------|
| `plasma` | Smooth psychedelic plasma waves | `speed=1.5` |
| `fire` | Realistic rising flame effect | `intensity=6, cooling=2` |
| `matrix` | The Matrix digital rain | `speed=1.5, length=15` |
| `sparkle` | Twinkling stars | `saturation=0.5` |
| `meteor` | Diagonal meteors with glowing trails | `length=15, speed=1.2` |
| `spiral` | Rotating spiral pattern from center | `speed=8, density=15` |
| `balls` | Multiple bouncing balls with trails | `count=8, size=2` |
| `lightning` | Random lightning bolts | `branches=true, color=240` |
| `fireworks` | Exploding fireworks | `particles=50, gravity=0.15` |
| `starfield` | 3D starfield flying through space | `count=150, speed=0.03` |
| `bubbles` | Colorful bubbles rising up | `size=3, wobble=3` |
| `comet` | Orbiting comet with colorful trail | `trail=30, speed=0.2` |

### High Power Effects (Pi 3/4 Recommended)

These 10 effects use more complex algorithms and are designed for Pi 3/4:

| Effect | Description | Best Settings |
|--------|-------------|---------------|
| `waves` | Realistic ocean waves with foam | `wave_count=4, speed=1.2` |
| `rain` | Rain storm with splashing droplets | `intensity=70, splash_size=4` |
| `life` | Conway's Game of Life (colorful) | `density=35, colorful=true` |
| `tunnel` | 3D tunnel flying effect | `speed=1.5, rings=25` |
| `pulse` | Pulsing rings from multiple sources | `sources=4, speed=1.2` |
| `warp` | Star Trek style warp speed | `star_count=300, speed=1.5` |
| `aurora` | Northern lights / Aurora Borealis | `bands=6, speed=0.8` |
| `spectrum` | Audio visualizer style bars | `bars=16, reactive=true` |
| `swirl` | Multiple rotating vortices | `vortices=3, speed=1.2` |
| `ripple` | Water ripple pond effect | `auto_drops=true, drop_rate=20` |

**Night mode effects** (darker, less intense):
`matrix`, `sparkle`, `balls`, `lightning`, `fireworks`, `starfield`, `aurora`, `ripple`

## Command-Line Options

```
Usage: python demos.py [options]

Options:
  -l, --list              List all available effects and exit
  --list-opts             List all effect-specific options and exit
  -n, --night             Night mode: darker effects only
  -p, --low-power         Low power mode: Pi Zero optimized effects (12 effects)
  --high-power            High power mode: Pi 3/4 effects only (10 effects)
  -e, --effects EFFECTS   Comma-separated effects (e.g., fireworks,matrix)
  -d, --duration SECS     Duration per effect (0 = forever, default: 8)
  -s, --shuffle           Randomize effect order
  -f, --frequency 1-10    Spawn rate for particle effects (default: 5)
  --loops N               Number of loops (0 = infinite, default: 0)
  --pause SECS            Pause between effects (default: 0.5)
  -o, --opts OPTIONS      Effect-specific options (see below)
  -v, --verbose           Enable verbose logging
  --daemon                Run as daemon with IPC control socket
  --socket PATH           Unix socket path (default: /tmp/led-matrix.sock)
```

## Daemon Control Commands

| Command | Description |
|---------|-------------|
| `status` | Get current effect, uptime, and settings |
| `next` | Skip to next effect |
| `prev` | Go to previous effect |
| `pause` | Pause current effect (freeze display) |
| `resume` | Resume paused effect |
| `set <effect>` | Switch to specific effect by name |
| `list` | List available effects in current playlist |
| `stop` | Graceful shutdown |
| `kill` | Force-stop daemon (SIGTERM) |
| `check` | Check if daemon is running |
| `logs [N]` | Show last N lines of daemon log (default: 20) |
| `frequency <1-10>` | Adjust spawn frequency |
| `brightness <0-100>` | Adjust brightness level |
| `speed <0.1-5.0>` | Adjust animation speed multiplier |
| `opt <key>=<value>` | Set effect-specific option |

## Effect Customization

Each effect has customizable options. Use `--list-opts` to see all options:

```bash
python demos.py --list-opts
```

**Setting options via command line:**
```bash
# Single effect with options
python demos.py -e balls --opts "balls:count=8,size=2"

# Multiple effects with options
python demos.py --opts "balls:count=3;fireworks:particles=50,gravity=0.2"

# High power effect with options
python demos.py -e aurora --opts "aurora:bands=7,speed=0.5"
```

**Setting options in daemon mode:**
```bash
bin/led-control opt particles=50
bin/led-control opt gravity=0.2
```

### Available Options by Effect

#### Low Power Effects

**plasma:**
- `speed` (default: 1.0) - Animation speed multiplier

**fire:**
- `intensity` (default: 4) - Spark intensity 1-10
- `cooling` (default: 3) - Cooling rate 1-5

**matrix:**
- `speed` (default: 1.0) - Drop speed multiplier
- `length` (default: 10) - Average trail length

**sparkle:**
- `saturation` (default: 0.3) - Color saturation 0-1

**meteor:**
- `length` (default: 12) - Meteor trail length
- `speed` (default: 1.0) - Speed multiplier

**spiral:**
- `speed` (default: 5) - Rotation speed
- `density` (default: 10) - Color band density

**balls:**
- `count` (default: 5) - Number of balls
- `size` (default: 1) - Ball radius
- `trail` (default: 10) - Trail length

**lightning:**
- `branches` (default: true) - Enable branching
- `fade` (default: 1.0) - Fade speed multiplier
- `color` (default: 240) - Hue 0-360 (240=blue, 0=red, -1=random)

**fireworks:**
- `particles` (default: 30) - Particles per explosion
- `gravity` (default: 0.1) - Gravity strength

**starfield:**
- `count` (default: 100) - Number of stars
- `speed` (default: 0.02) - Travel speed

**bubbles:**
- `size` (default: 2) - Max bubble size
- `wobble` (default: 2) - Wobble amount

**comet:**
- `trail` (default: 25) - Trail length
- `speed` (default: 0.15) - Orbit speed

#### High Power Effects

**waves:**
- `wave_count` (default: 3) - Number of wave layers
- `speed` (default: 1.0) - Wave speed multiplier

**rain:**
- `intensity` (default: 50) - Rain intensity
- `splash_size` (default: 3) - Splash ripple size

**life:**
- `density` (default: 30) - Initial cell density %
- `colorful` (default: true) - Colorful cells

**tunnel:**
- `speed` (default: 1.0) - Flight speed
- `rings` (default: 20) - Number of rings

**pulse:**
- `sources` (default: 3) - Number of pulse sources
- `speed` (default: 1.0) - Pulse expansion speed

**warp:**
- `star_count` (default: 200) - Number of stars
- `speed` (default: 1.0) - Warp speed multiplier

**aurora:**
- `bands` (default: 5) - Number of aurora bands
- `speed` (default: 1.0) - Movement speed

**spectrum:**
- `bars` (default: 16) - Number of frequency bars
- `reactive` (default: true) - Quick reactive mode

**swirl:**
- `vortices` (default: 2) - Number of vortices
- `speed` (default: 1.0) - Rotation speed

**ripple:**
- `auto_drops` (default: true) - Automatic water drops
- `drop_rate` (default: 30) - Drop frequency

## Troubleshooting

### Permission Errors

The RGB matrix library requires root access for GPIO:
```bash
# Always run with sudo
sudo python demos.py
```

If you get permission errors with daemon files:
```bash
sudo rm -f /tmp/led-matrix.pid /tmp/led-matrix.log /tmp/led-matrix.sock
sudo python demos.py --daemon
```

### "Daemon is not running" but process exists

Check the daemon logs for errors:
```bash
bin/led-control logs
# Or directly:
cat /tmp/led-matrix.log
```

Common issues:
- Matrix initialization failed (check GPIO connections)
- Socket permission issues
- Another instance is already running

### Display Not Working

1. Check hardware connections
2. Verify power supply is adequate (5V, high amperage)
3. Check that the HAT is properly seated
4. Try running without daemon mode first:
   ```bash
   sudo python demos.py -e plasma -d 0
   ```

### Slow Performance on Pi Zero

Use low-power mode for Pi Zero:
```bash
sudo python demos.py --low-power
```

The high-power effects (waves, life, aurora, etc.) require more CPU and may not run smoothly on Pi Zero.

### Realtime Priority Warning

The warning "Can't set realtime thread priority" is normal in daemon mode and can be ignored. The daemon uses `disable_hardware_pulsing=True` to work around this.

### Killing a Stuck Daemon

```bash
# Try graceful stop first
bin/led-control stop

# If that doesn't work, force kill
bin/led-control kill

# If still stuck, find and kill manually
cat /tmp/led-matrix.pid
sudo kill -9 <pid>

# Clean up files
sudo rm -f /tmp/led-matrix.pid /tmp/led-matrix.log /tmp/led-matrix.sock
```

## Project Structure

```
led-display/
├── demos.py           # Main demo script with 22 effects and daemon mode
├── blink.py           # Original simple animations
├── led_control.py     # Control client module
├── bin/
│   ├── led-daemon     # Convenience script to start daemon
│   └── led-control    # CLI client for daemon control
├── CLAUDE.md          # Development instructions
└── README.md          # This file
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
