"""Lightning effect - Random lightning bolts."""

import time
from random import randrange, choice

from .base import effect
from .utils import hsv_to_rgb


@effect('lightning', 'Lightning',
        category=['low_power', 'night'],
        branches=(True, "Enable branching"),
        fade=(1.0, "Fade speed multiplier"),
        color=(240, "Hue 0-360 (240=blue, 0=red, -1=random)"))
def lightning(ctx, duration=8, frequency=5, branches=True, fade=1.0, color=240, check_interrupt=None, **kwargs):
    """Random lightning bolts effect"""
    bolts = []
    spawn_rate = max(2, 27 - (frequency * 2.5))

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        # Fade existing pixels
        for y in range(ctx.rows):
            for x in range(ctx.cols):
                ctx.matrix.SetPixel(x, y, 0, 0, 0)

        # Draw active bolts
        new_bolts = []
        for bolt in bolts:
            bolt['life'] -= fade
            if bolt['life'] > 0:
                brightness = bolt['life'] / bolt['max_life']
                r, g, b = hsv_to_rgb(bolt['hue'], 0.3, brightness)
                for px, py in bolt['points']:
                    ctx.matrix.SetPixel(px, py, r, g, b)
                new_bolts.append(bolt)
        bolts = new_bolts

        # Spawn new lightning
        if randrange(int(spawn_rate)) == 0:
            x = randrange(10, ctx.cols - 10)
            points = []
            y = 0
            while y < ctx.rows:
                points.append((x, y))
                if randrange(3) == 0:
                    x += choice([-1, 1])
                    x = max(0, min(ctx.cols - 1, x))
                y += 1
                # Branch sometimes
                if branches and randrange(8) == 0 and y < ctx.rows - 5:
                    bx = x
                    for by in range(y, min(y + randrange(3, 8), ctx.rows)):
                        bx += choice([-1, 0, 1])
                        bx = max(0, min(ctx.cols - 1, bx))
                        points.append((bx, by))

            max_life = randrange(5, 12)
            bolt_hue = randrange(360) if color < 0 else color
            bolts.append({'points': points, 'life': max_life, 'max_life': max_life, 'hue': bolt_hue})

        time.sleep(0.04)
