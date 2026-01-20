"""Aurora effect - Northern lights / Aurora Borealis effect."""

import time
import math
from random import random, randrange

from .base import effect
from .utils import hsv_to_rgb


@effect('aurora', 'Aurora Borealis',
        category=['high_power', 'night'],
        bands=(5, "Number of aurora bands"),
        speed=(1.0, "Movement speed"))
def aurora(ctx, duration=8, frequency=5, bands=5, speed=1.0, check_interrupt=None, **kwargs):
    """Northern lights / Aurora Borealis effect"""
    start_time = time.time()
    t = 0

    # Aurora band parameters
    band_params = [(random() * 10, random() * 0.5 + 0.2, randrange(80, 160))
                   for _ in range(bands)]

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        for y in range(ctx.rows):
            for x in range(ctx.cols):
                total_r, total_g, total_b = 0, 0, 0

                for phase, freq, hue in band_params:
                    # Wavy band calculation
                    wave = math.sin(x * freq * 0.1 + t * speed + phase)
                    wave += math.sin(x * freq * 0.05 + t * speed * 0.5 + phase * 2) * 0.5

                    # Band center position
                    band_y = (ctx.rows // 2) + wave * 8

                    # Distance from band
                    dist = abs(y - band_y)

                    # Intensity falls off with distance
                    if dist < 8:
                        intensity = (1 - dist / 8) ** 2
                        # Add shimmer
                        shimmer = 0.7 + 0.3 * math.sin(x * 0.3 + y * 0.2 + t * 3 + phase)
                        intensity *= shimmer

                        r, g, b = hsv_to_rgb(hue, 0.7, intensity * 0.8)
                        total_r += r
                        total_g += g
                        total_b += b

                ctx.matrix.SetPixel(x, y, min(255, int(total_r)), min(255, int(total_g)), min(255, int(total_b)))

        t += 0.08
        time.sleep(0.025)
