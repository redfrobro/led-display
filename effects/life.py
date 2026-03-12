"""Life effect - Conway's Game of Life with colorful cells."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb


@effect('life', 'Game of Life',
        category='high_power',
        density=(30, "Initial cell density %"),
        colorful=(True, "Colorful cells"))
def life(ctx, duration=8, frequency=5, density=30, colorful=True, check_interrupt=None, **kwargs):
    """Conway's Game of Life with colorful cells"""
    # Initialize random grid
    grid = [[randrange(100) < density for x in range(ctx.cols)] for y in range(ctx.rows)]
    colors = [[ctx.random_hue() if grid[y][x] else 0 for x in range(ctx.cols)] for y in range(ctx.rows)]
    generation = 0

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        # Draw current state
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                if grid[y][x]:
                    if colorful:
                        r, g, b = hsv_to_rgb(colors[y][x], 1.0, 1.0)
                    else:
                        r, g, b = 0, 255, 0
                    ctx.matrix.SetPixel(x, y, r, g, b)
                else:
                    ctx.matrix.SetPixel(x, y, 0, 0, 0)

        # Compute next generation
        new_grid = [[False] * ctx.cols for _ in range(ctx.rows)]
        new_colors = [[0] * ctx.cols for _ in range(ctx.rows)]

        for y in range(ctx.rows):
            for x in range(ctx.cols):
                # Count neighbors
                neighbors = 0
                neighbor_hues = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = (y + dy) % ctx.rows, (x + dx) % ctx.cols
                        if grid[ny][nx]:
                            neighbors += 1
                            neighbor_hues.append(colors[ny][nx])

                # Apply rules
                if grid[y][x]:
                    if neighbors in [2, 3]:
                        new_grid[y][x] = True
                        new_colors[y][x] = colors[y][x]
                else:
                    if neighbors == 3:
                        new_grid[y][x] = True
                        if neighbor_hues:
                            new_colors[y][x] = (sum(neighbor_hues) // len(neighbor_hues) + 5) % 360

        grid = new_grid
        colors = new_colors
        generation += 1

        # Reinitialize if grid becomes empty or static
        alive = sum(sum(row) for row in grid)
        if alive < 10 or (generation > 50 and alive < 30):
            grid = [[randrange(100) < density for x in range(ctx.cols)] for y in range(ctx.rows)]
            colors = [[ctx.random_hue() if grid[y][x] else 0 for x in range(ctx.cols)] for y in range(ctx.rows)]
            generation = 0

        time.sleep(0.1)
