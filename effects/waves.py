"""Waves effect - Realistic ocean waves with foam."""

import time
import math

from .base import effect


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

                # More vivid ocean colors with better contrast
                if wave_height < 0.3:
                    blue = int(80 + 50 * wave_height)
                    green = int(20 * wave_height)
                elif wave_height < 0.6:
                    blue = int(130 + 100 * (wave_height - 0.3))
                    green = int(20 + 150 * (wave_height - 0.3))
                else:
                    blue = 230
                    green = int(170 + 85 * (wave_height - 0.6))

                # Brighter foam on peaks
                white = int(max(0, (wave_height - 0.65) * 600))

                # Update foam
                if wave_height > 0.7 and y < ctx.rows - 1:
                    foam[y][x] = min(255, foam[y][x] + 40)

                # Decay foam
                foam[y][x] = max(0, foam[y][x] - 8)

                r = min(255, white + foam[y][x])
                g = min(255, green + int(foam[y][x] * 0.8))
                b = min(255, blue + int(foam[y][x] * 0.3))

                ctx.matrix.SetPixel(x, y, r, g, b)

        t += 0.1
        time.sleep(0.025)
