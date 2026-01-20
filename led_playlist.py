#!/usr/bin/env python3
"""LED Matrix Playlist Management CLI

Command-line interface for creating, editing, and managing LED effect playlists.
"""

import sys
import argparse
import json
from typing import Optional

import playlist_manager

# Import DEMOS only when needed (deferred import to avoid rgbmatrix dependency)
DEMOS = None

def get_demos():
    """Lazy load DEMOS dict from effects module"""
    global DEMOS
    if DEMOS is None:
        try:
            from effects import DEMOS as _DEMOS
            DEMOS = _DEMOS
        except ImportError as e:
            print(f"Warning: Could not import DEMOS from effects module: {e}", file=sys.stderr)
            DEMOS = {}
    return DEMOS


def cmd_list(args):
    """List all available playlists"""
    playlists = playlist_manager.list_playlists()

    if not playlists:
        print("No playlists found. Create one with 'led-playlist create <name>'")
        return 0

    print(f"{'Playlist':<20} {'Effects':<10} {'Description'}")
    print("-" * 70)

    for p in playlists:
        builtin_marker = " [built-in]" if p['is_builtin'] else ""
        desc = p['description'][:40] + "..." if len(p['description']) > 40 else p['description']
        print(f"{p['name']:<20} {p['effect_count']:<10} {desc}{builtin_marker}")

    print(f"\nTotal: {len(playlists)} playlists")
    return 0


def cmd_show(args):
    """Show playlist details"""
    try:
        data = playlist_manager.load_playlist(args.name)

        print(f"Playlist: {data['name']}")
        print(f"Description: {data.get('description', 'N/A')}")
        print(f"Version: {data.get('version', '1.0')}")
        print(f"Created: {data.get('created', 'N/A')}")
        print(f"Modified: {data.get('modified', 'N/A')}")
        print(f"\nEffects ({len(data['effects'])}):")
        print("-" * 80)

        for idx, effect in enumerate(data['effects'], 1):
            effect_key = effect['key']
            effect_info = get_demos().get(effect_key)
            effect_name = effect_info[0] if effect_info else effect_key

            print(f"\n{idx}. {effect_key} ({effect_name})")

            # Show duration
            duration = effect.get('duration', 8)
            print(f"   Duration: {duration}s")

            # Show params
            params = effect.get('params', {})
            if params:
                print(f"   Params:")
                for key, value in params.items():
                    print(f"     - {key}: {value}")

            # Show options
            options = effect.get('options', {})
            if options:
                print(f"   Options:")
                for key, value in options.items():
                    print(f"     - {key}: {value}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_create(args):
    """Create a new playlist"""
    try:
        # Check if playlist already exists
        path = playlist_manager.get_playlist_path(args.name)
        import os
        if os.path.exists(path):
            print(f"Error: Playlist '{args.name}' already exists", file=sys.stderr)
            return 1

        # Create new playlist
        data = playlist_manager.create_playlist(args.name, args.description or "")
        playlist_manager.save_playlist(args.name, data)

        print(f"Created playlist '{args.name}'")
        print(f"Add effects with: led-playlist add {args.name} <effect>")
        return 0

    except Exception as e:
        print(f"Error creating playlist: {e}", file=sys.stderr)
        return 1


def cmd_delete(args):
    """Delete a playlist"""
    if args.name in playlist_manager.BUILTIN_PLAYLISTS:
        print(f"Error: Cannot delete built-in playlist '{args.name}'", file=sys.stderr)
        return 1

    # Confirm deletion unless --force
    if not args.force:
        try:
            response = input(f"Delete playlist '{args.name}'? [y/N] ")
            if response.lower() != 'y':
                print("Cancelled")
                return 0
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled")
            return 0

    success = playlist_manager.delete_playlist(args.name)

    if success:
        print(f"Deleted playlist '{args.name}'")
        return 0
    else:
        print(f"Error: Playlist '{args.name}' not found", file=sys.stderr)
        return 1


def cmd_add(args):
    """Add an effect to a playlist"""
    try:
        # Validate effect (skip if DEMOS not available)
        demos = get_demos()
        if demos and args.effect not in demos:
            print(f"Error: Unknown effect '{args.effect}'", file=sys.stderr)
            print(f"Available effects: {', '.join(sorted(demos.keys()))}")
            return 1

        # Load playlist
        data = playlist_manager.load_playlist(args.playlist)

        # Build params dict
        params = {}
        if args.brightness is not None:
            params['brightness'] = args.brightness
        if args.frequency is not None:
            params['frequency'] = args.frequency
        if args.speed is not None:
            params['speed'] = args.speed

        # Parse options
        options = {}
        if args.opt:
            for opt_str in args.opt:
                for pair in opt_str.split(','):
                    if '=' not in pair:
                        print(f"Error: Invalid option format '{pair}'. Use key=value", file=sys.stderr)
                        return 1

                    key, value = pair.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Try to parse as number
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        # Keep as string, handle booleans
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False

                    options[key] = value

        # Add effect
        playlist_manager.add_effect_to_playlist(
            data, args.effect,
            duration=args.duration,
            params=params,
            options=options
        )

        # Save playlist
        playlist_manager.save_playlist(args.playlist, data)

        print(f"Added '{args.effect}' to playlist '{args.playlist}'")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_remove(args):
    """Remove an effect from a playlist"""
    try:
        # Load playlist
        data = playlist_manager.load_playlist(args.playlist)

        # Check if effect exists in playlist
        effect_exists = any(e['key'] == args.effect for e in data['effects'])
        if not effect_exists:
            print(f"Error: Effect '{args.effect}' not found in playlist '{args.playlist}'", file=sys.stderr)
            return 1

        # Remove effect
        playlist_manager.remove_effect_from_playlist(data, args.effect)

        # Save playlist
        playlist_manager.save_playlist(args.playlist, data)

        print(f"Removed '{args.effect}' from playlist '{args.playlist}'")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_reorder(args):
    """Reorder an effect in a playlist"""
    try:
        # Load playlist
        data = playlist_manager.load_playlist(args.playlist)

        # Find effect
        effect_idx = None
        for idx, effect in enumerate(data['effects']):
            if effect['key'] == args.effect:
                effect_idx = idx
                break

        if effect_idx is None:
            print(f"Error: Effect '{args.effect}' not found in playlist '{args.playlist}'", file=sys.stderr)
            return 1

        # Validate position
        position = args.position
        if position < 0 or position >= len(data['effects']):
            print(f"Error: Position must be between 0 and {len(data['effects']) - 1}", file=sys.stderr)
            return 1

        # Move effect
        effect = data['effects'].pop(effect_idx)
        data['effects'].insert(position, effect)

        # Save playlist
        from datetime import datetime
        data['modified'] = datetime.utcnow().isoformat() + 'Z'
        playlist_manager.save_playlist(args.playlist, data)

        print(f"Moved '{args.effect}' to position {position} in playlist '{args.playlist}'")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_rename(args):
    """Rename a playlist"""
    if args.old in playlist_manager.BUILTIN_PLAYLISTS:
        print(f"Error: Cannot rename built-in playlist '{args.old}'", file=sys.stderr)
        return 1

    try:
        import os

        old_path = playlist_manager.get_playlist_path(args.old)
        new_path = playlist_manager.get_playlist_path(args.new)

        if not os.path.exists(old_path):
            print(f"Error: Playlist '{args.old}' not found", file=sys.stderr)
            return 1

        if os.path.exists(new_path):
            print(f"Error: Playlist '{args.new}' already exists", file=sys.stderr)
            return 1

        # Load, update name, save to new location
        data = playlist_manager.load_playlist(args.old)
        data['name'] = args.new
        playlist_manager.save_playlist(args.new, data)

        # Delete old file
        os.remove(old_path)

        print(f"Renamed playlist '{args.old}' to '{args.new}'")
        return 0

    except Exception as e:
        print(f"Error renaming playlist: {e}", file=sys.stderr)
        return 1


def cmd_clone(args):
    """Clone a playlist"""
    try:
        import os

        dest_path = playlist_manager.get_playlist_path(args.dest)

        if os.path.exists(dest_path):
            print(f"Error: Playlist '{args.dest}' already exists", file=sys.stderr)
            return 1

        # Load source
        data = playlist_manager.load_playlist(args.source)

        # Update metadata
        data['name'] = args.dest
        from datetime import datetime
        now = datetime.utcnow().isoformat() + 'Z'
        data['created'] = now
        data['modified'] = now

        # Save clone
        playlist_manager.save_playlist(args.dest, data)

        print(f"Cloned playlist '{args.source}' to '{args.dest}'")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error cloning playlist: {e}", file=sys.stderr)
        return 1


def cmd_validate(args):
    """Validate a playlist"""
    try:
        data = playlist_manager.load_playlist(args.name)

        is_valid, error = playlist_manager.validate_playlist(data)

        if is_valid:
            print(f"✓ Playlist '{args.name}' is valid")
            print(f"  - {len(data['effects'])} effects")
            return 0
        else:
            print(f"✗ Playlist '{args.name}' is invalid:", file=sys.stderr)
            print(f"  {error}", file=sys.stderr)
            return 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error validating playlist: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='LED Matrix Playlist Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all playlists
  led-playlist list

  # Create a new playlist
  led-playlist create my-favorites --description "My favorite effects"

  # Add effects to a playlist
  led-playlist add my-favorites fireworks --brightness 80 --frequency 8
  led-playlist add my-favorites aurora --duration 15 --speed 2.0
  led-playlist add my-favorites lightning --opt branches=true,color=240

  # Show playlist contents
  led-playlist show my-favorites

  # Remove an effect
  led-playlist remove my-favorites fireworks

  # Clone a playlist
  led-playlist clone low-power my-low-power

  # Validate a playlist
  led-playlist validate my-favorites
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # list command
    subparsers.add_parser('list', help='List all playlists')

    # show command
    parser_show = subparsers.add_parser('show', help='Show playlist details')
    parser_show.add_argument('name', help='Playlist name')

    # create command
    parser_create = subparsers.add_parser('create', help='Create a new playlist')
    parser_create.add_argument('name', help='Playlist name')
    parser_create.add_argument('--description', '-d', help='Playlist description')

    # delete command
    parser_delete = subparsers.add_parser('delete', help='Delete a playlist')
    parser_delete.add_argument('name', help='Playlist name')
    parser_delete.add_argument('--force', '-f', action='store_true',
                              help='Skip confirmation prompt')

    # add command
    parser_add = subparsers.add_parser('add', help='Add an effect to a playlist')
    parser_add.add_argument('playlist', help='Playlist name')
    parser_add.add_argument('effect', help='Effect key')
    parser_add.add_argument('--duration', type=int, default=8,
                           help='Effect duration in seconds (default: 8)')
    parser_add.add_argument('--brightness', type=int,
                           help='Brightness 0-100')
    parser_add.add_argument('--frequency', type=int,
                           help='Spawn frequency 1-10')
    parser_add.add_argument('--speed', type=float,
                           help='Speed multiplier 0.1-5.0')
    parser_add.add_argument('--opt', action='append',
                           help='Effect-specific options (key=value,key2=value2)')

    # remove command
    parser_remove = subparsers.add_parser('remove', help='Remove an effect from a playlist')
    parser_remove.add_argument('playlist', help='Playlist name')
    parser_remove.add_argument('effect', help='Effect key')

    # reorder command
    parser_reorder = subparsers.add_parser('reorder', help='Reorder an effect in a playlist')
    parser_reorder.add_argument('playlist', help='Playlist name')
    parser_reorder.add_argument('effect', help='Effect key')
    parser_reorder.add_argument('position', type=int, help='New position (0-based index)')

    # rename command
    parser_rename = subparsers.add_parser('rename', help='Rename a playlist')
    parser_rename.add_argument('old', help='Current playlist name')
    parser_rename.add_argument('new', help='New playlist name')

    # clone command
    parser_clone = subparsers.add_parser('clone', help='Clone a playlist')
    parser_clone.add_argument('source', help='Source playlist name')
    parser_clone.add_argument('dest', help='Destination playlist name')

    # validate command
    parser_validate = subparsers.add_parser('validate', help='Validate a playlist')
    parser_validate.add_argument('name', help='Playlist name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatch to command handler
    commands = {
        'list': cmd_list,
        'show': cmd_show,
        'create': cmd_create,
        'delete': cmd_delete,
        'add': cmd_add,
        'remove': cmd_remove,
        'reorder': cmd_reorder,
        'rename': cmd_rename,
        'clone': cmd_clone,
        'validate': cmd_validate,
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
