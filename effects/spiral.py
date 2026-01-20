"""Spiral effect - Spiral pattern from center."""

import time

from .base import effect
from .utils import hsv_to_rgb, DIST_TABLE, ANGLE_TABLE


@effect('spiral', 'Spiral',
        category='low_power',
        speed=(5, "Rotation speed"),
        density=(10, "Color band density"))
def spiral(ctx, duration=8, frequency=5, speed=5, density=10, check_interrupt=None, **kwargs):
    """Spiral pattern from center - optimized for Pi Zero"""
    start_time = time.time()
    hue_offset = 0

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                hue = (ANGLE_TABLE[y][x] + int(DIST_TABLE[y][x] * density) + hue_offset) % 360
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                ctx.matrix.SetPixel(x, y, r, g, b)

        hue_offset += speed
        time.sleep(0.02)
