"""Spectrum effect - Audio visualizer style spectrum bars (simulated)."""

import time
from random import random

from .base import effect
from .utils import hsv_to_rgb


@effect('spectrum', 'Spectrum Analyzer',
        category='high_power',
        bars=(16, "Number of frequency bars"),
        reactive=(True, "Quick reactive mode"))
def spectrum(ctx, duration=8, frequency=5, bars=16, reactive=True, check_interrupt=None, **kwargs):
    """Audio visualizer style spectrum bars (simulated)"""
    bars = max(1, int(bars))
    bars = min(bars, ctx.cols)
    bar_width = ctx.cols // bars
    heights = [0] * bars
    targets = [0] * bars
    peaks = [0] * bars
    peak_hold = [0] * bars

    start_time = time.time()
    frame = 0

    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        ctx.matrix.Clear()

        # Generate simulated audio data
        if frame % 3 == 0:
            for i in range(bars):
                base = ctx.rows * (1 - i / bars) * 0.5
                variation = random() * ctx.rows * 0.7
                targets[i] = int(base + variation)

        # Smooth movement toward targets
        for i in range(bars):
            diff = targets[i] - heights[i]
            if reactive:
                heights[i] += diff * 0.3
            else:
                heights[i] += diff * 0.1

            # Update peaks
            if heights[i] > peaks[i]:
                peaks[i] = heights[i]
                peak_hold[i] = 10
            elif peak_hold[i] > 0:
                peak_hold[i] -= 1
            else:
                peaks[i] = max(0, peaks[i] - 0.5)

        # Draw bars
        for i in range(bars):
            x_start = i * bar_width
            height = int(heights[i])

            for x in range(x_start, min(x_start + bar_width, ctx.cols)):
                for y in range(ctx.rows - 1, ctx.rows - 1 - height, -1):
                    if y >= 0:
                        ratio = (ctx.rows - 1 - y) / ctx.rows
                        if ratio < 0.5:
                            hue = 120  # Green
                        elif ratio < 0.75:
                            hue = 60  # Yellow
                        else:
                            hue = 0  # Red
                        r, g, b = hsv_to_rgb(hue, 1.0, 0.9)
                        ctx.matrix.SetPixel(x, y, r, g, b)

            # Draw peak indicator
            peak_y = ctx.rows - 1 - int(peaks[i])
            if 0 <= peak_y < ctx.rows:
                for x in range(x_start, min(x_start + bar_width, ctx.cols)):
                    ctx.matrix.SetPixel(x, peak_y, 255, 255, 255)

        frame += 1
        time.sleep(0.03)
