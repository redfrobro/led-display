"""Ripple effect - Water ripple effect with multiple drop points."""

import time
from random import randrange, random

from .base import effect


@effect('ripple', 'Ripple Pond',
        category=['high_power', 'night'],
        auto_drops=(True, "Automatic water drops"),
        drop_rate=(30, "Drop frequency"))
def ripple(ctx, duration=8, frequency=5, auto_drops=True, drop_rate=30, check_interrupt=None, **kwargs):
    """Water ripple effect with multiple drop points"""
    water = [[0.0] * ctx.cols for _ in range(ctx.rows)]
    velocity = [[0.0] * ctx.cols for _ in range(ctx.rows)]
    damping = 0.96

    start_time = time.time()
    frame = 0

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        # Add random drops
        rate = max(10, 50 - frequency * 4)
        if auto_drops and frame % rate == 0:
            x, y = randrange(2, ctx.cols-2), randrange(2, ctx.rows-2)
            water[y][x] = random() * 200 + 55

        # Simulate wave propagation
        new_water = [[0.0] * ctx.cols for _ in range(ctx.rows)]
        for y in range(1, ctx.rows - 1):
            for x in range(1, ctx.cols - 1):
                avg = (water[y-1][x] + water[y+1][x] +
                       water[y][x-1] + water[y][x+1]) / 4
                velocity[y][x] += (avg - water[y][x]) * 0.5
                velocity[y][x] *= damping
                new_water[y][x] = water[y][x] + velocity[y][x]

        water = new_water

        # Render
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                height = water[y][x]
                if height > 0:
                    blue = min(255, int(100 + height))
                    green = min(255, int(50 + height * 0.5))
                    white = min(255, max(0, int(height - 100)))
                    ctx.matrix.SetPixel(x, y, white, green + white // 2, blue)
                else:
                    ctx.matrix.SetPixel(x, y, 0, 20, 40)

        frame += 1
        time.sleep(0.03)
