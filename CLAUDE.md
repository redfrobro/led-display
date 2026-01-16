# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python project for controlling a 32x64 RGB LED matrix display using an Adafruit HAT on Raspberry Pi. Displays various animations including rainbow gradients, random fills, and image display.

## Running

```bash
# Run demo showcase (12 animations in a loop)
sudo -E env PATH=$PATH python demos.py

# Run original animations
sudo -E env PATH=$PATH python blink.py
```

Requires sudo for GPIO access. No build, lint, or test commands are configured.

## demos.py Command-Line Options

```
-l, --list              List all available effects
-n, --night             Night mode: darker effects only
-e, --effects EFFECTS   Comma-separated effects (e.g., fireworks,matrix)
-d, --duration SECS     Duration per effect (0 = forever, default: 8)
-s, --shuffle           Randomize effect order
-f, --frequency 1-10    Spawn rate for particle effects (default: 5)
--loops N               Number of loops (0 = infinite)
--pause SECS            Pause between effects (default: 0.5)
```

### Examples

```bash
python demos.py --list               # See available effects
python demos.py --night              # Night mode (darker effects)
python demos.py -e fireworks         # Run only fireworks
python demos.py -e matrix,starfield  # Run specific effects
python demos.py -d 15 --shuffle      # 15 sec each, random order
python demos.py -e lightning -f 8    # Frequent lightning storms
python demos.py -f 10                # Max spawn frequency
```

### Effect Names

`plasma`, `fire`, `matrix`, `sparkle`, `meteor`, `spiral`, `balls`, `lightning`, `fireworks`, `starfield`, `bubbles`, `comet`

### Night Mode Effects

`matrix`, `sparkle`, `balls`, `lightning`, `fireworks`, `starfield`

## Dependencies

- **rgbmatrix** - Adafruit RGB LED Matrix library (rpi-rgb-led-matrix)
- **Pillow** - Image processing

## Architecture

Two standalone scripts with shared matrix initialization pattern:

- **demos.py** - 12 colorful animations (plasma, fire, matrix rain, sparkle, meteor shower, spiral, bouncing balls, lightning, fireworks, starfield, rising bubbles, comet). Each runs 8 seconds, Ctrl+C to exit.
- **blink.py** - Original animations (`rainbow_fill`, `rand_fill`, `drop_fill`, `fill`, `show_image`)

Both use `hsv_to_rgb()` for color generation. Hardware config: 32 rows × 64 columns, `adafruit-hat` mapping, single parallel chain.
