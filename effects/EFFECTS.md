# Modular Effects System

The effects system organizes all LED matrix animations into a modular structure with auto-registration. This makes it easy to add new effects while maintaining compatibility with the existing codebase.

## Directory Structure

```
effects/
├── __init__.py        # Auto-discovery, builds DEMOS dict and category lists
├── base.py            # EffectContext class, @effect decorator, EFFECTS_REGISTRY
├── utils.py           # Shared utilities (hsv_to_rgb, fast_sin, lookup tables)
├── EFFECTS.md         # This documentation
│
├── # Low Power Effects (Pi Zero compatible - 12 effects)
├── plasma.py          # Plasma color waves
├── fire.py            # Realistic fire simulation
├── matrix_rain.py     # Matrix-style digital rain
├── sparkle.py         # Twinkling stars
├── meteor.py          # Meteor shower
├── spiral.py          # Spiral patterns
├── balls.py           # Bouncing balls
├── lightning.py       # Lightning strikes
├── fireworks.py       # Exploding fireworks
├── starfield.py       # Starfield warp
├── bubbles.py         # Rising bubbles
├── comet.py           # Comet trails
│
├── # High Power Effects (Pi 3/4 - 10 effects)
├── waves.py           # Ocean waves
├── rain.py            # Rain storm
├── life.py            # Conway's Game of Life
├── tunnel.py          # 3D tunnel
├── pulse.py           # Pulsing rings
├── warp.py            # Warp speed stars
├── aurora.py          # Aurora borealis
├── spectrum.py        # Spectrum analyzer
├── swirl.py           # Swirl vortex
├── ripple.py          # Water ripples
│
└── # Special Effects
    └── text.py        # Scrolling text display
```

## Adding a New Effect

Adding a new effect is simple - create a new file with a decorated function.

### Step 1: Create a New File

Create a new `.py` file in the `effects/` directory. Name it after your effect (e.g., `snow.py`).

### Step 2: Write the Effect File

Create your effect file with the required imports, decorator, and function:

```python
"""Snow effect - Peaceful falling snow with wind drift."""

import time
from random import random

from .base import effect


@effect('snow', 'Falling Snow',
        category=['low_power', 'night'],
        flake_count=(50, "Number of snowflakes"),
        wind=(0.5, "Wind drift amount"))
def snow(ctx, duration=8, frequency=5, flake_count=50, wind=0.5, check_interrupt=None, **kwargs):
    """Peaceful falling snow with wind drift"""
    start_time = time.time()
    flakes = [{'x': random() * ctx.cols, 'y': random() * ctx.rows,
               'speed': 0.5 + random() * 0.5}
              for _ in range(flake_count)]

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        ctx.matrix.Clear()
        for flake in flakes:
            flake['y'] += flake['speed']
            flake['x'] += (random() - 0.5) * wind

            if flake['y'] >= ctx.rows:
                flake['y'] = 0
                flake['x'] = random() * ctx.cols

            x, y = int(flake['x']), int(flake['y'])
            if 0 <= x < ctx.cols and 0 <= y < ctx.rows:
                ctx.matrix.SetPixel(x, y, 255, 255, 255)

        time.sleep(0.05)
```

### Step 3: Register the Import

Add an import for your new effect in `effects/__init__.py`:

```python
# In __init__.py, add with the appropriate category section:
from . import snow
```

### Step 4: Done!

No other changes needed. The effect is automatically:
- Registered in `EFFECTS_REGISTRY`
- Available in `DEMOS` dict
- Included in category lists based on the `category` parameter
- Available via CLI: `python demos.py -e snow`
- Available via web interface
- Usable in playlists

## The @effect Decorator

```python
@effect(key, name, category=None, **options)
```

**Parameters:**

- `key` (str): Short identifier for the effect (e.g., 'fireworks')
- `name` (str): Display name shown in UI (e.g., 'Fireworks')
- `category` (str or list): Categories this effect belongs to
  - Valid categories: `'low_power'`, `'high_power'`, `'night'`, `'special'`
  - Use a list for multiple categories: `['low_power', 'night']`
- `**options`: Effect-specific options as `(default, description)` tuples

**Example:**

```python
@effect('fireworks', 'Fireworks',
        category=['low_power', 'night'],
        particles=(30, "Particles per explosion"),
        gravity=(0.1, "Gravity strength"))
def fireworks(ctx, duration=8, frequency=5, particles=30, gravity=0.1, **kwargs):
    ...
```

## EffectContext

The `ctx` parameter passed to effects provides access to:

### Properties

- `ctx.matrix` - RGBMatrix instance for pixel operations
- `ctx.rows` - Display height (default: 32)
- `ctx.cols` - Display width (default: 64)

### Methods

- `ctx.check_interrupt()` - Returns True if effect should stop (user command, timeout)
- `ctx.hsv_to_rgb(h, s, v)` - Convert HSV to RGB (h: 0-360, s/v: 0-1)
- `ctx.fast_sin(x)` - Fast sine using lookup table

### Precomputed Tables

- `ctx.dist_table[y][x]` - Distance from center for each pixel
- `ctx.angle_table[y][x]` - Angle from center for each pixel

## Effect Function Signature

```python
def effect_name(ctx, duration=8, frequency=5, **kwargs):
```

**Required parameters:**

- `ctx` - EffectContext (provided automatically)
- `duration` - How long to run in seconds (0 = forever)
- `frequency` - Spawn rate for particle effects (1-10)
- `**kwargs` - Catches any additional parameters

**Optional custom parameters:**

Add any effect-specific parameters with defaults. These will be passed from:
- CLI: `--opts 'effect:param=value'`
- Web interface sliders
- Playlist configurations

## Best Practices

### Pi Zero Optimization (low_power effects)

- Use lookup tables instead of trigonometry: `fast_sin()`, `DIST_TABLE`, `ANGLE_TABLE`
- Limit particle/object counts
- Avoid per-pixel complex calculations
- Target 20-30 FPS (0.03-0.05 second sleep)

### Pi 3/4 Effects (high_power effects)

- Can use `math.sin()`, `math.cos()` per pixel
- Can have many particles/objects
- Can do physics simulations
- Target 30-40 FPS (0.025-0.03 second sleep)

### General Guidelines

- Always check `ctx.check_interrupt()` in the main loop
- Clear the display when appropriate: `ctx.matrix.Clear()`
- Use `ctx.rows` and `ctx.cols` instead of hardcoded dimensions
- Include a docstring describing the effect
- Accept `**kwargs` to handle future parameters gracefully

## Category System

Effects can belong to multiple categories:

| Category | Description | Example Effects |
|----------|-------------|-----------------|
| `low_power` | Optimized for Pi Zero | plasma, fire, matrix |
| `high_power` | Requires Pi 3/4 | waves, life, aurora |
| `night` | Dark, subtle effects | matrix, lightning, stars |
| `special` | Unique requirements | text |

Category lists are auto-generated from the `category` parameter in `@effect`.

## Importing Effects

```python
# Import the DEMOS dict (backward compatible)
from effects import DEMOS

# Import category lists
from effects import LOW_POWER_ORDER, HIGH_POWER_ORDER, NIGHT_MODE

# Import EffectContext for running effects
from effects import EffectContext

# Import utilities
from effects import hsv_to_rgb, fast_sin
```

## Backward Compatibility

The modular system maintains full backward compatibility:

- `DEMOS` dict has the same format: `{'key': (name, func, options)}`
- Category lists are auto-generated with correct ordering
- All CLI options work unchanged
- Web interface works unchanged
- Playlists work unchanged
