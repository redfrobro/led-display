"""Matrix rain effect - The Matrix digital rain."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb


@effect('matrix', 'Matrix Rain',
        category=['low_power', 'night'],
        speed=(1.0, "Drop speed multiplier"),
        length=(10, "Average trail length"))
def matrix_rain(ctx, duration=8, frequency=5, speed=1.0, length=10, check_interrupt=None, **kwargs):
    """The Matrix digital rain effect"""
    length = max(1, int(length))
    drops = []
    init_rate = max(1, 7 - frequency)
    spawn_rate = max(1, 11 - frequency)
    min_len = max(3, length - 5)
    max_len = length + 5

    for x in range(ctx.cols):
        if randrange(init_rate) == 0:
            drops.append({'x': x, 'y': randrange(-ctx.rows, 0), 'speed': randrange(1, 4), 'length': randrange(min_len, max_len)})

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        ctx.matrix.Clear()

        for drop in drops:
            for i in range(drop['length']):
                y = int(drop['y'] - i)
                if 0 <= y < ctx.rows:
                    if i == 0:
                        r, g, b = hsv_to_rgb(120, 1.0, 1.0)
                        ctx.matrix.SetPixel(drop['x'], y, min(255, r + 200), min(255, g + 200), min(255, b + 200))
                    else:
                        r, g, b = hsv_to_rgb(120, 1.0, 1 - i / drop['length'])
                        ctx.matrix.SetPixel(drop['x'], y, r, g, b)

            drop['y'] += drop['speed'] * speed
            if drop['y'] - drop['length'] > ctx.rows:
                drop['y'] = randrange(-20, -5)
                drop['x'] = randrange(ctx.cols)
                drop['speed'] = randrange(1, 4)

        if randrange(spawn_rate) == 0 and len(drops) < ctx.cols:
            drops.append({'x': randrange(ctx.cols), 'y': randrange(-10, 0), 'speed': randrange(1, 4), 'length': randrange(min_len, max_len)})

        time.sleep(0.05)
