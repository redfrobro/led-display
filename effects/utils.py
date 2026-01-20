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


def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB. h: 0-360, s: 0-1, v: 0-1"""
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
