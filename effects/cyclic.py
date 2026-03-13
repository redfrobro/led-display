"""Cyclic Cellular Automaton effect - produces spiral and wave patterns."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb


@effect('cyclic', 'Cyclic CA',
        category='high_power',
        states=(16, "Number of color states (4-32)"),
        threshold=(3, "Neighbor count needed to advance state (1-4)"))
def cyclic(ctx, duration=8, states=16, threshold=3, check_interrupt=None, **kwargs):
    """Cyclic CA: cells cycle through N color states. A cell advances if it has
    enough neighbors already in the next state, producing spirals and waves."""

    states = max(4, min(32, states))
    threshold = max(1, min(4, threshold))

    grid = [[randrange(states) for _ in range(ctx.cols)] for _ in range(ctx.rows)]

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        # Draw current state
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                hue = (grid[y][x] * 360) // states
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                ctx.matrix.SetPixel(x, y, r, g, b)

        # Compute next generation
        new_grid = [[0] * ctx.cols for _ in range(ctx.rows)]
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                state = grid[y][x]
                next_state = (state + 1) % states
                count = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dy == 0 and dx == 0:
                            continue
                        if grid[(y + dy) % ctx.rows][(x + dx) % ctx.cols] == next_state:
                            count += 1
                new_grid[y][x] = next_state if count >= threshold else state

        grid = new_grid
        time.sleep(0.05)