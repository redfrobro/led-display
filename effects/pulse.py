"""Pulse effect - Pulsing rings emanating from multiple points."""

import time
import math
from random import randrange

from .base import effect
from .utils import hsv_to_rgb


@effect('pulse', 'Pulse Rings',
        category='high_power',
        sources=(3, "Number of pulse sources"),
        speed=(1.0, "Pulse expansion speed"))
def pulse(ctx, duration=8, frequency=5, sources=3, speed=1.0, check_interrupt=None, **kwargs):
    """Pulsing rings emanating from multiple points"""
    sources = max(1, int(sources))
    pulses = []
    # Generate source points
    source_points = [(randrange(10, ctx.cols-10), randrange(5, ctx.rows-5), ctx.random_hue())
                     for _ in range(sources)]

    start_time = time.time()
    frame = 0

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        ctx.matrix.Clear()

        # Create new pulses periodically
        spawn_rate = max(5, 20 - frequency * 2)
        if frame % spawn_rate == 0:
            src = source_points[frame // spawn_rate % len(source_points)]
            pulses.append({
                'x': src[0],
                'y': src[1],
                'radius': 0,
                'hue': src[2],
                'life': 1.0
            })
            # Slowly shift source colors
            source_points[frame // spawn_rate % len(source_points)] = (src[0], src[1], (src[2] + 10) % 360)

        # Update and draw pulses
        new_pulses = []
        for pulse_obj in pulses:
            pulse_obj['radius'] += 0.8 * speed
            pulse_obj['life'] -= 0.02

            if pulse_obj['life'] > 0:
                # Draw ring
                r, g, b = hsv_to_rgb(pulse_obj['hue'], 1.0, pulse_obj['life'])
                points = max(int(pulse_obj['radius'] * 6), 12)
                for i in range(points):
                    angle = (i / points) * 2 * math.pi
                    px = int(pulse_obj['x'] + pulse_obj['radius'] * math.cos(angle))
                    py = int(pulse_obj['y'] + pulse_obj['radius'] * math.sin(angle))
                    if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                        ctx.matrix.SetPixel(px, py, r, g, b)
                new_pulses.append(pulse_obj)

        pulses = new_pulses
        frame += 1
        time.sleep(0.03)
