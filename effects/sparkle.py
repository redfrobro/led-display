"""Sparkle effect - Twinkling stars."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb


@effect('sparkle', 'Sparkle Twinkle',
        category=['low_power', 'night'],
        saturation=(0.3, "Color saturation 0-1"))
def sparkle(ctx, duration=8, frequency=5, saturation=0.3, check_interrupt=None, **kwargs):
    """Twinkling stars effect"""
    stars = {}
    stars_per_frame = max(1, frequency)
    start_time = time.time()

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        # Add new stars
        for _ in range(stars_per_frame):
            x, y = randrange(ctx.cols), randrange(ctx.rows)
            hue = randrange(360)
            stars[(x, y)] = {'brightness': 0, 'direction': 1, 'hue': hue, 'max': randrange(150, 255), 'sat': saturation}

        # Update and render stars
        to_remove = []
        for pos, star in stars.items():
            star['brightness'] += star['direction'] * randrange(10, 30)

            if star['brightness'] >= star['max']:
                star['direction'] = -1
            elif star['brightness'] <= 0:
                to_remove.append(pos)
                continue

            brightness = max(0, min(255, star['brightness']))
            r, g, b = hsv_to_rgb(star['hue'], star.get('sat', 0.3), brightness / 255)
            ctx.matrix.SetPixel(pos[0], pos[1], r, g, b)

        for pos in to_remove:
            ctx.matrix.SetPixel(pos[0], pos[1], 0, 0, 0)
            del stars[pos]

        time.sleep(0.03)
