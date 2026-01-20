"""Starfield effect - 3D starfield flying through space."""

import time
from random import random

from .base import effect


@effect('starfield', 'Starfield',
        category=['low_power', 'night'],
        count=(100, "Number of stars"),
        speed=(0.02, "Travel speed"))
def starfield(ctx, duration=8, frequency=5, count=100, speed=0.02, check_interrupt=None, **kwargs):
    """3D starfield flying through space"""
    count = max(1, int(count))
    stars = []
    for _ in range(count):
        stars.append({
            'x': random() * 2 - 1,
            'y': random() * 2 - 1,
            'z': random()
        })

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        ctx.matrix.Clear()

        for star in stars:
            star['z'] -= speed

            if star['z'] <= 0:
                star['x'] = random() * 2 - 1
                star['y'] = random() * 2 - 1
                star['z'] = 1

            # Project to 2D
            px = int((star['x'] / star['z']) * ctx.cols/2 + ctx.cols/2)
            py = int((star['y'] / star['z']) * ctx.rows/2 + ctx.rows/2)

            if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                brightness = int((1 - star['z']) * 255)
                sz = 1 if star['z'] > 0.5 else 2

                for dx in range(sz):
                    for dy in range(sz):
                        if 0 <= px+dx < ctx.cols and 0 <= py+dy < ctx.rows:
                            ctx.matrix.SetPixel(px+dx, py+dy, brightness, brightness, brightness)

        time.sleep(0.03)
