"""Tunnel effect - 3D tunnel flying effect."""

import time
import math

from .base import effect
from .utils import hsv_to_rgb


@effect('tunnel', 'Tunnel Effect',
        category='high_power',
        speed=(1.0, "Flight speed"),
        rings=(20, "Number of rings"))
def tunnel(ctx, duration=8, frequency=5, speed=1.0, rings=20, check_interrupt=None, **kwargs):
    """3D tunnel flying effect"""
    rings = max(1, int(rings))
    start_time = time.time()
    offset = 0
    hue_offset = 0

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        ctx.matrix.Clear()
        cx_center, cy_center = ctx.cols // 2, ctx.rows // 2

        # Draw concentric rings
        for ring in range(rings, 0, -1):
            z = (ring + offset) % rings
            if z < 0.1:
                z = 0.1

            # Calculate ring radius based on depth
            radius = (1 / z) * 15

            # Calculate brightness based on depth
            brightness = min(1.0, 1.0 / (z * 0.3))

            # Color varies by depth
            hue = (int(z * 30) + hue_offset) % 360
            r, g, b = hsv_to_rgb(hue, 1.0, brightness)

            # Draw ring as points
            points = max(int(radius * 4), 8)
            for i in range(points):
                angle = (i / points) * 2 * math.pi
                px = int(cx_center + radius * math.cos(angle) * 2)  # Stretch horizontally
                py = int(cy_center + radius * math.sin(angle))

                if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                    ctx.matrix.SetPixel(px, py, r, g, b)

        offset = (offset + 0.15 * speed) % rings
        hue_offset = (hue_offset + 2) % 360
        time.sleep(0.02)
