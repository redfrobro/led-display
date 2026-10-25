# Known Issues

Findings from a code and docs review (2026-10-24). Static review only, not verified on hardware.

## Bugs

- [x] **#1 Brightness does nothing.** `DaemonController.apply_brightness` (`demos.py:409`) is never called and `matrix.brightness` is never set. The `brightness` command, web slider, and playlist `params.brightness` are all no-ops.
  - Fixed: `matrix.brightness` is set at init, per effect (playlist override or global), and live by the `brightness` command; the text effect copies it to its canvas and redraws static text on change. Needs a hardware check (20 / 100 / 0 on fireworks and static text).
- [x] **#2 Global speed does nothing.** `if 'speed' not in opts` (`demos.py:465`, `:1313`) is always false for effects with a `speed` option because defaults are already merged in; effects without one swallow it in `**kwargs`. Per-effect `speed` options also mean different things (comet 0.15, starfield 0.02, spiral 5), so a global multiplier can't simply be passed through.
  - Fixed: effects call `ctx.sleep()` for their frame delay, which divides by the live global speed (or the playlist's per-effect speed). Per-effect `speed` options are untouched. Speed-up is capped by per-frame compute time on heavy effects (aurora/swirl/waves reach ~1.5-1.7x at 2x even on a desktop).
- [x] **#3 One effect exception kills the display.** The `try` at `demos.py:425` wraps the whole loop; the worker exits but `effects_running` stays True, so `on` says "already running". Trigger: enter `42` or `3.14` as text in the web UI — `opt` parsing (`demos.py:672-680`) makes it a number, `text.split()` crashes, and the value is persisted to `text_config.json`.
  - Fixed: each effect run is wrapped (log, clear, 2s backoff, move on) in daemon and normal mode; the worker marks `effects_running = False` on exit so `on` works. `opt` and `--opts` share `coerce_option()`, which converts by the default's type (`text` always a string), rejects unknown keys and unparseable values, and rounds fractional input for whole-number options. Saved numeric text is converted to a string on load. Spiral's `speed` default is now `5.0` so fractional values stay fractional.
- [x] **#4 Startup IP display overwrites saved text config.** `run_effect` injects `config_saver` for `text` (`demos.py:326`) and `text_display` saves every non-None arg (`effects/text.py:62-80`). Daemon also passes option defaults explicitly, so saved font/speed/hue are never used.
  - Fixed: `text_display` only displays; settings are saved only by the `opt` command. `get_effect_options('text')` layers declared defaults < `text_config.json` < `--opts`, and the daemon adds playlist/`opt` values on top (playlist values aren't saved). One set of defaults (from the `@effect` declaration). Removed unused `load_text_config`/`save_text_config`; `text_config.json` is gitignored. A config already overwritten with the IP must be re-entered once.
- [x] **#5 Daemon ignores playlist per-effect settings at startup.** `effect_durations`/`effect_params` built in `__main__` (`demos.py:1194-1207`) are never passed to `DaemonController`; `current_playlist_name` stays None.
  - Fixed: `playlist_settings()` extracts keys/durations/params once; `DaemonController.apply_playlist()` is used at startup and by `load_playlist` (also applies mood, and `--shuffle`). Startup playlists, including built-ins from `--low-power` etc., now set `current_playlist_name`. Normal mode applies the playlist mood. Known limit: settings are keyed by effect name, so duplicate effects in one playlist share the last entry's settings.
- [x] **#6 `set <effect>` permanently sets global duration to 0** (`demos.py:559`, `:566`). After next/prev/playlist, every effect runs forever.
  - Fixed: single mode always runs the effect indefinitely; `set` no longer touches `self.duration`. `duration` in single mode notes it applies in playlist mode.
- [x] **#7 Empty playlist busy-loops at 100% CPU** (`demos.py:426-439`). The web UI can create and load an empty playlist.
  - Fixed: `load_playlist` refuses a playlist with no effects (keeps the current one); `--playlist` with no effects exits with an error. The worker waits on the condition instead of spinning if the effect list is ever empty, and won't divide by zero if it empties mid-playlist. Saving empty playlists is still allowed so the web UI can build them up.
- [x] **#8 `stop` doesn't stop the daemon.** Code treats `stop` as `off` (`demos.py:575`); docs say it shuts down daemon + web server. Nothing sets `running = False` in a detached daemon, and there's no SIGTERM handler, so the matrix isn't cleared and the socket isn't removed (including on `systemctl stop`).
  - Decision: `stop` should only stop the display (current behaviour).
  - Fixed: SIGTERM handler; `wait()` polls and runs a shared `shutdown()` (stop effects/IPC/web, join threads, clear matrix, remove socket + PID file). Docs, `led-control` help, and the web UI button now say `stop` = display off, `kill` = clean daemon shutdown. Tested with a forked daemon: exits in ~0.4s with display cleared and files removed.
- [x] **#9 Starting a second daemon clobbers the first's PID file** (`demos.py:903`) before checking whether one is running.
  - Fixed: `running_daemon_pid()` checks the PID file (process must be a live `demos.py`, so reused PIDs don't count) and whether the socket answers; daemon and normal mode both refuse to start if one is running. Note: with the systemd service installed, a manually started daemon makes the service fail/retry until it's shut down.

## Security

Web server runs as root on `0.0.0.0:80` with no auth.

- [x] **#10 Path traversal in playlist names.** `POST /api/playlist` takes `name` from the JSON body; `get_playlist_path` (`playlist_manager.py:28`) joins it unchecked, so `../../etc/foo` writes `/etc/foo.json` as root. Socket `load_playlist` has the same read-side issue. Validate names against `^[A-Za-z0-9_-]+$`.
  - Fixed: `get_playlist_path` only accepts `[A-Za-z0-9][A-Za-z0-9_-]{0,63}` and raises `ValueError` otherwise, covering the web API, socket `load_playlist`/`save_playlist`, `--playlist`, and `bin/led-playlist`. Web routes return 400; the web UI checks names before sending. `list_playlists` logs and skips files with invalid names (rename any existing ones with spaces or dots).
- [x] **#11 Unescaped values in web UI HTML** (`static/script.js:471`, `value="${option.default}"`). Text containing `"` breaks the input; stored XSS.
  - Fixed: added `escapeHtml()` in `script.js` and wrapped every value interpolated into `innerHTML` templates (option descriptions, ids, defaults/current values, playlist effect names and params). Inline `onclick` handlers still use raw option keys, which are Python identifiers from code.
- [x] **#12 Socket permissions (unverified).** Root-created socket with umask 022 likely rejects non-root `bin/led-control`, though docs show it run without sudo.
  - Confirmed: the daemon keeps root (`drop_privileges = False`), so the socket was `0755 root:root` and connecting (which needs write permission) failed for normal users.
  - Fixed: the daemon sets the socket to `0660` with the group from the new `socket_group` setting under `[daemon]` (default `gpio`; falls back to `SUDO_GID` with a warning if the group is missing; `""` = root only). `led-control` explains permission errors, and `kill` says to use sudo instead of printing a bare errno. Docs updated, including `sudo` on every `kill` example.
- [x] **#13 No access control** on the web UI. Consider basic auth or binding to a specific interface.
  - Fixed: optional HTTP Basic Auth, set with `bin/led-web-password` (PBKDF2 hash in gitignored `web_password`, mode 0600; any username; `--remove` turns it off; no restart needed). Off by default, and the daemon logs a warning while no password is set. New `host` setting under `[daemon]` picks the bind address, replacing the hard-coded `0.0.0.0` in daemon and standalone mode. Non-GET requests with a cross-site `Origin` get 403, which also covers the body-less `/api/start` and `/load` routes. Successful password checks are cached in memory, since the UI polls every second and hashing is slow on a Pi Zero.

## Smaller code issues

- [x] **#14** Built-in playlists are regenerated every start (`playlist_manager.py:306`): web UI edits to them are lost, tracked JSON files get dirtied with new timestamps each run, and duration 8 is hardcoded instead of read from `settings.toml`.
  - Fixed: `refresh_builtin_playlists()` only writes a built-in when its description or effects changed, keeping `created`. Entries use duration 0 (global duration), so `--duration`/`settings.toml` now apply to `--low-power` etc. (the hardcoded 8 overrode them). Built-ins are read-only: `save_playlist` refuses them with a "clone it first" hint (web PUT/POST → 400, socket and CLI show the error), and the web editor won't open them. The four files are untracked and gitignored. On the Pi, run `git checkout playlists/` before pulling.
- [ ] **#15** Mood presets are only registered when `demos.py` is imported (`demos.py:41`). In `bin/led-playlist` and the standalone web server, any playlist with a mood fails validation (`playlist_manager.py:172`).
- [ ] **#16** Category order is hardcoded (`effects/__init__.py:84-92`), so new effects don't appear in `--low-power`/`all`, contradicting EFFECTS.md.
- [ ] **#17** Most effects `Clear()` + `SetPixel` on the live matrix each frame (flicker/tearing). `text.py` already uses `CreateFrameCanvas`/`SwapOnVSync`.
- [ ] **#18** `effects/utils.py` hardcodes ROWS/COLS at 32x64 even though `settings.toml` makes them configurable; distance/angle tables break on other sizes.
- [ ] **#19** IPC does a single `recv(1024)` with no per-connection timeout (`demos.py:845`); a silent client blocks `led-control` and the web UI.
- [ ] **#20** Hardcoded `.jevin` domain at `demos.py:68`; "No network found" branch is unreachable.
- [ ] **#21** `request.json` can be None → 500 (`webserver.py:136`); fallback effect list at `webserver.py:67` is stale.
- [ ] **#22** `demos.py` is imported as both `__main__` and `demos`, so its top-level code runs twice. Move shared helpers to their own module.
- [ ] **#23** Minor: `flock` on the temp file in `save_playlist` protects nothing; `datetime.utcnow()` deprecated in 3.12; `shuffle(effect_keys)` (`demos.py:500`) runs outside the lock.

## Docs

- [ ] **#24** CLAUDE.md and argparse help (`demos.py:1019-1021`) say 22 effects / 12 low-power / 10 high-power; actual is 26 (+`text`) / 14 / 12.
- [ ] **#25** CLAUDE.md "Architecture" is outdated (no mention of `effects/`, `webserver.py`, `playlist_manager.py`, `config.py`/`settings.toml`, moods, `mood`/`duration` commands; options table missing `--opts`/`--list-opts`).
- [x] **#26** `stop` described as shutting down the daemon in CLAUDE.md, README (lines 193, 250, 255), and `led-control` help (see #8).
- [ ] **#27** `requirements.txt` doesn't say `rgbmatrix` must be built from rpi-rgb-led-matrix; `werkzeug` is redundant; Pillow is only used by `blink.py`.
- [ ] **#28** Cleanup: stray `package-lock.json`; `text_config.json` not in `.gitignore`; debug prints in `blink.py`; `run_demos.sh` duplicates `bin/led-demos` with a hardcoded venv path.
