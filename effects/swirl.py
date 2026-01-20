"""Swirl effect - Multiple rotating swirl vortices."""

import time
import math
from random import random, choice

from .base import effect
from .utils import hsv_to_rgb


@effect('swirl', 'Swirl Vortex',
        category='high_power',
        vortices=(2, "Number of vortices"),
        speed=(1.0, "Rotation speed"))
def swirl(ctx, duration=8, frequency=5, vortices=2, speed=1.0, check_interrupt=None, **kwargs):
    """Multiple rotating swirl vortices"""
    vortices = max(1, int(vortices))
    vortices = min(vortices, 10)
    start_time = time.time()
    t = 0

    # Vortex centers and parameters
    vortex_params = []
    for i in range(vortices):
        vortex_params.append({
            'cx': ctx.cols // (vortices + 1) * (i + 1),
            'cy': ctx.rows // 2,
            'rotation': random() * 2 * math.pi,
            'direction': choice([-1, 1]),
            'hue': i * (360 // vortices)
        })

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        for y in range(ctx.rows):
            for x in range(ctx.cols):
                total_r, total_g, total_b = 0, 0, 0

                for vortex in vortex_params:
                    # Distance and angle from vortex center
                    dx = x - vortex['cx']
                    dy = y - vortex['cy']
                    dist = math.sqrt(dx * dx + dy * dy) + 0.1
                    angle = math.atan2(dy, dx)

                    # Spiral effect
                    spiral_angle = angle + dist * 0.3 + vortex['rotation']
                    spiral_val = (math.sin(spiral_angle * 3) + 1) / 2

                    # Intensity falls off with distance
                    intensity = max(0, 1 - dist / 20) * spiral_val

                    if intensity > 0.05:
                        hue = (vortex['hue'] + int(dist * 10)) % 360
                        r, g, b = hsv_to_rgb(hue, 1.0, intensity)
                        total_r += r
                        total_g += g
                        total_b += b

                ctx.matrix.SetPixel(x, y, min(255, int(total_r)), min(255, int(total_g)), min(255, int(total_b)))

        # Update vortex rotations
        for vortex in vortex_params:
            vortex['rotation'] += 0.1 * speed * vortex['direction']
            vortex['hue'] = (vortex['hue'] + 1) % 360

        t += 0.1
        time.sleep(0.025)
