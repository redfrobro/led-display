"""Modular effects system for LED matrix display.

Auto-discovers and registers all effects from submodules, providing:
- DEMOS: Dict of all effects in legacy format for backward compatibility
- EFFECTS_REGISTRY: New-style registry with full metadata
- Category lists: LOW_POWER_ORDER, HIGH_POWER_ORDER, NIGHT_MODE, DEFAULT_ORDER
- EffectContext: Context object passed to effect functions

Usage:
    from effects import DEMOS, EffectContext, LOW_POWER_ORDER

    # Run an effect the old way
    name, func, options = DEMOS['fireworks']
    func(duration=8, frequency=5, check_interrupt=None)

    # Run an effect the new way with context
    ctx = EffectContext(matrix, rows=32, cols=64, check_interrupt=callback)
    from effects.low_power import fireworks
    fireworks(ctx, duration=8, frequency=5)
"""

# Import base infrastructure
from .base import EFFECTS_REGISTRY, EffectContext, effect
from .utils import hsv_to_rgb, fast_sin, SIN_TABLE, DIST_TABLE, ANGLE_TABLE, ROWS, COLS

# Import individual effect modules to trigger registration
# The @effect decorators in these modules will populate EFFECTS_REGISTRY

# Low power effects (Pi Zero compatible)
from . import plasma
from . import fire
from . import matrix_rain
from . import sparkle
from . import meteor
from . import spiral
from . import balls
from . import lightning
from . import fireworks
from . import starfield
from . import bubbles
from . import comet

# High power effects (Pi 3/4)
from . import waves
from . import rain
from . import life
from . import tunnel
from . import pulse
from . import warp
from . import aurora
from . import spectrum
from . import swirl
from . import ripple

# Special effects
from . import text


def _build_demos_dict():
    """Build the legacy DEMOS dict from EFFECTS_REGISTRY.

    Returns dict in format:
        {'key': (display_name, function, {option: (default, description)})}
    """
    demos = {}
    for key, info in EFFECTS_REGISTRY.items():
        demos[key] = (info['name'], info['func'], info['options'])
    return demos


def _build_category_list(category):
    """Build an ordered list of effect keys for a given category.

    Maintains the original order defined in the effect modules.
    """
    # Define the expected order for each category
    # This ensures backward compatibility with the original ordering
    orders = {
        'low_power': ['plasma', 'fire', 'matrix', 'sparkle', 'meteor', 'spiral',
                      'balls', 'lightning', 'fireworks', 'starfield', 'bubbles', 'comet'],
        'high_power': ['waves', 'rain', 'life', 'tunnel', 'pulse', 'warp',
                       'aurora', 'spectrum', 'swirl', 'ripple'],
        'night': ['matrix', 'sparkle', 'balls', 'lightning', 'fireworks',
                  'starfield', 'aurora', 'ripple'],
    }

    if category in orders:
        # Return predefined order, filtered to only include registered effects
        return [k for k in orders[category] if k in EFFECTS_REGISTRY]

    # For unknown categories, collect from registry
    result = []
    for key, info in EFFECTS_REGISTRY.items():
        if category in info.get('categories', []):
            result.append(key)
    return result


# Build the DEMOS dict for backward compatibility
DEMOS = _build_demos_dict()

# Build category lists
LOW_POWER_ORDER = _build_category_list('low_power')
HIGH_POWER_ORDER = _build_category_list('high_power')
NIGHT_MODE = _build_category_list('night')
DEFAULT_ORDER = LOW_POWER_ORDER + HIGH_POWER_ORDER

# Public API
__all__ = [
    # Core classes
    'EffectContext',
    'effect',

    # Registries
    'EFFECTS_REGISTRY',
    'DEMOS',

    # Category lists
    'LOW_POWER_ORDER',
    'HIGH_POWER_ORDER',
    'NIGHT_MODE',
    'DEFAULT_ORDER',

    # Utilities
    'hsv_to_rgb',
    'fast_sin',
    'SIN_TABLE',
    'DIST_TABLE',
    'ANGLE_TABLE',
    'ROWS',
    'COLS',
]
