"""Comet effect - Orbiting comet with colorful trail."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb, fast_sin


@effect('comet', 'Comet',
        category='low_power',
        trail=(25, "Trail length"),
        speed=(0.15, "Orbit speed"))
def comet(ctx, duration=8, frequency=5, trail=25, speed=0.15, check_interrupt=None, **kwargs):
    """Orbiting comet with colorful trail"""
    trail_points = []
    angle = 0
    hue = ctx.random_hue()

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        ctx.matrix.Clear()

        # Calculate comet position (elliptical orbit)
        cx = ctx.cols // 2 + int(fast_sin(angle) * (ctx.cols // 3))
        cy = ctx.rows // 2 + int(fast_sin(angle + 8) * (ctx.rows // 3))

        # Add to trail
        trail_points.append((cx, cy, hue))
        if len(trail_points) > trail:
            trail_points.pop(0)

        # Draw trail
        for i, (tx, ty, th) in enumerate(trail_points):
            brightness = (i + 1) / len(trail_points)
            r, g, b = hsv_to_rgb(th, 1.0, brightness * 0.8)
            if 0 <= tx < ctx.cols and 0 <= ty < ctx.rows:
                ctx.matrix.SetPixel(tx, ty, r, g, b)

        # Draw comet head (brighter, larger)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                px, py = cx + dx, cy + dy
                if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                    r, g, b = hsv_to_rgb(hue, 0.5, 1.0)
                    ctx.matrix.SetPixel(px, py, r, g, b)

        angle += speed
        hue = (hue + 2) % 360
        time.sleep(0.03)
