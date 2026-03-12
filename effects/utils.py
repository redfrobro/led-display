"""Shared utilities for LED matrix effects.

This module contains common helper functions used across all effects:
- Color conversion (HSV to RGB)
- Fast trigonometry using lookup tables
- Precomputed distance and angle tables
"""

import math

# Matrix dimensions (constants for table generation)
ROWS = 32
COLS = 64

# Precomputed lookup tables for Pi Zero performance
SIN_TABLE = [math.sin(i * math.pi / 128) for i in range(256)]
DIST_TABLE = [[math.sqrt((x - COLS//2)**2 + (y - ROWS//2)**2) for x in range(COLS)] for y in range(ROWS)]
ANGLE_TABLE = [[int((math.atan2(y - ROWS//2, x - COLS//2) * 180 / math.pi + 180) % 360) for x in range(COLS)] for y in range(ROWS)]


def fast_sin(x):
    """Fast sin using lookup table, x in arbitrary units"""
    return SIN_TABLE[int(x * 8) & 255]


# Named color mood presets
# hue_lock: fix all hues to this value (monochrome)
# hue_shift: rotate all hues by this many degrees
# sat_mult: multiply saturation (0=grayscale, 0.4=pastel, 1=unchanged)
# sat_override: force saturation to a fixed value regardless of effect
# val_mult: multiply value/brightness
MOOD_PRESETS = {
    'default':     {},
    'mono_red':    {'hue_lock': 0,   'sat_override': 1.0, 'hue_range': 15},
    'mono_orange': {'hue_lock': 30,  'sat_override': 1.0, 'hue_range': 15},
    'mono_yellow': {'hue_lock': 60,  'sat_override': 1.0, 'hue_range': 15},
    'mono_green':  {'hue_lock': 120, 'sat_override': 1.0, 'hue_range': 15},
    'mono_cyan':   {'hue_lock': 180, 'sat_override': 1.0, 'hue_range': 15},
    'mono_blue':   {'hue_lock': 240, 'sat_override': 1.0, 'hue_range': 15},
    'mono_purple': {'hue_lock': 280, 'sat_override': 1.0, 'hue_range': 15},
    'warm':        {'hue_shift': -40},
    'cool':        {'hue_shift': 60},
    'pastel':      {'sat_mult': 0.4},
    'night':       {'sat_mult': 0.7, 'val_mult': 0.5},
    'grayscale':   {'sat_mult': 0.0},
}

_active_mood_name = 'default'
_active_mood = {}


def set_mood(name):
    """Set the active color mood by name. Pass None or 'default' to reset."""
    global _active_mood_name, _active_mood
    if not name or name == 'default':
        _active_mood_name = 'default'
        _active_mood = {}
    else:
        _active_mood_name = name
        _active_mood = MOOD_PRESETS.get(name, {})


def get_mood():
    """Return the active mood name."""
    return _active_mood_name


def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB. h: 0-360, s: 0-1, v: 0-1. Applies active mood if set."""
    if _active_mood:
        if 'hue_lock' in _active_mood:
            h = _active_mood['hue_lock']
        else:
            h = (h + _active_mood.get('hue_shift', 0)) % 360
        if 'sat_override' in _active_mood:
            s = _active_mood['sat_override']
        else:
            s = min(1.0, s * _active_mood.get('sat_mult', 1.0))
        v = min(1.0, v * _active_mood.get('val_mult', 1.0))
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
