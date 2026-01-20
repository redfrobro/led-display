"""Meteor effect - Diagonal meteors with glowing trails."""

import time
from random import randrange, choice

from .base import effect
from .utils import hsv_to_rgb


@effect('meteor', 'Meteor Shower',
        category='low_power',
        length=(12, "Meteor trail length"),
        speed=(1.0, "Speed multiplier"))
def meteor(ctx, duration=8, frequency=5, length=12, speed=1.0, check_interrupt=None, **kwargs):
    """Diagonal meteors with glowing trails"""
    length = max(1, int(length))
    meteors = []
    spawn_rate = max(2, 18 - (frequency * 1.6))
    min_len = max(4, length - 4)
    max_len = length + 4

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        ctx.matrix.Clear()

        # Spawn new meteors
        if randrange(int(spawn_rate)) == 0:
            meteors.append({
                'x': randrange(ctx.cols + 20),
                'y': randrange(-10, 0),
                'speed': randrange(2, 4),
                'length': randrange(min_len, max_len),
                'hue': choice([0, 30, 200, 280])
            })

        # Update and draw meteors
        new_meteors = []
        for m in meteors:
            for i in range(m['length']):
                px = int(m['x'] - i * 0.5)
                py = int(m['y'] - i)
                if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                    brightness = 1.0 - (i / m['length'])
                    r, g, b = hsv_to_rgb(m['hue'], 0.7, brightness)
                    ctx.matrix.SetPixel(px, py, r, g, b)

            m['x'] -= m['speed'] * 0.5 * speed
            m['y'] += m['speed'] * speed

            if m['y'] - m['length'] < ctx.rows + 10 and m['x'] + m['length'] > -10:
                new_meteors.append(m)

        meteors = new_meteors
        time.sleep(0.04)
