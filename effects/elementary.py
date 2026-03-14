"""Elementary Cellular Automaton effect - 1D rule scrolls down the display."""

import time
from random import randrange

from .base import effect
from .utils import hsv_to_rgb


@effect('elementary', 'Elementary CA',
        category='low_power',
        rule=(110, "Wolfram rule number (0-255). 30=chaotic, 90=sierpinski, 110=complex"))
def elementary(ctx, duration=8, rule=110, check_interrupt=None, **kwargs):
    """Elementary CA: each row is computed from the row above using a 1D rule.
    The pattern scrolls down, revealing the automaton's evolution over time."""

    rule = max(0, min(255, rule))
    rule_table = [(rule >> i) & 1 for i in range(8)]

    def new_seed():
        row = [0] * ctx.cols
        row[ctx.cols // 2] = 1  # single center seed
        return row

    rows = []
    current = new_seed()
    hue_offset = 0

    start_time = time.time()
    while time.time() - start_time < duration:
        if ctx.check_interrupt():
            return

        # Compute next row from current
        next_row = [0] * ctx.cols
        for x in range(ctx.cols):
            pattern = (current[(x - 1) % ctx.cols] << 2) | (current[x] << 1) | current[(x + 1) % ctx.cols]
            next_row[x] = rule_table[pattern]

        rows.append(next_row)
        if len(rows) > ctx.rows:
            rows.pop(0)
        current = next_row

        # Reinitialize if row goes dark (e.g. rule 0 or absorbing rules)
        if not any(current):
            rows.clear()
            ctx.matrix.Clear()
            current = new_seed()

        hue_offset = (hue_offset + 3) % 360

        # Draw all buffered rows
        for y, row in enumerate(rows):
            hue = (y * 360 // ctx.rows + hue_offset) % 360
            for x, state in enumerate(row):
                if state:
                    r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                else:
                    r, g, b = 0, 0, 0
                ctx.matrix.SetPixel(x, y, r, g, b)

        time.sleep(0.05)