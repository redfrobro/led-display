"""Brian's Brain effect - 3-state cellular automaton."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb

DEAD, ALIVE, DYING = 0, 1, 2


@effect('brains', "Brian's Brain",
        category='high_power',
        density=(20, "Initial alive cell density %"))
def brains(ctx, duration=8, density=20, check_interrupt=None, **kwargs):
    """Brian's Brain 3-state CA: dead -> alive -> dying -> dead.
    A dead cell becomes alive if it has exactly 2 alive neighbors."""

    def make_grid():
        g = [[ALIVE if randrange(100) < density else DEAD for _ in range(ctx.cols)] for _ in range(ctx.rows)]
        h = [[randrange(360) for _ in range(ctx.cols)] for _ in range(ctx.rows)]
        return g, h

    grid, hues = make_grid()

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        # Draw current state
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                state = grid[y][x]
                if state == ALIVE:
                    r, g, b = hsv_to_rgb(hues[y][x], 1.0, 1.0)
                elif state == DYING:
                    r, g, b = hsv_to_rgb(hues[y][x], 0.5, 0.35)
                else:
                    r, g, b = 0, 0, 0
                ctx.matrix.SetPixel(x, y, r, g, b)

        # Compute next generation
        new_grid = [[DEAD] * ctx.cols for _ in range(ctx.rows)]
        new_hues = [[0] * ctx.cols for _ in range(ctx.rows)]
        alive_count = 0

        for y in range(ctx.rows):
            for x in range(ctx.cols):
                state = grid[y][x]
                if state == ALIVE:
                    new_grid[y][x] = DYING
                    new_hues[y][x] = hues[y][x]
                    alive_count += 1
                elif state == DYING:
                    new_grid[y][x] = DEAD
                else:
                    alive_neighbors = 0
                    neighbor_hues = []
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            if grid[(y + dy) % ctx.rows][(x + dx) % ctx.cols] == ALIVE:
                                alive_neighbors += 1
                                neighbor_hues.append(hues[(y + dy) % ctx.rows][(x + dx) % ctx.cols])
                    if alive_neighbors == 2:
                        new_grid[y][x] = ALIVE
                        avg_hue = sum(neighbor_hues) // len(neighbor_hues) if neighbor_hues else randrange(360)
                        new_hues[y][x] = (avg_hue + 10) % 360

        grid, hues = new_grid, new_hues

        if alive_count == 0:
            grid, hues = make_grid()

        time.sleep(0.05)