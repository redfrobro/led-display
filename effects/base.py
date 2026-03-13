"""Base infrastructure for the modular effects system.

This module provides:
- EFFECTS_REGISTRY: Central registry of all effects
- @effect decorator: Auto-registers effects with metadata
- EffectContext: Encapsulates matrix and utilities for effects
"""

from random import randrange
from . import utils
from .utils import hsv_to_rgb, fast_sin, DIST_TABLE, ANGLE_TABLE, ROWS, COLS

# Central registry of all effects
# Format: {'key': {'name': display_name, 'func': function, 'options': {}, 'categories': []}}
EFFECTS_REGISTRY = {}


def effect(key, name, category=None, **options):
    """Decorator to register an effect with metadata.

    Args:
        key: Short identifier for the effect (e.g., 'fireworks')
        name: Display name (e.g., 'Fireworks')
        category: List of categories or single category string
                  Valid categories: 'low_power', 'high_power', 'night', 'special'
        **options: Effect-specific options as (default, description) tuples
                   e.g., particles=(30, "Particles per explosion")

    Example:
        @effect('fireworks', 'Fireworks',
                category=['low_power', 'night'],
                particles=(30, "Particles per explosion"),
                gravity=(0.1, "Gravity strength"))
        def fireworks(ctx, duration=8, frequency=5, particles=30, gravity=0.1, **kwargs):
            # Effect implementation
            pass
    """
    def decorator(func):
        # Normalize category to list
        categories = []
        if category is not None:
            if isinstance(category, str):
                categories = [category]
            else:
                categories = list(category)

        # Register the effect
        EFFECTS_REGISTRY[key] = {
            'name': name,
            'func': func,
            'options': options,
            'categories': categories
        }

        # Return the function unchanged
        return func

    return decorator


class EffectContext:
    """Context object passed to effect functions.

    Encapsulates:
    - Matrix reference for pixel operations
    - Display dimensions (rows, cols)
    - Interrupt checking callback
    - Utility functions (hsv_to_rgb, fast_sin)
    - Precomputed tables (dist_table, angle_table)
    """

    def __init__(self, matrix, rows=ROWS, cols=COLS, check_interrupt=None):
        """Initialize the effect context.

        Args:
            matrix: RGBMatrix instance for pixel operations
            rows: Display height (default: 32)
            cols: Display width (default: 64)
            check_interrupt: Callback that returns True if effect should stop
        """
        self._matrix = matrix
        self._rows = rows
        self._cols = cols
        self._check_interrupt = check_interrupt

        # Expose utility functions
        self.hsv_to_rgb = hsv_to_rgb
        self.fast_sin = fast_sin

        # Expose precomputed tables
        self.dist_table = DIST_TABLE
        self.angle_table = ANGLE_TABLE

    @property
    def matrix(self):
        """The RGBMatrix instance for SetPixel/Clear operations."""
        return self._matrix

    @property
    def rows(self):
        """Display height in pixels."""
        return self._rows

    @property
    def cols(self):
        """Display width in pixels."""
        return self._cols

    def random_hue(self):
        """Return a random hue (0-359). Mood transforms are applied by hsv_to_rgb at render time."""
        return randrange(360)

    def check_interrupt(self):
        """Check if the effect should stop.

        Returns True if:
        - An interrupt callback was provided and it returns True
        - No callback was provided (always returns False)
        """
        if self._check_interrupt is not None:
            return self._check_interrupt()
        return False
