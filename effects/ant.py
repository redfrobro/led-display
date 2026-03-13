"""Langton's Ant effect - emergent patterns from simple turning rules."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb

# Direction vectors: 0=up, 1=right, 2=down, 3=left
_DX = (0, 1, 0, -1)
_DY = (-1, 0, 1, 0)


@effect('ant', "Langton's Ant",
        category='low_power',
        num_ants=(4, "Number of ants (1-8)"))
def ant(ctx, duration=8, num_ants=4, check_interrupt=None, **kwargs):
    """Langton's Ant: ants turn right on empty cells, left on filled cells,
    flipping the cell and moving forward. Multiple ants produce complex trails."""

    num_ants = max(1, min(8, num_ants))

    grid = [[0] * ctx.cols for _ in range(ctx.rows)]
    hues = [[0] * ctx.cols for _ in range(ctx.rows)]

    ants = [
        {
            'x': randrange(ctx.cols),
            'y': randrange(ctx.rows),
            'dir': randrange(4),
            'hue': (i * 360 // num_ants) % 360,
        }
        for i in range(num_ants)
    ]

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        # Step each ant
        for a in ants:
            x, y = a['x'], a['y']
            if grid[y][x] == 0:
                a['dir'] = (a['dir'] + 1) % 4  # turn right
                grid[y][x] = 1
                hues[y][x] = a['hue']
            else:
                a['dir'] = (a['dir'] - 1) % 4  # turn left
                grid[y][x] = 0
            a['x'] = (x + _DX[a['dir']]) % ctx.cols
            a['y'] = (y + _DY[a['dir']]) % ctx.rows
            a['hue'] = (a['hue'] + 1) % 360

        # Draw trail
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                if grid[y][x]:
                    r, g, b = hsv_to_rgb(hues[y][x], 1.0, 0.8)
                else:
                    r, g, b = 0, 0, 0
                ctx.matrix.SetPixel(x, y, r, g, b)

        # Draw ants as bright white dots on top
        for a in ants:
            ctx.matrix.SetPixel(a['x'], a['y'], 255, 255, 255)

        time.sleep(0.01)