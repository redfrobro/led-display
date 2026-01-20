"""Plasma effect - Smooth psychedelic plasma waves."""

import time

from .base import effect
from .utils import hsv_to_rgb, fast_sin, DIST_TABLE


@effect('plasma', 'Plasma Effect',
        category='low_power',
        speed=(1.0, "Animation speed multiplier"))
def plasma(ctx, duration=8, frequency=5, speed=1.0, check_interrupt=None, **kwargs):
    """Smooth psychedelic plasma waves - optimized for Pi Zero"""
    start_time = time.time()
    t = 0
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                value = fast_sin(x + t * 8) + fast_sin(y + t * 4)
                value += fast_sin(x + y + t * 6) + fast_sin(DIST_TABLE[y][x] + t * 8)
                hue = int(value * 45 + t * 50) % 360
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                ctx.matrix.SetPixel(x, y, r, g, b)
        t += 0.15 * speed
        time.sleep(0.02)
