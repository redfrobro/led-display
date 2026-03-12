"""Warp effect - Star Trek style warp speed effect."""

import time
import math
from random import randrange, random

from .base import effect
from .utils import hsv_to_rgb


@effect('warp', 'Warp Speed',
        category='high_power',
        star_count=(200, "Number of stars"),
        speed=(1.0, "Warp speed multiplier"))
def warp(ctx, duration=8, frequency=5, star_count=200, speed=1.0, check_interrupt=None, **kwargs):
    """Star Trek style warp speed effect"""
    stars = []
    cx, cy = ctx.cols // 2, ctx.rows // 2

    for _ in range(star_count):
        angle = random() * 2 * math.pi
        dist = random() * 1.9 + 0.05  # spread across full lifecycle to avoid reset waves
        stars.append({
            'angle': angle,
            'dist': dist,
            'speed': random() * 0.5 + 0.5,
            'hue': randrange(180, 240)  # Blue-white spectrum
        })

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        ctx.matrix.Clear()

        for star in stars:
            # Calculate position from center
            old_dist = star['dist']
            star['dist'] += star['speed'] * 0.02 * speed

            # Reset if too far
            if star['dist'] > 2:
                star['dist'] = random() * 0.1 + 0.05
                star['angle'] = random() * 2 * math.pi
                star['hue'] = randrange(180, 240)
                continue

            # Draw streak (from old to new position)
            for t in [0, 0.3, 0.6, 1.0]:
                d = old_dist + (star['dist'] - old_dist) * t
                px = int(cx + math.cos(star['angle']) * d * ctx.cols)
                py = int(cy + math.sin(star['angle']) * d * ctx.rows * 0.5)

                if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                    brightness = min(1.0, star['dist'] * 2)
                    saturation = max(0, 1 - star['dist'])
                    r, g, b = hsv_to_rgb(star['hue'], saturation, brightness)
                    ctx.matrix.SetPixel(px, py, r, g, b)

        time.sleep(0.02)
