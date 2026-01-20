"""Rain effect - Rain with splashing droplets and ripples."""

import time
import math
from random import randrange, random

from .base import effect


@effect('rain', 'Rain Storm',
        category='high_power',
        intensity=(50, "Rain intensity"),
        splash_size=(3, "Splash ripple size"))
def rain(ctx, duration=8, frequency=5, intensity=50, splash_size=3, check_interrupt=None, **kwargs):
    """Rain with splashing droplets and ripples"""
    drops = []
    splashes = []
    max_drops = int(20 + frequency * 8)

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        ctx.matrix.Clear()

        # Spawn new drops
        while len(drops) < max_drops:
            drops.append({
                'x': randrange(ctx.cols),
                'y': randrange(-20, 0),
                'speed': random() * 2 + 2,
                'length': randrange(2, 5)
            })

        # Update and draw drops
        new_drops = []
        for drop in drops:
            # Draw drop trail
            for i in range(drop['length']):
                dy = int(drop['y'] - i)
                if 0 <= dy < ctx.rows:
                    intensity_val = int(150 * (1 - i / drop['length']))
                    ctx.matrix.SetPixel(int(drop['x']), dy, intensity_val // 2, intensity_val // 2, intensity_val)

            drop['y'] += drop['speed']

            # Create splash when hitting bottom
            if drop['y'] >= ctx.rows:
                splashes.append({
                    'x': drop['x'],
                    'y': ctx.rows - 1,
                    'radius': 0,
                    'max_radius': splash_size + randrange(2),
                    'life': 1.0
                })
            else:
                new_drops.append(drop)

        drops = new_drops

        # Update and draw splashes (ripple effect)
        new_splashes = []
        for splash in splashes:
            splash['radius'] += 0.5
            splash['life'] -= 0.1

            if splash['life'] > 0:
                # Draw expanding ring
                for angle in range(0, 360, 15):
                    rad = math.radians(angle)
                    px = int(splash['x'] + splash['radius'] * math.cos(rad))
                    py = int(splash['y'] + splash['radius'] * 0.3 * math.sin(rad))
                    if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                        intensity_val = int(200 * splash['life'])
                        ctx.matrix.SetPixel(px, py, intensity_val // 2, intensity_val // 2, intensity_val)
                new_splashes.append(splash)

        splashes = new_splashes
        time.sleep(0.03)
