"""Playlist management for LED matrix effects

This module provides functionality to create, load, save, and manage custom playlists
of LED effects with per-effect parameters.
"""

import os
import json
import fcntl
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


# Path configuration
PLAYLISTS_DIR = os.path.join(os.path.dirname(__file__), 'playlists')
BUILTIN_PLAYLISTS = {'low-power', 'high-power', 'night', 'all'}


def ensure_playlists_dir():
    """Create playlists directory if it doesn't exist"""
    if not os.path.exists(PLAYLISTS_DIR):
        os.makedirs(PLAYLISTS_DIR)


def get_playlist_path(name: str) -> str:
    """Get full path to playlist file"""
    return os.path.join(PLAYLISTS_DIR, f"{name}.json")


def load_playlist(name: str) -> dict:
    """Load and validate playlist from JSON file

    Args:
        name: Playlist name (without .json extension)

    Returns:
        Playlist data dictionary

    Raises:
        FileNotFoundError: If playlist doesn't exist
        ValueError: If playlist is invalid
    """
    path = get_playlist_path(name)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Playlist '{name}' not found at {path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Validate the loaded playlist
    is_valid, error = validate_playlist(data)
    if not is_valid:
        raise ValueError(f"Invalid playlist '{name}': {error}")

    return data


def save_playlist(name: str, data: dict):
    """Save playlist to JSON file with atomic writes and file locking

    Args:
        name: Playlist name (without .json extension)
        data: Playlist data dictionary

    Raises:
        ValueError: If data is invalid
        OSError: If file write fails
    """
    ensure_playlists_dir()

    # Validate before saving
    is_valid, error = validate_playlist(data)
    if not is_valid:
        raise ValueError(f"Cannot save invalid playlist: {error}")

    # Update modified timestamp
    data['modified'] = datetime.utcnow().isoformat() + 'Z'

    path = get_playlist_path(name)
    temp_path = path + '.tmp'

    # Write to temporary file with file locking
    with open(temp_path, 'w') as f:
        # Try to acquire lock with timeout
        timeout = 5.0
        start = time.time()
        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except IOError:
                if time.time() - start > timeout:
                    raise OSError("Could not acquire file lock for playlist save")
                time.sleep(0.1)

        try:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    # Atomic rename
    os.replace(temp_path, path)


def list_playlists() -> List[dict]:
    """List all available playlists with metadata

    Returns:
        List of dicts with playlist metadata (name, description, effect_count, etc.)
    """
    ensure_playlists_dir()

    playlists = []

    if not os.path.exists(PLAYLISTS_DIR):
        return playlists

    for filename in os.listdir(PLAYLISTS_DIR):
        if not filename.endswith('.json'):
            continue

        name = filename[:-5]  # Remove .json extension

        try:
            data = load_playlist(name)
            playlists.append({
                'name': name,
                'description': data.get('description', ''),
                'effect_count': len(data.get('effects', [])),
                'version': data.get('version', '1.0'),
                'created': data.get('created', ''),
                'modified': data.get('modified', ''),
                'is_builtin': name in BUILTIN_PLAYLISTS
            })
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            # Skip invalid playlists
            continue

    # Sort by name
    playlists.sort(key=lambda x: x['name'])

    return playlists


def validate_playlist(data: dict) -> Tuple[bool, Optional[str]]:
    """Validate playlist data structure and values

    Args:
        data: Playlist data dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    if not isinstance(data, dict):
        return False, "Playlist must be a dictionary"

    if 'name' not in data:
        return False, "Missing required field: name"

    if 'effects' not in data:
        return False, "Missing required field: effects"

    if not isinstance(data['effects'], list):
        return False, "Effects must be a list"

    # Validate optional mood field
    if 'mood' in data and data['mood'] is not None:
        try:
            from effects.utils import MOOD_PRESETS
            if data['mood'] not in MOOD_PRESETS:
                return False, f"Unknown mood: {data['mood']}"
        except ImportError:
            pass  # Skip mood validation without rgbmatrix

    # Import DEMOS to validate effect keys
    try:
        from effects import DEMOS
        from demos import validate_effect_option
    except ImportError as e:
        # Allow validation to pass if rgbmatrix is not available (e.g., on dev machine)
        # Just do basic structure validation
        import warnings
        warnings.warn(f"Cannot import effects module (likely missing rgbmatrix): {e}")
        DEMOS = {}
        validate_effect_option = lambda *args: True

    # Validate each effect
    for idx, effect in enumerate(data['effects']):
        if not isinstance(effect, dict):
            return False, f"Effect {idx} must be a dictionary"

        if 'key' not in effect:
            return False, f"Effect {idx} missing required field: key"

        effect_key = effect['key']

        # Check if effect exists (skip if DEMOS not available)
        if DEMOS and effect_key not in DEMOS:
            return False, f"Unknown effect: {effect_key}"

        # Validate duration if present
        if 'duration' in effect:
            duration = effect['duration']
            if not isinstance(duration, (int, float)) or duration < 0:
                return False, f"Effect {effect_key}: duration must be >= 0"

        # Validate params if present
        if 'params' in effect:
            params = effect['params']
            if not isinstance(params, dict):
                return False, f"Effect {effect_key}: params must be a dictionary"

            # Validate brightness (0-100)
            if 'brightness' in params:
                brightness = params['brightness']
                if not isinstance(brightness, (int, float)) or not (0 <= brightness <= 100):
                    return False, f"Effect {effect_key}: brightness must be 0-100"

            # Validate frequency (1-10)
            if 'frequency' in params:
                frequency = params['frequency']
                if not isinstance(frequency, (int, float)) or not (1 <= frequency <= 10):
                    return False, f"Effect {effect_key}: frequency must be 1-10"

            # Validate speed (0.1-5.0)
            if 'speed' in params:
                speed = params['speed']
                if not isinstance(speed, (int, float)) or not (0.1 <= speed <= 5.0):
                    return False, f"Effect {effect_key}: speed must be 0.1-5.0"

        # Validate options if present
        if 'options' in effect:
            options = effect['options']
            if not isinstance(options, dict):
                return False, f"Effect {effect_key}: options must be a dictionary"

            # Validate each option using existing validation (skip if DEMOS not available)
            if DEMOS and effect_key in DEMOS:
                effect_info = DEMOS[effect_key]
                valid_options = effect_info[2]  # Options dict from DEMOS

                for opt_key, opt_value in options.items():
                    if opt_key not in valid_options:
                        return False, f"Effect {effect_key}: unknown option '{opt_key}'"

                    # Use existing validation function
                    if not validate_effect_option(effect_key, opt_key, opt_value):
                        return False, f"Effect {effect_key}: invalid value for option '{opt_key}'"

    return True, None


def delete_playlist(name: str) -> bool:
    """Delete a playlist

    Args:
        name: Playlist name

    Returns:
        True if deleted, False if it's a built-in playlist or doesn't exist
    """
    # Don't allow deleting built-in playlists
    if name in BUILTIN_PLAYLISTS:
        return False

    path = get_playlist_path(name)

    if not os.path.exists(path):
        return False

    try:
        os.remove(path)
        return True
    except OSError:
        return False


def create_playlist(name: str, description: str = "") -> dict:
    """Create a new empty playlist structure

    Args:
        name: Playlist name
        description: Optional description

    Returns:
        New playlist data dictionary
    """
    now = datetime.utcnow().isoformat() + 'Z'

    return {
        "name": name,
        "description": description,
        "version": "1.0",
        "created": now,
        "modified": now,
        "mood": None,
        "effects": []
    }


def migrate_builtin_playlists():
    """Create built-in playlists from hardcoded effect lists in demos.py

    This should be called once on first startup to populate the playlists directory.
    """
    ensure_playlists_dir()

    try:
        from effects import LOW_POWER_ORDER, HIGH_POWER_ORDER, NIGHT_MODE, DEFAULT_ORDER
    except ImportError:
        raise ImportError("Cannot import effect lists from effects module")

    # Define built-in playlists
    builtin_configs = [
        ('low-power', 'Pi Zero optimized effects (12 effects)', LOW_POWER_ORDER),
        ('high-power', 'Pi 3/4 high-performance effects (10 effects)', HIGH_POWER_ORDER),
        ('night', 'Dark effects suitable for nighttime (8 effects)', NIGHT_MODE),
        ('all', 'All available effects (22 effects)', DEFAULT_ORDER),
    ]

    for name, description, effect_list in builtin_configs:
        # Skip if already exists
        playlist_path = get_playlist_path(name)
        if os.path.exists(playlist_path):
            continue

        # Create playlist
        playlist = create_playlist(name, description)

        # Add effects with default parameters
        for effect_key in effect_list:
            playlist['effects'].append({
                'key': effect_key,
                'duration': 8,  # Default duration
                'params': {},   # Use global params
                'options': {}   # Use default options
            })

        # Save playlist
        save_playlist(name, playlist)


def get_effect_from_playlist(playlist_data: dict, effect_key: str) -> Optional[dict]:
    """Get effect configuration from playlist

    Args:
        playlist_data: Playlist data dictionary
        effect_key: Effect key to find

    Returns:
        Effect configuration dict or None if not found
    """
    for effect in playlist_data.get('effects', []):
        if effect.get('key') == effect_key:
            return effect
    return None


def add_effect_to_playlist(playlist_data: dict, effect_key: str,
                           duration: int = 8, params: Optional[dict] = None,
                           options: Optional[dict] = None) -> dict:
    """Add an effect to a playlist

    Args:
        playlist_data: Playlist data dictionary
        effect_key: Effect key to add
        duration: Effect duration in seconds
        params: Optional params dict (brightness, frequency, speed)
        options: Optional effect-specific options

    Returns:
        Updated playlist data

    Raises:
        ValueError: If effect is invalid
    """
    try:
        from effects import DEMOS
        if effect_key not in DEMOS:
            raise ValueError(f"Unknown effect: {effect_key}")
    except ImportError:
        # Allow adding effects without validation if rgbmatrix not available
        pass

    effect = {
        'key': effect_key,
        'duration': duration,
        'params': params or {},
        'options': options or {}
    }

    playlist_data['effects'].append(effect)
    playlist_data['modified'] = datetime.utcnow().isoformat() + 'Z'

    return playlist_data


def remove_effect_from_playlist(playlist_data: dict, effect_key: str) -> dict:
    """Remove an effect from a playlist

    Args:
        playlist_data: Playlist data dictionary
        effect_key: Effect key to remove

    Returns:
        Updated playlist data
    """
    playlist_data['effects'] = [e for e in playlist_data['effects']
                                 if e.get('key') != effect_key]
    playlist_data['modified'] = datetime.utcnow().isoformat() + 'Z'

    return playlist_data
