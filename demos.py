import time
import math
import sys
import os
import argparse
import logging
import socket
import threading
import json
from random import randrange, random, choice, shuffle

# Setup logging (disabled by default)
logger = logging.getLogger('led-demos')
logger.addHandler(logging.NullHandler())

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from rgbmatrix import RGBMatrix, RGBMatrixOptions

ROWS = 32
COLS = 64

options = RGBMatrixOptions()
options.hardware_mapping = 'adafruit-hat'
options.rows = ROWS
options.cols = COLS
options.parallel = 1

# Matrix will be initialized later (after fork in daemon mode, or now in normal mode)
matrix = None

def init_matrix(for_daemon=False):
    """Initialize or reinitialize the matrix"""
    global matrix

    if for_daemon:
        # Create fresh options for daemon mode (can't copy from existing options
        # because rgbmatrix returns bytes which can't be re-assigned)
        daemon_options = RGBMatrixOptions()
        daemon_options.hardware_mapping = 'adafruit-hat'
        daemon_options.rows = ROWS
        daemon_options.cols = COLS
        daemon_options.parallel = 1
        daemon_options.drop_privileges = False
        daemon_options.disable_hardware_pulsing = True
        matrix = RGBMatrix(options=daemon_options)
    else:
        # Use standard options
        matrix = RGBMatrix(options=options)

# Precomputed lookup tables for Pi Zero performance
SIN_TABLE = [math.sin(i * math.pi / 128) for i in range(256)]
DIST_TABLE = [[math.sqrt((x - COLS//2)**2 + (y - ROWS//2)**2) for x in range(COLS)] for y in range(ROWS)]
ANGLE_TABLE = [[int((math.atan2(y - ROWS//2, x - COLS//2) * 180 / math.pi + 180) % 360) for x in range(COLS)] for y in range(ROWS)]

def fast_sin(x):
    """Fast sin using lookup table, x in arbitrary units"""
    return SIN_TABLE[int(x * 8) & 255]


def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB. h: 0-360, s: 0-1, v: 0-1"""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


def plasma_effect(duration=8, frequency=5, speed=1.0, check_interrupt=None, **kwargs):
    """Smooth psychedelic plasma waves - optimized for Pi Zero"""
    start_time = time.time()
    t = 0
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        for y in range(ROWS):
            for x in range(COLS):
                value = fast_sin(x + t * 8) + fast_sin(y + t * 4)
                value += fast_sin(x + y + t * 6) + fast_sin(DIST_TABLE[y][x] + t * 8)
                hue = int(value * 45 + t * 50) % 360
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                matrix.SetPixel(x, y, r, g, b)
        t += 0.15 * speed
        time.sleep(0.02)


def fire_effect(duration=8, frequency=5, intensity=4, cooling=3, check_interrupt=None, **kwargs):
    """Realistic rising flame effect"""
    heat = [[0] * COLS for _ in range(ROWS)]
    start_time = time.time()

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        # Cool down
        for y in range(ROWS):
            for x in range(COLS):
                cooldown = randrange(0, cooling + 1)
                heat[y][x] = max(0, heat[y][x] - cooldown)

        # Heat rises
        for y in range(ROWS - 1, 1, -1):
            for x in range(COLS):
                heat[y][x] = (heat[y-1][(x-1) % COLS] +
                             heat[y-1][x] +
                             heat[y-1][(x+1) % COLS] +
                             heat[y-2][x]) // 4

        # Random sparks at bottom
        for x in range(COLS):
            if randrange(10) < intensity:
                heat[0][x] = min(255, heat[0][x] + randrange(160, 255))

        # Render
        for y in range(ROWS):
            for x in range(COLS):
                h = heat[ROWS - 1 - y][x]
                if h < 85:
                    r, g, b = min(255, h * 3), 0, 0
                elif h < 170:
                    r, g, b = 255, min(255, (h - 85) * 3), 0
                else:
                    r, g, b = 255, 255, min(255, (h - 170) * 3)
                matrix.SetPixel(x, y, r, g, b)

        time.sleep(0.05)


def matrix_rain(duration=8, frequency=5, speed=1.0, length=10, check_interrupt=None, **kwargs):
    """The Matrix digital rain effect"""
    drops = []
    # frequency 1=sparse(6), 5=default(3), 10=dense(1)
    init_rate = max(1, 7 - frequency)
    # frequency 1=rare(10), 5=default(5), 10=frequent(1)
    spawn_rate = max(1, 11 - frequency)
    min_len = max(3, length - 5)
    max_len = length + 5

    for x in range(COLS):
        if randrange(init_rate) == 0:
            drops.append({'x': x, 'y': randrange(-ROWS, 0), 'speed': randrange(1, 4), 'length': randrange(min_len, max_len)})

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        matrix.Clear()

        for drop in drops:
            for i in range(drop['length']):
                y = int(drop['y'] - i)
                if 0 <= y < ROWS:
                    if i == 0:
                        matrix.SetPixel(drop['x'], y, 200, 255, 200)
                    else:
                        intensity = int(255 * (1 - i / drop['length']))
                        matrix.SetPixel(drop['x'], y, 0, intensity, 0)

            drop['y'] += drop['speed'] * speed
            if drop['y'] - drop['length'] > ROWS:
                drop['y'] = randrange(-20, -5)
                drop['x'] = randrange(COLS)
                drop['speed'] = randrange(1, 4)

        if randrange(spawn_rate) == 0 and len(drops) < COLS:
            drops.append({'x': randrange(COLS), 'y': randrange(-10, 0), 'speed': randrange(1, 4), 'length': randrange(min_len, max_len)})

        time.sleep(0.05)


def sparkle_twinkle(duration=8, frequency=5, saturation=0.3, check_interrupt=None, **kwargs):
    """Twinkling stars effect"""
    stars = {}
    # frequency 1=few(2), 5=default(5), 10=many(10)
    stars_per_frame = max(1, frequency)
    start_time = time.time()

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        # Add new stars
        for _ in range(stars_per_frame):
            x, y = randrange(COLS), randrange(ROWS)
            hue = randrange(360)
            stars[(x, y)] = {'brightness': 0, 'direction': 1, 'hue': hue, 'max': randrange(150, 255), 'sat': saturation}

        # Update and render stars
        to_remove = []
        for pos, star in stars.items():
            star['brightness'] += star['direction'] * randrange(10, 30)

            if star['brightness'] >= star['max']:
                star['direction'] = -1
            elif star['brightness'] <= 0:
                to_remove.append(pos)
                continue

            brightness = max(0, min(255, star['brightness']))
            r, g, b = hsv_to_rgb(star['hue'], star.get('sat', 0.3), brightness / 255)
            matrix.SetPixel(pos[0], pos[1], r, g, b)

        for pos in to_remove:
            matrix.SetPixel(pos[0], pos[1], 0, 0, 0)
            del stars[pos]

        time.sleep(0.03)


def meteor_shower(duration=8, frequency=5, length=12, speed=1.0, check_interrupt=None, **kwargs):
    """Diagonal meteors with glowing trails"""
    meteors = []
    # frequency 1=rare(16), 5=default(8), 10=frequent(2)
    spawn_rate = max(2, 18 - (frequency * 1.6))
    min_len = max(4, length - 4)
    max_len = length + 4

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        matrix.Clear()

        # Spawn new meteors
        if randrange(int(spawn_rate)) == 0:
            meteors.append({
                'x': randrange(COLS + 20),
                'y': randrange(-10, 0),
                'speed': randrange(2, 4),
                'length': randrange(min_len, max_len),
                'hue': choice([0, 30, 200, 280])  # Red, orange, blue, purple
            })

        # Update and draw meteors
        new_meteors = []
        for m in meteors:
            for i in range(m['length']):
                px = int(m['x'] - i * 0.5)
                py = int(m['y'] - i)
                if 0 <= px < COLS and 0 <= py < ROWS:
                    brightness = 1.0 - (i / m['length'])
                    r, g, b = hsv_to_rgb(m['hue'], 0.7, brightness)
                    matrix.SetPixel(px, py, r, g, b)

            m['x'] -= m['speed'] * 0.5 * speed
            m['y'] += m['speed'] * speed

            if m['y'] - m['length'] < ROWS + 10 and m['x'] + m['length'] > -10:
                new_meteors.append(m)

        meteors = new_meteors
        time.sleep(0.04)


def spiral_effect(duration=8, frequency=5, speed=5, density=10, check_interrupt=None, **kwargs):
    """Spiral pattern from center - optimized for Pi Zero"""
    start_time = time.time()
    hue_offset = 0

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        for y in range(ROWS):
            for x in range(COLS):
                hue = (ANGLE_TABLE[y][x] + int(DIST_TABLE[y][x] * density) + hue_offset) % 360
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                matrix.SetPixel(x, y, r, g, b)

        hue_offset += speed
        time.sleep(0.02)


def bouncing_balls(duration=8, frequency=5, count=5, size=1, trail=10, check_interrupt=None, **kwargs):
    """Multiple bouncing balls with trails"""
    balls = []
    colors = [(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 50), (255, 50, 255), (50, 255, 255)]

    for i in range(count):
        balls.append({
            'x': randrange(5, COLS-5),
            'y': randrange(5, ROWS-5),
            'vx': choice([-2, -1, 1, 2]),
            'vy': choice([-2, -1, 1, 2]),
            'color': colors[i % len(colors)],
            'trail': []
        })

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        matrix.Clear()

        for ball in balls:
            # Draw trail
            for i, pos in enumerate(ball['trail']):
                fade = (i + 1) / len(ball['trail']) if ball['trail'] else 1
                r = int(ball['color'][0] * fade * 0.5)
                g = int(ball['color'][1] * fade * 0.5)
                b = int(ball['color'][2] * fade * 0.5)
                matrix.SetPixel(int(pos[0]), int(pos[1]), r, g, b)

            # Draw ball
            for dx in range(-size, size + 1):
                for dy in range(-size, size + 1):
                    px, py = int(ball['x']) + dx, int(ball['y']) + dy
                    if 0 <= px < COLS and 0 <= py < ROWS:
                        matrix.SetPixel(px, py, *ball['color'])

            # Update trail
            ball['trail'].append((ball['x'], ball['y']))
            if len(ball['trail']) > trail:
                ball['trail'].pop(0)

            # Move ball
            ball['x'] += ball['vx']
            ball['y'] += ball['vy']

            # Bounce
            if ball['x'] <= 1 or ball['x'] >= COLS - 2:
                ball['vx'] *= -1
                ball['x'] = max(1, min(COLS - 2, ball['x']))
            if ball['y'] <= 1 or ball['y'] >= ROWS - 2:
                ball['vy'] *= -1
                ball['y'] = max(1, min(ROWS - 2, ball['y']))

        time.sleep(0.05)


def lightning(duration=8, frequency=5, branches=True, fade=1.0, color=240, check_interrupt=None, **kwargs):
    """Random lightning bolts effect"""
    bolts = []
    # frequency 1=rare(25), 5=default(12), 10=frequent(2)
    spawn_rate = max(2, 27 - (frequency * 2.5))

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        # Fade existing pixels
        for y in range(ROWS):
            for x in range(COLS):
                matrix.SetPixel(x, y, 0, 0, 0)

        # Draw active bolts
        new_bolts = []
        for bolt in bolts:
            bolt['life'] -= fade
            if bolt['life'] > 0:
                brightness = bolt['life'] / bolt['max_life']
                r, g, b = hsv_to_rgb(bolt['hue'], 0.3, brightness)
                for px, py in bolt['points']:
                    matrix.SetPixel(px, py, r, g, b)
                new_bolts.append(bolt)
        bolts = new_bolts

        # Spawn new lightning
        if randrange(int(spawn_rate)) == 0:
            x = randrange(10, COLS - 10)
            points = []
            y = 0
            while y < ROWS:
                points.append((x, y))
                if randrange(3) == 0:
                    x += choice([-1, 1])
                    x = max(0, min(COLS - 1, x))
                y += 1
                # Branch sometimes
                if branches and randrange(8) == 0 and y < ROWS - 5:
                    bx = x
                    for by in range(y, min(y + randrange(3, 8), ROWS)):
                        bx += choice([-1, 0, 1])
                        bx = max(0, min(COLS - 1, bx))
                        points.append((bx, by))

            max_life = randrange(5, 12)
            # color is hue: 240=blue, 0=red, 60=yellow, 120=green, 300=purple, -1=random
            bolt_hue = randrange(360) if color < 0 else color
            bolts.append({'points': points, 'life': max_life, 'max_life': max_life, 'hue': bolt_hue})

        time.sleep(0.04)


def fireworks(duration=8, frequency=5, particles=30, gravity=0.1, check_interrupt=None, **kwargs):
    """Exploding fireworks effect"""
    active_particles = []
    # frequency 1=rare(30), 5=default(15), 10=frequent(3)
    spawn_rate = max(3, 33 - (frequency * 3))

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        matrix.Clear()

        # Launch new firework
        if randrange(int(spawn_rate)) == 0:
            x = randrange(10, COLS - 10)
            hue = randrange(360)
            for _ in range(particles):
                angle = random() * 2 * math.pi
                speed = random() * 3 + 1
                active_particles.append({
                    'x': x,
                    'y': ROWS // 2,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
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

            if p['life'] > 0 and 0 <= p['x'] < COLS and 0 <= p['y'] < ROWS:
                brightness = p['life'] / 40
                r, g, b = hsv_to_rgb(p['hue'], 1.0, brightness)
                matrix.SetPixel(int(p['x']), int(p['y']), r, g, b)
                new_particles.append(p)

        active_particles = new_particles
        time.sleep(0.04)


def starfield(duration=8, frequency=5, count=100, speed=0.02, check_interrupt=None, **kwargs):
    """3D starfield flying through space"""
    stars = []
    for _ in range(count):
        stars.append({
            'x': random() * 2 - 1,
            'y': random() * 2 - 1,
            'z': random()
        })

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        matrix.Clear()

        for star in stars:
            star['z'] -= speed

            if star['z'] <= 0:
                star['x'] = random() * 2 - 1
                star['y'] = random() * 2 - 1
                star['z'] = 1

            # Project to 2D
            px = int((star['x'] / star['z']) * COLS/2 + COLS/2)
            py = int((star['y'] / star['z']) * ROWS/2 + ROWS/2)

            if 0 <= px < COLS and 0 <= py < ROWS:
                brightness = int((1 - star['z']) * 255)
                size = 1 if star['z'] > 0.5 else 2

                for dx in range(size):
                    for dy in range(size):
                        if 0 <= px+dx < COLS and 0 <= py+dy < ROWS:
                            matrix.SetPixel(px+dx, py+dy, brightness, brightness, brightness)

        time.sleep(0.03)


def rising_bubbles(duration=8, frequency=5, size=2, wobble=2, check_interrupt=None, **kwargs):
    """Colorful bubbles rising up"""
    bubbles = []
    # frequency 1=rare(10), 5=default(4), 10=frequent(1)
    spawn_rate = max(1, 11 - frequency)
    max_size = max(1, size)

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        matrix.Clear()

        # Spawn new bubbles
        if randrange(spawn_rate) == 0:
            bubbles.append({
                'x': randrange(COLS),
                'y': ROWS + randrange(3),
                'speed': random() * 0.5 + 0.5,
                'wobble_offset': random() * 2,
                'size': randrange(1, max_size + 1),
                'hue': randrange(360)
            })

        # Update and draw bubbles
        new_bubbles = []
        for b in bubbles:
            bx = int(b['x'] + fast_sin(b['y'] * 0.5 + b['wobble_offset']) * wobble)
            by = int(b['y'])

            # Draw bubble
            for dy in range(-b['size'], b['size'] + 1):
                for dx in range(-b['size'], b['size'] + 1):
                    if dx*dx + dy*dy <= b['size']*b['size']:
                        px, py = bx + dx, by + dy
                        if 0 <= px < COLS and 0 <= py < ROWS:
                            edge = 1.0 if dx*dx + dy*dy < b['size']*b['size']*0.5 else 0.6
                            r, g, b_col = hsv_to_rgb(b['hue'], 0.5, edge)
                            matrix.SetPixel(px, py, r, g, b_col)

            b['y'] -= b['speed']
            b['hue'] = (b['hue'] + 1) % 360

            if b['y'] + b['size'] > -1:
                new_bubbles.append(b)

        bubbles = new_bubbles
        time.sleep(0.04)


def comet(duration=8, frequency=5, trail=25, speed=0.15, check_interrupt=None, **kwargs):
    """Orbiting comet with colorful trail"""
    trail_points = []
    angle = 0
    hue = randrange(360)

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return
        matrix.Clear()

        # Calculate comet position (elliptical orbit)
        cx = COLS // 2 + int(fast_sin(angle) * (COLS // 3))
        cy = ROWS // 2 + int(fast_sin(angle + 8) * (ROWS // 3))

        # Add to trail
        trail_points.append((cx, cy, hue))
        if len(trail_points) > trail:
            trail_points.pop(0)

        # Draw trail
        for i, (tx, ty, th) in enumerate(trail_points):
            brightness = (i + 1) / len(trail_points)
            r, g, b = hsv_to_rgb(th, 1.0, brightness * 0.8)
            if 0 <= tx < COLS and 0 <= ty < ROWS:
                matrix.SetPixel(tx, ty, r, g, b)

        # Draw comet head (brighter, larger)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                px, py = cx + dx, cy + dy
                if 0 <= px < COLS and 0 <= py < ROWS:
                    r, g, b = hsv_to_rgb(hue, 0.5, 1.0)
                    matrix.SetPixel(px, py, r, g, b)

        angle += speed
        hue = (hue + 2) % 360
        time.sleep(0.03)


# ============================================================================
# HIGH POWER EFFECTS - Optimized for Pi 3/4 with more CPU headroom
# ============================================================================

def ocean_waves(duration=8, frequency=5, wave_count=3, speed=1.0, check_interrupt=None, **kwargs):
    """Realistic ocean waves with foam effect"""
    start_time = time.time()
    t = 0
    foam = [[0] * COLS for _ in range(ROWS)]

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        for y in range(ROWS):
            for x in range(COLS):
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

                # Color based on depth
                depth = (y / ROWS)
                blue = int(100 + 155 * wave_height * (1 - depth * 0.3))
                green = int(50 + 100 * wave_height * (1 - depth * 0.5))
                white = int(max(0, (wave_height - 0.7) * 800))  # Foam on peaks

                # Update foam
                if wave_height > 0.75 and y < ROWS - 1:
                    foam[y][x] = min(255, foam[y][x] + 30)

                # Decay foam
                foam[y][x] = max(0, foam[y][x] - 5)

                r = min(255, white + foam[y][x])
                g = min(255, green + foam[y][x])
                b = min(255, blue)

                matrix.SetPixel(x, y, r, g, b)

        t += 0.1
        time.sleep(0.025)


def rain_storm(duration=8, frequency=5, intensity=50, splash_size=3, check_interrupt=None, **kwargs):
    """Rain with splashing droplets and ripples"""
    drops = []
    splashes = []
    # frequency 1=light(20), 5=default(50), 10=heavy(100)
    max_drops = int(20 + frequency * 8)

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        matrix.Clear()

        # Spawn new drops
        while len(drops) < max_drops:
            drops.append({
                'x': randrange(COLS),
                'y': randrange(-20, 0),
                'speed': random() * 2 + 2,
                'length': randrange(2, 5)
            })

        # Update and draw drops
        new_drops = []
        for drop in drops:
            # Draw drop trail
            for i in range(drop['length']):
                dy = int(drop['y'] - i)
                if 0 <= dy < ROWS:
                    intensity_val = int(150 * (1 - i / drop['length']))
                    matrix.SetPixel(int(drop['x']), dy, intensity_val // 2, intensity_val // 2, intensity_val)

            drop['y'] += drop['speed']

            # Create splash when hitting bottom
            if drop['y'] >= ROWS:
                splashes.append({
                    'x': drop['x'],
                    'y': ROWS - 1,
                    'radius': 0,
                    'max_radius': splash_size + randrange(2),
                    'life': 1.0
                })
            else:
                new_drops.append(drop)

        drops = new_drops

        # Update and draw splashes (ripple effect)
        new_splashes = []
        for splash in splashes:
            splash['radius'] += 0.5
            splash['life'] -= 0.1

            if splash['life'] > 0:
                # Draw expanding ring
                for angle in range(0, 360, 15):
                    rad = math.radians(angle)
                    px = int(splash['x'] + splash['radius'] * math.cos(rad))
                    py = int(splash['y'] + splash['radius'] * 0.3 * math.sin(rad))
                    if 0 <= px < COLS and 0 <= py < ROWS:
                        intensity_val = int(200 * splash['life'])
                        matrix.SetPixel(px, py, intensity_val // 2, intensity_val // 2, intensity_val)
                new_splashes.append(splash)

        splashes = new_splashes
        time.sleep(0.03)


def game_of_life(duration=8, frequency=5, density=30, colorful=True, check_interrupt=None, **kwargs):
    """Conway's Game of Life with colorful cells"""
    # Initialize random grid
    grid = [[randrange(100) < density for x in range(COLS)] for y in range(ROWS)]
    colors = [[randrange(360) if grid[y][x] else 0 for x in range(COLS)] for y in range(ROWS)]
    generation = 0

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        # Draw current state
        for y in range(ROWS):
            for x in range(COLS):
                if grid[y][x]:
                    if colorful:
                        r, g, b = hsv_to_rgb(colors[y][x], 1.0, 1.0)
                    else:
                        r, g, b = 0, 255, 0
                    matrix.SetPixel(x, y, r, g, b)
                else:
                    matrix.SetPixel(x, y, 0, 0, 0)

        # Compute next generation
        new_grid = [[False] * COLS for _ in range(ROWS)]
        new_colors = [[0] * COLS for _ in range(ROWS)]

        for y in range(ROWS):
            for x in range(COLS):
                # Count neighbors
                neighbors = 0
                neighbor_hues = []
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = (y + dy) % ROWS, (x + dx) % COLS
                        if grid[ny][nx]:
                            neighbors += 1
                            neighbor_hues.append(colors[ny][nx])

                # Apply rules
                if grid[y][x]:
                    # Cell is alive
                    if neighbors in [2, 3]:
                        new_grid[y][x] = True
                        new_colors[y][x] = colors[y][x]
                else:
                    # Cell is dead
                    if neighbors == 3:
                        new_grid[y][x] = True
                        # Inherit average color from parents
                        if neighbor_hues:
                            new_colors[y][x] = (sum(neighbor_hues) // len(neighbor_hues) + 5) % 360

        grid = new_grid
        colors = new_colors
        generation += 1

        # Reinitialize if grid becomes empty or static
        alive = sum(sum(row) for row in grid)
        if alive < 10 or (generation > 50 and alive < 30):
            grid = [[randrange(100) < density for x in range(COLS)] for y in range(ROWS)]
            colors = [[randrange(360) if grid[y][x] else 0 for x in range(COLS)] for y in range(ROWS)]
            generation = 0

        time.sleep(0.1)


def tunnel_effect(duration=8, frequency=5, speed=1.0, rings=20, check_interrupt=None, **kwargs):
    """3D tunnel flying effect"""
    start_time = time.time()
    offset = 0
    hue_offset = 0

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        matrix.Clear()
        cx, cy = COLS // 2, ROWS // 2

        # Draw concentric rings
        for ring in range(rings, 0, -1):
            z = (ring + offset) % rings
            if z < 0.1:
                z = 0.1

            # Calculate ring radius based on depth
            radius = (1 / z) * 15

            # Calculate brightness based on depth
            brightness = min(1.0, 1.0 / (z * 0.3))

            # Color varies by depth
            hue = (int(z * 30) + hue_offset) % 360
            r, g, b = hsv_to_rgb(hue, 1.0, brightness)

            # Draw ring as points
            points = max(int(radius * 4), 8)
            for i in range(points):
                angle = (i / points) * 2 * math.pi
                px = int(cx + radius * math.cos(angle) * 2)  # Stretch horizontally
                py = int(cy + radius * math.sin(angle))

                if 0 <= px < COLS and 0 <= py < ROWS:
                    matrix.SetPixel(px, py, r, g, b)

        offset = (offset + 0.15 * speed) % rings
        hue_offset = (hue_offset + 2) % 360
        time.sleep(0.02)


def pulse_rings(duration=8, frequency=5, sources=3, speed=1.0, check_interrupt=None, **kwargs):
    """Pulsing rings emanating from multiple points"""
    pulses = []
    # Generate source points
    source_points = [(randrange(10, COLS-10), randrange(5, ROWS-5), randrange(360))
                     for _ in range(sources)]

    start_time = time.time()
    frame = 0

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        matrix.Clear()

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
        for pulse in pulses:
            pulse['radius'] += 0.8 * speed
            pulse['life'] -= 0.02

            if pulse['life'] > 0:
                # Draw ring
                r, g, b = hsv_to_rgb(pulse['hue'], 1.0, pulse['life'])
                points = max(int(pulse['radius'] * 6), 12)
                for i in range(points):
                    angle = (i / points) * 2 * math.pi
                    px = int(pulse['x'] + pulse['radius'] * math.cos(angle))
                    py = int(pulse['y'] + pulse['radius'] * math.sin(angle))
                    if 0 <= px < COLS and 0 <= py < ROWS:
                        matrix.SetPixel(px, py, r, g, b)
                new_pulses.append(pulse)

        pulses = new_pulses
        frame += 1
        time.sleep(0.03)


def warp_speed(duration=8, frequency=5, star_count=200, speed=1.0, check_interrupt=None, **kwargs):
    """Star Trek style warp speed effect"""
    stars = []
    cx, cy = COLS // 2, ROWS // 2

    for _ in range(star_count):
        angle = random() * 2 * math.pi
        dist = random() * 0.5 + 0.1
        stars.append({
            'angle': angle,
            'dist': dist,
            'speed': random() * 0.5 + 0.5,
            'hue': randrange(180, 240)  # Blue-white spectrum
        })

    start_time = time.time()
    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        matrix.Clear()

        for star in stars:
            # Calculate position from center
            old_dist = star['dist']
            star['dist'] += star['speed'] * 0.02 * speed

            # Reset if too far
            if star['dist'] > 2:
                star['dist'] = random() * 0.1 + 0.05
                star['angle'] = random() * 2 * math.pi
                star['hue'] = randrange(180, 240)
                continue

            # Draw streak (from old to new position)
            for t in [0, 0.3, 0.6, 1.0]:
                d = old_dist + (star['dist'] - old_dist) * t
                px = int(cx + math.cos(star['angle']) * d * COLS)
                py = int(cy + math.sin(star['angle']) * d * ROWS * 0.5)

                if 0 <= px < COLS and 0 <= py < ROWS:
                    # Brightness increases with distance
                    brightness = min(1.0, star['dist'] * 2)
                    saturation = max(0, 1 - star['dist'])  # Gets whiter as it streaks
                    r, g, b = hsv_to_rgb(star['hue'], saturation, brightness)
                    matrix.SetPixel(px, py, r, g, b)

        time.sleep(0.02)


def aurora(duration=8, frequency=5, bands=5, speed=1.0, check_interrupt=None, **kwargs):
    """Northern lights / Aurora Borealis effect"""
    start_time = time.time()
    t = 0

    # Aurora band parameters
    band_params = [(random() * 10, random() * 0.5 + 0.2, randrange(80, 160))
                   for _ in range(bands)]  # (phase, frequency, hue)

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        for y in range(ROWS):
            for x in range(COLS):
                total_r, total_g, total_b = 0, 0, 0

                for phase, freq, hue in band_params:
                    # Wavy band calculation
                    wave = math.sin(x * freq * 0.1 + t * speed + phase)
                    wave += math.sin(x * freq * 0.05 + t * speed * 0.5 + phase * 2) * 0.5

                    # Band center position
                    band_y = (ROWS // 2) + wave * 8

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

                matrix.SetPixel(x, y, min(255, int(total_r)), min(255, int(total_g)), min(255, int(total_b)))

        t += 0.08
        time.sleep(0.025)


def spectrum_analyzer(duration=8, frequency=5, bars=16, reactive=True, check_interrupt=None, **kwargs):
    """Audio visualizer style spectrum bars (simulated)"""
    bar_width = COLS // bars
    heights = [0] * bars
    targets = [0] * bars
    peaks = [0] * bars
    peak_hold = [0] * bars

    start_time = time.time()
    frame = 0

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        matrix.Clear()

        # Generate simulated audio data (pseudo-random but smooth)
        if frame % 3 == 0:
            for i in range(bars):
                # Bass frequencies (left) tend to be higher
                base = ROWS * (1 - i / bars) * 0.5
                variation = random() * ROWS * 0.7
                targets[i] = int(base + variation)

        # Smooth movement toward targets
        for i in range(bars):
            diff = targets[i] - heights[i]
            if reactive:
                heights[i] += diff * 0.3  # Quick response
            else:
                heights[i] += diff * 0.1  # Smooth

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

            for x in range(x_start, min(x_start + bar_width - 1, COLS)):
                for y in range(ROWS - 1, ROWS - 1 - height, -1):
                    if y >= 0:
                        # Color gradient: green at bottom, yellow in middle, red at top
                        ratio = (ROWS - 1 - y) / ROWS
                        if ratio < 0.5:
                            hue = 120  # Green
                        elif ratio < 0.75:
                            hue = 60  # Yellow
                        else:
                            hue = 0  # Red
                        r, g, b = hsv_to_rgb(hue, 1.0, 0.9)
                        matrix.SetPixel(x, y, r, g, b)

            # Draw peak indicator
            peak_y = ROWS - 1 - int(peaks[i])
            if 0 <= peak_y < ROWS:
                for x in range(x_start, min(x_start + bar_width - 1, COLS)):
                    matrix.SetPixel(x, peak_y, 255, 255, 255)

        frame += 1
        time.sleep(0.03)


def swirl_vortex(duration=8, frequency=5, vortices=2, speed=1.0, check_interrupt=None, **kwargs):
    """Multiple rotating swirl vortices"""
    start_time = time.time()
    t = 0

    # Vortex centers and parameters
    vortex_params = []
    for i in range(vortices):
        vortex_params.append({
            'cx': COLS // (vortices + 1) * (i + 1),
            'cy': ROWS // 2,
            'rotation': random() * 2 * math.pi,
            'direction': choice([-1, 1]),
            'hue': i * (360 // vortices)
        })

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        for y in range(ROWS):
            for x in range(COLS):
                total_r, total_g, total_b = 0, 0, 0

                for vortex in vortex_params:
                    # Distance and angle from vortex center
                    dx = x - vortex['cx']
                    dy = y - vortex['cy']
                    dist = math.sqrt(dx * dx + dy * dy) + 0.1
                    angle = math.atan2(dy, dx)

                    # Spiral effect
                    spiral_angle = angle + dist * 0.3 + vortex['rotation']
                    spiral_val = (math.sin(spiral_angle * 3) + 1) / 2

                    # Intensity falls off with distance
                    intensity = max(0, 1 - dist / 20) * spiral_val

                    if intensity > 0.05:
                        hue = (vortex['hue'] + int(dist * 10)) % 360
                        r, g, b = hsv_to_rgb(hue, 1.0, intensity)
                        total_r += r
                        total_g += g
                        total_b += b

                matrix.SetPixel(x, y, min(255, int(total_r)), min(255, int(total_g)), min(255, int(total_b)))

        # Update vortex rotations
        for vortex in vortex_params:
            vortex['rotation'] += 0.1 * speed * vortex['direction']
            vortex['hue'] = (vortex['hue'] + 1) % 360

        t += 0.1
        time.sleep(0.025)


def ripple_pond(duration=8, frequency=5, auto_drops=True, drop_rate=30, check_interrupt=None, **kwargs):
    """Water ripple effect with multiple drop points"""
    ripples = []
    water = [[0.0] * COLS for _ in range(ROWS)]
    velocity = [[0.0] * COLS for _ in range(ROWS)]
    damping = 0.96

    start_time = time.time()
    frame = 0

    while time.time() - start_time < duration:
        if check_interrupt and check_interrupt():
            return

        # Add random drops
        rate = max(10, 50 - frequency * 4)
        if auto_drops and frame % rate == 0:
            x, y = randrange(2, COLS-2), randrange(2, ROWS-2)
            water[y][x] = random() * 200 + 55

        # Simulate wave propagation
        new_water = [[0.0] * COLS for _ in range(ROWS)]
        for y in range(1, ROWS - 1):
            for x in range(1, COLS - 1):
                # Average of neighbors minus current velocity
                avg = (water[y-1][x] + water[y+1][x] +
                       water[y][x-1] + water[y][x+1]) / 4
                velocity[y][x] += (avg - water[y][x]) * 0.5
                velocity[y][x] *= damping
                new_water[y][x] = water[y][x] + velocity[y][x]

        water = new_water

        # Render
        for y in range(ROWS):
            for x in range(COLS):
                height = water[y][x]
                if height > 0:
                    # Blue water with white highlights
                    blue = min(255, int(100 + height))
                    green = min(255, int(50 + height * 0.5))
                    white = min(255, max(0, int(height - 100)))
                    matrix.SetPixel(x, y, white, green + white // 2, blue)
                else:
                    # Dark water base
                    matrix.SetPixel(x, y, 0, 20, 40)

        frame += 1
        time.sleep(0.03)


# All demo functions with their customizable options
# Format: "name": (display_name, function, {option: (default, description)})
DEMOS = {
    # Low-power effects (optimized for Pi Zero)
    "plasma": ("Plasma Effect", plasma_effect, {
        "speed": (1.0, "Animation speed multiplier"),
    }),
    "fire": ("Fire Effect", fire_effect, {
        "intensity": (4, "Spark intensity 1-10"),
        "cooling": (3, "Cooling rate 1-5"),
    }),
    "matrix": ("Matrix Rain", matrix_rain, {
        "speed": (1.0, "Drop speed multiplier"),
        "length": (10, "Average trail length"),
    }),
    "sparkle": ("Sparkle Twinkle", sparkle_twinkle, {
        "saturation": (0.3, "Color saturation 0-1"),
    }),
    "meteor": ("Meteor Shower", meteor_shower, {
        "length": (12, "Meteor trail length"),
        "speed": (1.0, "Speed multiplier"),
    }),
    "spiral": ("Spiral", spiral_effect, {
        "speed": (5, "Rotation speed"),
        "density": (10, "Color band density"),
    }),
    "balls": ("Bouncing Balls", bouncing_balls, {
        "count": (5, "Number of balls"),
        "size": (1, "Ball radius"),
        "trail": (10, "Trail length"),
    }),
    "lightning": ("Lightning", lightning, {
        "branches": (True, "Enable branching"),
        "fade": (1.0, "Fade speed multiplier"),
        "color": (240, "Hue 0-360 (240=blue, 0=red, -1=random)"),
    }),
    "fireworks": ("Fireworks", fireworks, {
        "particles": (30, "Particles per explosion"),
        "gravity": (0.1, "Gravity strength"),
    }),
    "starfield": ("Starfield", starfield, {
        "count": (100, "Number of stars"),
        "speed": (0.02, "Travel speed"),
    }),
    "bubbles": ("Rising Bubbles", rising_bubbles, {
        "size": (2, "Max bubble size"),
        "wobble": (2, "Wobble amount"),
    }),
    "comet": ("Comet", comet, {
        "trail": (25, "Trail length"),
        "speed": (0.15, "Orbit speed"),
    }),
    # High-power effects (optimized for Pi 3/4)
    "waves": ("Ocean Waves", ocean_waves, {
        "wave_count": (3, "Number of wave layers"),
        "speed": (1.0, "Wave speed multiplier"),
    }),
    "rain": ("Rain Storm", rain_storm, {
        "intensity": (50, "Rain intensity"),
        "splash_size": (3, "Splash ripple size"),
    }),
    "life": ("Game of Life", game_of_life, {
        "density": (30, "Initial cell density %"),
        "colorful": (True, "Colorful cells"),
    }),
    "tunnel": ("Tunnel Effect", tunnel_effect, {
        "speed": (1.0, "Flight speed"),
        "rings": (20, "Number of rings"),
    }),
    "pulse": ("Pulse Rings", pulse_rings, {
        "sources": (3, "Number of pulse sources"),
        "speed": (1.0, "Pulse expansion speed"),
    }),
    "warp": ("Warp Speed", warp_speed, {
        "star_count": (200, "Number of stars"),
        "speed": (1.0, "Warp speed multiplier"),
    }),
    "aurora": ("Aurora Borealis", aurora, {
        "bands": (5, "Number of aurora bands"),
        "speed": (1.0, "Movement speed"),
    }),
    "spectrum": ("Spectrum Analyzer", spectrum_analyzer, {
        "bars": (16, "Number of frequency bars"),
        "reactive": (True, "Quick reactive mode"),
    }),
    "swirl": ("Swirl Vortex", swirl_vortex, {
        "vortices": (2, "Number of vortices"),
        "speed": (1.0, "Rotation speed"),
    }),
    "ripple": ("Ripple Pond", ripple_pond, {
        "auto_drops": (True, "Automatic water drops"),
        "drop_rate": (30, "Drop frequency"),
    }),
}

# Effect options storage
EFFECT_OPTIONS = {}

# Low power mode - original 12 effects optimized for Pi Zero
LOW_POWER_ORDER = ["plasma", "fire", "matrix", "sparkle", "meteor", "spiral",
                   "balls", "lightning", "fireworks", "starfield", "bubbles", "comet"]

# High power effects - require Pi 3/4
HIGH_POWER_ORDER = ["waves", "rain", "life", "tunnel", "pulse", "warp",
                    "aurora", "spectrum", "swirl", "ripple"]

# Default includes all effects (for Pi 3/4)
DEFAULT_ORDER = LOW_POWER_ORDER + HIGH_POWER_ORDER

NIGHT_MODE = ["matrix", "sparkle", "balls", "lightning", "fireworks", "starfield", "aurora", "ripple"]


def parse_effect_opts(opts_string):
    """Parse effect options string like 'fireworks:particles=50,gravity=0.2;balls:count=8'"""
    if not opts_string:
        return {}

    result = {}
    for effect_opts in opts_string.split(";"):
        if ":" not in effect_opts:
            continue
        effect_name, opts = effect_opts.split(":", 1)
        effect_name = effect_name.strip()
        if effect_name not in DEMOS:
            print(f"Warning: Unknown effect '{effect_name}' in options, skipping")
            continue

        result[effect_name] = {}
        for opt in opts.split(","):
            if "=" not in opt:
                continue
            key, value = opt.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Try to convert to appropriate type
            try:
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                elif "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Keep as string

            result[effect_name][key] = value

    return result


class DaemonController:
    """Controls daemon mode with threading and Unix socket IPC"""

    def __init__(self, socket_path, args, effect_keys, webserver_enabled=False, webserver_port=80):
        self.socket_path = socket_path
        self.args = args
        self.effect_keys = effect_keys
        self.running = True
        self.paused = False
        self.current_effect = None
        self.effect_index = 0
        self.skip_to_next = False
        self.skip_to_prev = False
        self.jump_to_effect = False  # For set command - jump without incrementing
        self.start_time = time.time()

        # Adjustable parameters
        self.frequency = args.frequency
        self.brightness = 100  # 0-100
        self.speed = 1.0  # 0.1-5.0
        self.effect_options = EFFECT_OPTIONS.copy()

        # Playback mode: 'playlist' or 'single'
        self.playback_mode = 'playlist'  # Default to playlist mode

        # Web server options
        self.webserver_enabled = webserver_enabled
        self.webserver_port = webserver_port

        # Threading
        self.effect_thread = None
        self.ipc_thread = None
        self.webserver_thread = None
        self.lock = threading.Lock()

    def should_interrupt(self):
        """Called by effect functions to check for commands"""
        with self.lock:
            if not self.running or self.skip_to_next or self.skip_to_prev or self.jump_to_effect:
                return True

        # Check pause (release lock while sleeping to allow resume command)
        while True:
            with self.lock:
                if not self.paused or not self.running:
                    break
            time.sleep(0.1)

        with self.lock:
            return not self.running

    def apply_brightness(self, r, g, b):
        """Scale RGB values by brightness percentage"""
        factor = self.brightness / 100.0
        return int(r * factor), int(g * factor), int(b * factor)

    def effect_worker(self):
        """Run effects in a loop"""
        logger.info("Effect worker thread started")
        loop_count = 0

        try:
            while self.running and (self.args.loops == 0 or loop_count < self.args.loops):
                # Determine which effects to play based on mode
                with self.lock:
                    mode = self.playback_mode
                    start_idx = self.effect_index
                    if mode == 'single':
                        # Single effect mode - only play the current effect
                        effects_to_play = [(start_idx, self.effect_keys[start_idx])]
                    else:
                        # Playlist mode - play all effects starting from current index
                        # Create a rotated list starting from effect_index
                        num_effects = len(self.effect_keys)
                        effects_to_play = [
                            ((start_idx + i) % num_effects, self.effect_keys[(start_idx + i) % num_effects])
                            for i in range(num_effects)
                        ]

                for idx, key in effects_to_play:
                    with self.lock:
                        if not self.running:
                            break
                        self.effect_index = idx
                        self.current_effect = key
                        self.skip_to_next = False
                        self.skip_to_prev = False
                        self.jump_to_effect = False

                    name, func, _ = DEMOS[key]
                    opts = get_effect_options(key)

                    # Merge with any custom options from daemon
                    opts.update(self.effect_options.get(key, {}))

                    logger.info(f"Starting effect '{key}': {name}")

                    # Run effect with interrupt checking
                    duration = self.args.duration if self.args.duration > 0 else 999999
                    func(
                        duration=duration,
                        frequency=self.frequency,
                        check_interrupt=self.should_interrupt,
                        **opts
                    )

                    # Check if we were interrupted
                    with self.lock:
                        if not self.running:
                            break
                        if self.jump_to_effect:
                            # Jump to specific effect - index already set, just break
                            break  # Break out of for loop to restart at new position
                        if self.skip_to_prev:
                            # Go back one position
                            self.effect_index = (idx - 1) % len(self.effect_keys)
                            self.playback_mode = 'playlist'  # Switch to playlist on manual navigation
                            break  # Break out of for loop to restart with new position
                        if self.skip_to_next:
                            # Advance to next position
                            self.effect_index = (idx + 1) % len(self.effect_keys)
                            self.playback_mode = 'playlist'  # Switch to playlist on manual navigation
                            break  # Break out of for loop to restart with new position

                    matrix.Clear()
                    time.sleep(self.args.pause)

                    # In single mode, loop restarts automatically (outer while loop)
                    # In playlist mode, continue to next effect

                loop_count += 1

                if self.args.shuffle and self.running and (self.args.loops == 0 or loop_count < self.args.loops):
                    shuffle(self.effect_keys)

        except Exception as e:
            logger.error(f"Effect worker error: {e}", exc_info=True)
        finally:
            logger.info("Effect worker thread exiting")
            matrix.Clear()

    def handle_command(self, cmd):
        """Process a command and return JSON response"""
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        with self.lock:
            if command == "status":
                uptime = int(time.time() - self.start_time)
                return {
                    "status": "ok",
                    "effect": self.current_effect,
                    "effect_name": DEMOS[self.current_effect][0] if self.current_effect else None,
                    "index": self.effect_index,
                    "total": len(self.effect_keys),
                    "paused": self.paused,
                    "uptime": uptime,
                    "frequency": self.frequency,
                    "brightness": self.brightness,
                    "speed": self.speed,
                    "playback_mode": self.playback_mode
                }

            elif command == "next":
                self.skip_to_next = True
                return {"status": "ok", "message": "Skipping to next effect"}

            elif command == "prev":
                self.skip_to_prev = True
                return {"status": "ok", "message": "Going to previous effect"}

            elif command == "pause":
                self.paused = True
                return {"status": "ok", "message": "Paused"}

            elif command == "resume":
                self.paused = False
                return {"status": "ok", "message": "Resumed"}

            elif command == "set":
                if not arg or arg not in DEMOS:
                    return {"status": "error", "message": f"Unknown effect: {arg}"}
                # Find the effect in our list
                if arg in self.effect_keys:
                    target_idx = self.effect_keys.index(arg)
                    self.effect_index = target_idx
                    self.playback_mode = 'single'  # Switch to single effect mode
                    self.jump_to_effect = True  # Jump to exact effect without incrementing
                    return {"status": "ok", "message": f"Locked on {arg}"}
                else:
                    return {"status": "error", "message": f"Effect {arg} not in current playlist"}

            elif command == "playlist":
                self.playback_mode = 'playlist'
                return {"status": "ok", "message": "Playlist mode enabled"}

            elif command == "stop":
                self.running = False
                return {"status": "ok", "message": "Stopping daemon"}

            elif command == "list":
                effects = [{"key": k, "name": DEMOS[k][0]} for k in self.effect_keys]
                return {"status": "ok", "effects": effects}

            elif command == "frequency":
                if not arg:
                    return {"status": "error", "message": "Missing frequency value"}
                try:
                    freq = int(arg)
                    if 1 <= freq <= 10:
                        self.frequency = freq
                        return {"status": "ok", "frequency": freq, "message": f"Frequency set to {freq}"}
                    else:
                        return {"status": "error", "message": "Frequency must be 1-10"}
                except ValueError:
                    return {"status": "error", "message": "Invalid frequency value"}

            elif command == "brightness":
                if not arg:
                    return {"status": "error", "message": "Missing brightness value"}
                try:
                    bright = int(arg)
                    if 0 <= bright <= 100:
                        self.brightness = bright
                        return {"status": "ok", "brightness": bright, "message": f"Brightness set to {bright}%"}
                    else:
                        return {"status": "error", "message": "Brightness must be 0-100"}
                except ValueError:
                    return {"status": "error", "message": "Invalid brightness value"}

            elif command == "speed":
                if not arg:
                    return {"status": "error", "message": "Missing speed value"}
                try:
                    spd = float(arg)
                    if 0.1 <= spd <= 5.0:
                        self.speed = spd
                        return {"status": "ok", "speed": spd, "message": f"Speed set to {spd}x"}
                    else:
                        return {"status": "error", "message": "Speed must be 0.1-5.0"}
                except ValueError:
                    return {"status": "error", "message": "Invalid speed value"}

            elif command == "opt":
                if not arg or "=" not in arg:
                    return {"status": "error", "message": "Usage: opt key=value"}
                key, value = arg.split("=", 1)
                if self.current_effect:
                    if self.current_effect not in self.effect_options:
                        self.effect_options[self.current_effect] = {}
                    # Try to parse value
                    try:
                        if value.lower() in ("true", "false"):
                            value = value.lower() == "true"
                        elif "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # Keep as string
                    self.effect_options[self.current_effect][key] = value
                    return {"status": "ok", "message": f"Set {key}={value} for {self.current_effect}"}
                else:
                    return {"status": "error", "message": "No effect currently running"}

            else:
                return {"status": "error", "message": f"Unknown command: {command}"}

    def ipc_worker(self):
        """Listen for commands on Unix socket"""
        logger.info(f"IPC worker starting on {self.socket_path}")

        # Remove existing socket
        try:
            os.unlink(self.socket_path)
        except OSError:
            if os.path.exists(self.socket_path):
                raise

        # Create socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(self.socket_path)
        sock.listen(1)
        sock.settimeout(1.0)  # Check running status periodically

        logger.info(f"Listening on {self.socket_path}")

        try:
            while self.running:
                try:
                    conn, _ = sock.accept()
                    try:
                        data = conn.recv(1024).decode('utf-8').strip()
                        if data:
                            logger.debug(f"Received command: {data}")
                            response = self.handle_command(data)
                            conn.sendall((json.dumps(response) + "\n").encode('utf-8'))
                    finally:
                        conn.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"IPC error: {e}", exc_info=True)
        finally:
            sock.close()
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass
            logger.info("IPC worker exiting")

    def webserver_worker(self):
        """Run Flask web server"""
        logger.info(f"Web server starting on port {self.webserver_port}")

        try:
            import webserver
            # Disable Flask's default logging to avoid duplicate messages
            import logging as flask_logging
            flask_log = flask_logging.getLogger('werkzeug')
            flask_log.setLevel(flask_logging.ERROR)

            # Run Flask web server
            webserver.app.run(
                host='0.0.0.0',
                port=self.webserver_port,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except ImportError:
            logger.error("Flask not installed. Install with: pip install flask")
        except Exception as e:
            logger.error(f"Web server error: {e}", exc_info=True)
        finally:
            logger.info("Web server exiting")

    def start(self, fork=True):
        """Start daemon threads"""
        pid_file = "/tmp/led-matrix.pid"
        log_path = "/tmp/led-matrix.log"

        # Clean up old files that might have wrong permissions
        for f in [pid_file, log_path]:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except OSError:
                pass  # Will fail later if we can't write

        if fork:
            # Fork to background
            pid = os.fork()
            if pid > 0:
                # Parent process - write PID and exit
                with open(pid_file, "w") as f:
                    f.write(str(pid))
                print(f"Daemon started with PID {pid}")
                sys.exit(0)

            # Child process continues
            # Detach from terminal
            os.setsid()

            # Setup logging to file for daemon
            log_file = open(log_path, 'a')
            os.dup2(log_file.fileno(), sys.stdout.fileno())
            os.dup2(log_file.fileno(), sys.stderr.fileno())

            # Initialize the matrix after fork (GPIO resources don't survive fork)
            try:
                logger.info("Initializing matrix after fork...")
                init_matrix(for_daemon=True)
                logger.info("Matrix initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize matrix: {e}", exc_info=True)
                sys.exit(1)
        else:
            # No fork - write PID of current process
            with open(pid_file, "w") as f:
                f.write(str(os.getpid()))
            logger.info(f"PID file written: {pid_file}")

        # Start threads
        self.effect_thread = threading.Thread(target=self.effect_worker, daemon=False)
        self.ipc_thread = threading.Thread(target=self.ipc_worker, daemon=False)

        self.effect_thread.start()
        self.ipc_thread.start()

        # Start web server if enabled
        if self.webserver_enabled:
            self.webserver_thread = threading.Thread(target=self.webserver_worker, daemon=False)
            self.webserver_thread.start()
            logger.info(f"Daemon started with web server on port {self.webserver_port}")
        else:
            logger.info("Daemon started")

    def wait(self):
        """Wait for threads to finish"""
        try:
            self.effect_thread.join()
            self.ipc_thread.join()
            if self.webserver_thread:
                self.webserver_thread.join()
        except KeyboardInterrupt:
            logger.info("Interrupted, shutting down...")
            self.running = False
            self.effect_thread.join(timeout=2)
            self.ipc_thread.join(timeout=2)
            if self.webserver_thread:
                self.webserver_thread.join(timeout=2)
        finally:
            # Clean up PID file
            pid_file = "/tmp/led-matrix.pid"
            try:
                os.unlink(pid_file)
                logger.info("PID file removed")
            except OSError:
                pass


def get_effect_options(effect_name):
    """Get merged options for an effect (defaults + custom)"""
    if effect_name not in DEMOS:
        return {}

    defaults = {k: v[0] for k, v in DEMOS[effect_name][2].items()}
    custom = EFFECT_OPTIONS.get(effect_name, {})
    return {**defaults, **custom}


def parse_args():
    parser = argparse.ArgumentParser(
        description="LED Matrix Demo - Colorful animations for RGB LED matrix",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demos.py                      # Run all demos in a loop
  python demos.py --list               # List available effects
  python demos.py --list-opts          # List effect options
  python demos.py --night              # Night mode (darker effects)
  python demos.py -e fireworks         # Run only fireworks
  python demos.py -e matrix,starfield  # Run specific effects
  python demos.py -d 15 --shuffle      # 15 sec each, random order
  python demos.py -e fire -d 0         # Run fire effect forever
  python demos.py --loops 2            # Run through all effects twice
  python demos.py -f 10                # Max spawn frequency (intense!)
  python demos.py -e lightning -f 8    # Frequent lightning storms

Effect-specific options (use --list-opts to see all):
  python demos.py -e balls --opts "balls:count=8,size=2"
  python demos.py -e fireworks --opts "fireworks:particles=50,gravity=0.2"
  python demos.py --opts "balls:count=3;starfield:count=200"
        """
    )
    parser.add_argument("-l", "--list", action="store_true",
                        help="List all available effects and exit")
    parser.add_argument("--list-opts", action="store_true",
                        help="List all effect-specific options and exit")
    parser.add_argument("-n", "--night", action="store_true",
                        help="Night mode: darker effects only")
    parser.add_argument("-p", "--low-power", action="store_true",
                        help="Low power mode: use only Pi Zero optimized effects (12 effects)")
    parser.add_argument("--high-power", action="store_true",
                        help="High power mode: use only Pi 3/4 optimized effects (10 effects)")
    parser.add_argument("-o", "--opts", type=str, default=None,
                        help="Effect-specific options (e.g., 'balls:count=8,size=2;fireworks:particles=50')")
    parser.add_argument("-e", "--effects", type=str, default=None,
                        help="Comma-separated list of effects to run (e.g., fireworks,matrix,starfield)")
    parser.add_argument("-d", "--duration", type=float, default=8,
                        help="Duration of each effect in seconds (0 = run forever, default: 8)")
    parser.add_argument("-s", "--shuffle", action="store_true",
                        help="Randomize the order of effects")
    parser.add_argument("--loops", type=int, default=0,
                        help="Number of loops (0 = infinite, default: 0)")
    parser.add_argument("-f", "--frequency", type=int, default=5, choices=range(1, 11),
                        metavar="1-10", help="Spawn frequency for effects like fireworks/lightning (1=rare, 10=frequent, default: 5)")
    parser.add_argument("--pause", type=float, default=0.5,
                        help="Pause between effects in seconds (default: 0.5)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose logging for troubleshooting")
    parser.add_argument("--daemon", action="store_true",
                        help="Run as a daemon with IPC control socket")
    parser.add_argument("--socket", type=str, default="/tmp/led-matrix.sock",
                        help="Unix socket path for daemon mode (default: /tmp/led-matrix.sock)")
    parser.add_argument("--webserver", action="store_true",
                        help="Run web server for browser-based control (requires Flask)")
    parser.add_argument("--port", type=int, default=80,
                        help="Port for web server (default: 80, requires sudo)")
    return parser.parse_args()


def setup_logging(verbose):
    """Configure logging based on verbose flag"""
    if verbose:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)

    logger.debug(f"Arguments: {vars(args)}")

    # List effects and exit
    if args.list:
        print("Available effects:")
        for key, (name, _, _) in DEMOS.items():
            print(f"  {key:12} - {name}")
        sys.exit(0)

    # List effect options and exit
    if args.list_opts:
        print("Effect-specific options:")
        print("Use with: --opts 'effect:option=value,option2=value2'")
        print()
        for key, (name, _, opts) in DEMOS.items():
            print(f"  {key}:")
            for opt_name, (default, desc) in opts.items():
                print(f"    {opt_name:12} = {default!r:8} - {desc}")
        sys.exit(0)

    # Parse effect-specific options
    if args.opts:
        EFFECT_OPTIONS.update(parse_effect_opts(args.opts))
        logger.debug(f"Custom effect options: {EFFECT_OPTIONS}")

    # Determine which effects to run
    if args.effects:
        effect_keys = [e.strip() for e in args.effects.split(",")]
        for key in effect_keys:
            if key not in DEMOS:
                print(f"Error: Unknown effect '{key}'")
                print(f"Use --list to see available effects")
                sys.exit(1)
    elif args.low_power:
        effect_keys = LOW_POWER_ORDER.copy()
    elif args.high_power:
        effect_keys = HIGH_POWER_ORDER.copy()
    elif args.night:
        effect_keys = NIGHT_MODE.copy()
    else:
        effect_keys = DEFAULT_ORDER.copy()

    if args.shuffle:
        shuffle(effect_keys)
        logger.debug("Effect order shuffled")

    logger.info(f"Running effects: {effect_keys}")
    logger.info(f"Duration: {args.duration}s, Frequency: {args.frequency}, Pause: {args.pause}s")

    # Web server mode (standalone, without daemon)
    if args.webserver and not args.daemon:
        print("LED Matrix Web Server (Standalone Mode)")
        print(f"Port: {args.port}")
        print("Open your browser to control the LED matrix")
        print(f"Make sure daemon is running: sudo python demos.py --daemon")
        print()

        try:
            import webserver
            webserver.app.run(host='0.0.0.0', port=args.port, debug=False)
        except ImportError:
            print("Error: Flask not installed. Install with: pip install flask")
            sys.exit(1)
        except PermissionError:
            print(f"Error: Permission denied. Port {args.port} requires sudo.")
            sys.exit(1)
        sys.exit(0)

    # Initialize matrix for normal mode (daemon mode initializes after fork)
    if not args.daemon:
        logger.debug(f"Initializing matrix: {ROWS}x{COLS}, mapping={options.hardware_mapping}")
        init_matrix(for_daemon=False)
        logger.debug("Matrix initialized successfully")

    # Daemon mode
    if args.daemon:
        print("LED Matrix Daemon")
        print(f"Socket: {args.socket}")
        print(f"PID file: /tmp/led-matrix.pid")
        print(f"Log file: /tmp/led-matrix.log")
        print(f"Effects: {', '.join(effect_keys)}")
        if args.webserver:
            print(f"Web server: http://0.0.0.0:{args.port}")
        print()

        # Enable logging for daemon mode
        if not args.verbose:
            setup_logging(True)

        daemon = DaemonController(
            args.socket,
            args,
            effect_keys,
            webserver_enabled=args.webserver,
            webserver_port=args.port
        )
        daemon.start(fork=True)  # This will fork and parent exits, returning to shell
        # Code below only runs in child process
        daemon.wait()
        logger.info("Daemon finished")
    else:
        # Normal mode
        print("LED Matrix Demo - Press Ctrl+C to exit")
        print(f"Effects: {', '.join(effect_keys)}")
        print(f"Duration: {'forever' if args.duration == 0 else f'{args.duration}s'} each")
        if args.loops > 0:
            print(f"Loops: {args.loops}")
        print()

        try:
            loop_count = 0
            while args.loops == 0 or loop_count < args.loops:
                for key in effect_keys:
                    name, func, _ = DEMOS[key]
                    opts = get_effect_options(key)
                    logger.debug(f"Starting effect '{key}' with options: {opts}")
                    print(f"Now showing: {name}")

                    start = time.time()
                    if args.duration == 0:
                        # Run forever (until Ctrl+C)
                        func(duration=999999, frequency=args.frequency, **opts)
                    else:
                        func(duration=args.duration, frequency=args.frequency, **opts)

                    elapsed = time.time() - start
                    logger.debug(f"Effect '{key}' finished after {elapsed:.2f}s")

                    matrix.Clear()
                    time.sleep(args.pause)

                loop_count += 1
                logger.debug(f"Completed loop {loop_count}")
                if args.shuffle and (args.loops == 0 or loop_count < args.loops):
                    shuffle(effect_keys)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            print("\nExiting...")
            matrix.Clear()

        logger.info("Demo finished")
