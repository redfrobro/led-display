"""Balls effect - Multiple bouncing balls with trails."""

import time
from random import randrange, choice

from .base import effect


@effect('balls', 'Bouncing Balls',
        category=['low_power', 'night'],
        count=(5, "Number of balls"),
        size=(1, "Ball radius"),
        trail=(10, "Trail length"))
def balls(ctx, duration=8, frequency=5, count=5, size=1, trail=10, check_interrupt=None, **kwargs):
    """Multiple bouncing balls with trails"""
    count = max(1, int(count))
    size = max(0, int(size))
    ball_list = []
    colors = [(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 50), (255, 50, 255), (50, 255, 255)]

    for i in range(count):
        ball_list.append({
            'x': randrange(5, ctx.cols-5),
            'y': randrange(5, ctx.rows-5),
            'vx': choice([-2, -1, 1, 2]),
            'vy': choice([-2, -1, 1, 2]),
            'color': colors[i % len(colors)],
            'trail': []
        })

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return
        ctx.matrix.Clear()

        for ball in ball_list:
            # Draw trail
            for i, pos in enumerate(ball['trail']):
                fade = (i + 1) / len(ball['trail']) if ball['trail'] else 1
                r = int(ball['color'][0] * fade * 0.5)
                g = int(ball['color'][1] * fade * 0.5)
                b = int(ball['color'][2] * fade * 0.5)
                ctx.matrix.SetPixel(int(pos[0]), int(pos[1]), r, g, b)

            # Draw ball
            for dx in range(-size, size + 1):
                for dy in range(-size, size + 1):
                    px, py = int(ball['x']) + dx, int(ball['y']) + dy
                    if 0 <= px < ctx.cols and 0 <= py < ctx.rows:
                        ctx.matrix.SetPixel(px, py, *ball['color'])

            # Update trail
            ball['trail'].append((ball['x'], ball['y']))
            if len(ball['trail']) > trail:
                ball['trail'].pop(0)

            # Move ball
            ball['x'] += ball['vx']
            ball['y'] += ball['vy']

            # Bounce
            if ball['x'] <= 1 or ball['x'] >= ctx.cols - 2:
                ball['vx'] *= -1
                ball['x'] = max(1, min(ctx.cols - 2, ball['x']))
            if ball['y'] <= 1 or ball['y'] >= ctx.rows - 2:
                ball['vy'] *= -1
                ball['y'] = max(1, min(ctx.rows - 2, ball['y']))

        time.sleep(0.05)
