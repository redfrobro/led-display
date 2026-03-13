"""Fire effect - Realistic rising flame."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb


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

        # Render: black -> red -> orange -> yellow -> white
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                h = heat[ctx.rows - 1 - y][x]
                if h < 64:
                    r, g, b = hsv_to_rgb(0, 1.0, h / 64)
                elif h < 128:
                    r, g, b = hsv_to_rgb((h - 64) / 64 * 60, 1.0, 1.0)
                else:
                    r, g, b = hsv_to_rgb(60, max(0.0, 1.0 - (h - 128) / 128), 1.0)
                ctx.matrix.SetPixel(x, y, r, g, b)

        time.sleep(0.05)
