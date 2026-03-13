"""Waves effect - Realistic ocean waves with foam."""

import time
import math

from .base import effect
from .utils import hsv_to_rgb


@effect('waves', 'Ocean Waves',
        category='high_power',
        wave_count=(3, "Number of wave layers"),
        speed=(1.0, "Wave speed multiplier"))
def waves(ctx, duration=8, frequency=5, wave_count=3, speed=1.0, check_interrupt=None, **kwargs):
    """Realistic ocean waves with foam effect"""
    wave_count = max(1, int(wave_count))
    start_time = time.time()
    t = 0
    foam = [[0] * ctx.cols for _ in range(ctx.rows)]

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        for y in range(ctx.rows):
            for x in range(ctx.cols):
                # Multiple wave layers
                wave = 0
                for i in range(wave_count):
                    freq = (i + 1) * 0.3
                    amp = 1.0 / (i + 1)
                    phase = i * 2.1
                    wave += amp * math.sin(x * freq * 0.15 + t * speed + phase)
                    wave += amp * 0.5 * math.sin(y * freq * 0.1 + t * speed * 0.7 + phase)

                # Normalize wave height
                wave_height = (wave + wave_count) / (wave_count * 2)

                # Update foam
                if wave_height > 0.7 and y < ctx.rows - 1:
                    foam[y][x] = min(255, foam[y][x] + 40)
                foam[y][x] = max(0, foam[y][x] - 8)

                # Ocean colors: deep blue -> cyan -> white foam at peaks
                hue = 220 - wave_height * 40
                foam_f = foam[y][x] / 255.0
                s = max(0.0, 1.0 - max(0.0, wave_height - 0.65) * 2.5 - foam_f * 0.5)
                v = min(1.0, 0.3 + wave_height * 0.7 + foam_f * 0.2)
                r, g, b = hsv_to_rgb(hue, s, v)
                ctx.matrix.SetPixel(x, y, r, g, b)

        t += 0.1
        time.sleep(0.025)
