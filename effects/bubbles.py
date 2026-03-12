"""Bubbles effect - Colorful bubbles rising up."""

import time
from random import randrange, random

from .base import effect
from .utils import hsv_to_rgb, fast_sin


@effect('bubbles', 'Rising Bubbles',
        category='low_power',
        size=(2, "Max bubble size"),
        wobble=(2, "Wobble amount"))
def bubbles(ctx, duration=8, frequency=5, size=2, wobble=2, check_interrupt=None, **kwargs):
    """Colorful bubbles rising up"""
    size = max(0, int(size))
    bubble_list = []
    spawn_rate = max(1, 11 - frequency)
    max_size = max(1, size)

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        ctx.matrix.Clear()

        # Spawn new bubbles
        if randrange(spawn_rate) == 0:
            bubble_list.append({
                'x': randrange(ctx.cols),
                'y': ctx.rows + randrange(3),
                'speed': random() * 0.5 + 0.5,
                'wobble_offset': random() * 2,
                'size': randrange(1, max_size + 1),
                'hue': ctx.random_hue()
            })

        # Update and draw bubbles
        new_bubbles = []
        for bub in bubble_list:
            bx = int(bub['x'] + fast_sin(bub['y'] * 0.5 + bub['wobble_offset']) * wobble)
            by = int(bub['y'])

            # Draw bubble
            for dy in range(-bub['size'], bub['size'] + 1):
                for dx in range(-bub['size'], bub['size'] + 1):
                    if dx*dx + dy*dy <= bub['size']*bub['size']:
                        px, py = bx + dx, by + dy
                        if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                            edge = 1.0 if dx*dx + dy*dy < bub['size']*bub['size']*0.5 else 0.6
                            r, g, b = hsv_to_rgb(bub['hue'], 0.5, edge)
                            ctx.matrix.SetPixel(px, py, r, g, b)

            bub['y'] -= bub['speed']
            bub['hue'] = (bub['hue'] + 1) % 360

            if bub['y'] + bub['size'] > -1:
                new_bubbles.append(bub)

        bubble_list = new_bubbles
        time.sleep(0.04)
