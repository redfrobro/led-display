import time
import math
import sys
import os
import argparse
from random import randrange, random, choice, shuffle

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from rgbmatrix import RGBMatrix, RGBMatrixOptions

ROWS = 32
COLS = 64

options = RGBMatrixOptions()
options.hardware_mapping = 'adafruit-hat'
options.rows = ROWS
options.cols = COLS
options.parallel = 1

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


def plasma_effect(duration=8, frequency=5, speed=1.0, **kwargs):
    """Smooth psychedelic plasma waves - optimized for Pi Zero"""
    start_time = time.time()
    t = 0
    while time.time() - start_time < duration:
        for y in range(ROWS):
            for x in range(COLS):
                value = fast_sin(x + t * 8) + fast_sin(y + t * 4)
                value += fast_sin(x + y + t * 6) + fast_sin(DIST_TABLE[y][x] + t * 8)
                hue = int(value * 45 + t * 50) % 360
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                matrix.SetPixel(x, y, r, g, b)
        t += 0.15 * speed
        time.sleep(0.02)


def fire_effect(duration=8, frequency=5, intensity=4, cooling=3, **kwargs):
    """Realistic rising flame effect"""
    heat = [[0] * COLS for _ in range(ROWS)]
    start_time = time.time()

    while time.time() - start_time < duration:
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


def matrix_rain(duration=8, frequency=5, speed=1.0, length=10, **kwargs):
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


def sparkle_twinkle(duration=8, frequency=5, saturation=0.3, **kwargs):
    """Twinkling stars effect"""
    stars = {}
    # frequency 1=few(2), 5=default(5), 10=many(10)
    stars_per_frame = max(1, frequency)
    start_time = time.time()

    while time.time() - start_time < duration:
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


def meteor_shower(duration=8, frequency=5, length=12, speed=1.0, **kwargs):
    """Diagonal meteors with glowing trails"""
    meteors = []
    # frequency 1=rare(16), 5=default(8), 10=frequent(2)
    spawn_rate = max(2, 18 - (frequency * 1.6))
    min_len = max(4, length - 4)
    max_len = length + 4

    start_time = time.time()
    while time.time() - start_time < duration:
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


def spiral_effect(duration=8, frequency=5, speed=5, density=10, **kwargs):
    """Spiral pattern from center - optimized for Pi Zero"""
    start_time = time.time()
    hue_offset = 0

    while time.time() - start_time < duration:
        for y in range(ROWS):
            for x in range(COLS):
                hue = (ANGLE_TABLE[y][x] + int(DIST_TABLE[y][x] * density) + hue_offset) % 360
                r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
                matrix.SetPixel(x, y, r, g, b)

        hue_offset += speed
        time.sleep(0.02)


def bouncing_balls(duration=8, frequency=5, count=5, size=1, trail=10, **kwargs):
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


def lightning(duration=8, frequency=5, branches=True, fade=1.0, color=240, **kwargs):
    """Random lightning bolts effect"""
    bolts = []
    # frequency 1=rare(25), 5=default(12), 10=frequent(2)
    spawn_rate = max(2, 27 - (frequency * 2.5))

    start_time = time.time()
    while time.time() - start_time < duration:
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


def fireworks(duration=8, frequency=5, particles=30, gravity=0.1, **kwargs):
    """Exploding fireworks effect"""
    active_particles = []
    # frequency 1=rare(30), 5=default(15), 10=frequent(3)
    spawn_rate = max(3, 33 - (frequency * 3))

    start_time = time.time()
    while time.time() - start_time < duration:
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


def starfield(duration=8, frequency=5, count=100, speed=0.02, **kwargs):
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


def rising_bubbles(duration=8, frequency=5, size=2, wobble=2, **kwargs):
    """Colorful bubbles rising up"""
    bubbles = []
    # frequency 1=rare(10), 5=default(4), 10=frequent(1)
    spawn_rate = max(1, 11 - frequency)
    max_size = max(1, size)

    start_time = time.time()
    while time.time() - start_time < duration:
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


def comet(duration=8, frequency=5, trail=25, speed=0.15, **kwargs):
    """Orbiting comet with colorful trail"""
    trail_points = []
    angle = 0
    hue = randrange(360)

    start_time = time.time()
    while time.time() - start_time < duration:
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


# All demo functions with their customizable options
# Format: "name": (display_name, function, {option: (default, description)})
DEMOS = {
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
}

# Effect options storage
EFFECT_OPTIONS = {}

DEFAULT_ORDER = ["plasma", "fire", "matrix", "sparkle", "meteor", "spiral",
                 "balls", "lightning", "fireworks", "starfield", "bubbles", "comet"]

NIGHT_MODE = ["matrix", "sparkle", "balls", "lightning", "fireworks", "starfield"]


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
                        help="Night mode: darker effects only (matrix, sparkle, balls, lightning, fireworks, starfield)")
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

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

    # Determine which effects to run
    if args.effects:
        effect_keys = [e.strip() for e in args.effects.split(",")]
        for key in effect_keys:
            if key not in DEMOS:
                print(f"Error: Unknown effect '{key}'")
                print(f"Use --list to see available effects")
                sys.exit(1)
    elif args.night:
        effect_keys = NIGHT_MODE.copy()
    else:
        effect_keys = DEFAULT_ORDER.copy()

    if args.shuffle:
        shuffle(effect_keys)

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
                print(f"Now showing: {name}")

                if args.duration == 0:
                    # Run forever (until Ctrl+C)
                    func(duration=999999, frequency=args.frequency, **opts)
                else:
                    func(duration=args.duration, frequency=args.frequency, **opts)

                matrix.Clear()
                time.sleep(args.pause)

            loop_count += 1
            if args.shuffle and (args.loops == 0 or loop_count < args.loops):
                shuffle(effect_keys)

    except KeyboardInterrupt:
        print("\nExiting...")
        matrix.Clear()
