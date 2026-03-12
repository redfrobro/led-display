"""Fireworks effect - Exploding fireworks."""

import time
import math
from random import randrange, random

from .base import effect
from .utils import hsv_to_rgb


@effect('fireworks', 'Fireworks',
        category=['low_power', 'night'],
        particles=(30, "Particles per explosion"),
        gravity=(0.1, "Gravity strength"))
def fireworks(ctx, duration=8, frequency=5, particles=30, gravity=0.1, check_interrupt=None, **kwargs):
    """Exploding fireworks effect"""
    active_particles = []
    spawn_rate = max(3, 33 - (frequency * 3))

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        ctx.matrix.Clear()

        # Launch new firework
        if randrange(int(spawn_rate)) == 0:
            x = randrange(10, ctx.cols - 10)
            hue = ctx.random_hue()
            for _ in range(particles):
                angle = random() * 2 * math.pi
                spd = random() * 3 + 1
                active_particles.append({
                    'x': x,
                    'y': ctx.rows // 2,
                    'vx': math.cos(angle) * spd,
                    'vy': math.sin(angle) * spd,
                    'life': randrange(20, 40),
                    'hue': hue + randrange(-20, 20)
                })

        # Update particles
        new_particles = []
        for p in active_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += gravity
            p['life'] -= 1

            if p['life'] > 0 and 0 <= p['x'] < ctx.cols and 0 <= p['y'] < ctx.rows:
                brightness = p['life'] / 40
                r, g, b = hsv_to_rgb(p['hue'], 1.0, brightness)
                ctx.matrix.SetPixel(int(p['x']), int(p['y']), r, g, b)
                new_particles.append(p)

        active_particles = new_particles
        time.sleep(0.04)
