"""Fire effect - Realistic rising flame."""

import time
from random import randrange

from .base import effect


@effect('fire', 'Fire Effect',
        category='low_power',
        intensity=(4, "Spark intensity 1-10"),
        cooling=(3, "Cooling rate 1-5"))
def fire(ctx, duration=8, frequency=5, intensity=4, cooling=3, check_interrupt=None, **kwargs):
    """Realistic rising flame effect"""
    heat = [[0] * ctx.cols for _ in range(ctx.rows)]
    start_time = time.time()

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        # Cool down
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                cooldown = randrange(0, cooling + 1)
                heat[y][x] = max(0, heat[y][x] - cooldown)

        # Heat rises
        for y in range(ctx.rows - 1, 1, -1):
            for x in range(ctx.cols):
                heat[y][x] = (heat[y-1][(x-1) % ctx.cols] +
                             heat[y-1][x] +
                             heat[y-1][(x+1) % ctx.cols] +
                             heat[y-2][x]) // 4

        # Random sparks at bottom
        for x in range(ctx.cols):
            if randrange(10) < intensity:
                heat[0][x] = min(255, heat[0][x] + randrange(160, 255))

        # Render with more vivid fire colors
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                h = heat[ctx.rows - 1 - y][x]
                if h < 64:
                    r, g, b = min(255, h * 4), 0, 0
                elif h < 128:
                    r, g, b = 255, min(255, (h - 64) * 4), 0
                elif h < 192:
                    r, g, b = 255, 255, min(255, (h - 128) * 4)
                else:
                    intensity_val = min(255, (h - 192) * 4)
                    r, g, b = 255, 255, intensity_val
                ctx.matrix.SetPixel(x, y, r, g, b)

        time.sleep(0.05)
