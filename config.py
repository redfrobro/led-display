"""Configuration loader for LED matrix settings.

Reads settings.toml from the project directory.
Command-line arguments take precedence over settings.toml values.
"""

import os

try:
    import tomllib          # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # pip install tomli
    except ImportError:
        tomllib = None

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(_PROJECT_DIR, 'settings.toml')

# Hardcoded fallback defaults
_DEFAULTS = {
    'display': {
        'rows': 32,
        'cols': 64,
        'hardware_mapping': 'adafruit-hat',
        'parallel': 1,
    },
    'daemon': {
        'duration': 8,
        'frequency': 5,
        'pause': 0.5,
        'brightness': 100,
        'speed': 1.0,
        'port': 80,
        'socket': '/tmp/led-matrix.sock',
    },
    'startup': {
        'display_duration': 15,
        'font': '4x6.bdf',
    },
    'mood_presets': {},
}


def load():
    """Load settings.toml, merged over hardcoded defaults."""
    # Deep copy defaults
    result = {k: dict(v) for k, v in _DEFAULTS.items()}

    if tomllib is None:
        return result

    if not os.path.exists(SETTINGS_PATH):
        return result

    try:
        with open(SETTINGS_PATH, 'rb') as f:
            user = tomllib.load(f)
        for section, values in user.items():
            if section in result and isinstance(values, dict):
                result[section].update(values)
            else:
                result[section] = values
    except Exception as e:
        print(f"Warning: Failed to load settings.toml: {e}")

    return result


# Loaded once at import time
settings = load()