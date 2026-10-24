# Known Issues

Findings from a code and docs review (2026-10-24). Static review only, not verified on hardware.

## Bugs

- [x] **#1 Brightness does nothing.** `DaemonController.apply_brightness` (`demos.py:409`) is never called and `matrix.brightness` is never set. The `brightness` command, web slider, and playlist `params.brightness` are all no-ops.
  - Fixed: `matrix.brightness` is set at init, per effect (playlist override or global), and live by the `brightness` command; the text effect copies it to its canvas and redraws static text on change. Needs a hardware check (20 / 100 / 0 on fireworks and static text).
- [ ] **#2 Global speed does nothing.** `if 'speed' not in opts` (`demos.py:465`, `:1313`) is always false for effects with a `speed` option because defaults are already merged in; effects without one swallow it in `**kwargs`. Per-effect `speed` options also mean different things (comet 0.15, starfield 0.02, spiral 5), so a global multiplier can't simply be passed through.
- [ ] **#3 One effect exception kills the display.** The `try` at `demos.py:425` wraps the whole loop; the worker exits but `effects_running` stays True, so `on` says "already running". Trigger: enter `42` or `3.14` as text in the web UI — `opt` parsing (`demos.py:672-680`) makes it a number, `text.split()` crashes, and the value is persisted to `text_config.json`.
- [ ] **#4 Startup IP display overwrites saved text config.** `run_effect` injects `config_saver` for `text` (`demos.py:326`) and `text_display` saves every non-None arg (`effects/text.py:62-80`). Daemon also passes option defaults explicitly, so saved font/speed/hue are never used.
- [ ] **#5 Daemon ignores playlist per-effect settings at startup.** `effect_durations`/`effect_params` built in `__main__` (`demos.py:1194-1207`) are never passed to `DaemonController`; `current_playlist_name` stays None.
- [ ] **#6 `set <effect>` permanently sets global duration to 0** (`demos.py:559`, `:566`). After next/prev/playlist, every effect runs forever.
- [ ] **#7 Empty playlist busy-loops at 100% CPU** (`demos.py:426-439`). The web UI can create and load an empty playlist.
- [ ] **#8 `stop` doesn't stop the daemon.** Code treats `stop` as `off` (`demos.py:575`); docs say it shuts down daemon + web server. Nothing sets `running = False` in a detached daemon, and there's no SIGTERM handler, so the matrix isn't cleared and the socket isn't removed (including on `systemctl stop`).
- [ ] **#9 Starting a second daemon clobbers the first's PID file** (`demos.py:903`) before checking whether one is running.

## Security

Web server runs as root on `0.0.0.0:80` with no auth.

- [ ] **#10 Path traversal in playlist names.** `POST /api/playlist` takes `name` from the JSON body; `get_playlist_path` (`playlist_manager.py:28`) joins it unchecked, so `../../etc/foo` writes `/etc/foo.json` as root. Socket `load_playlist` has the same read-side issue. Validate names against `^[A-Za-z0-9_-]+$`.
- [ ] **#11 Unescaped values in web UI HTML** (`static/script.js:471`, `value="${option.default}"`). Text containing `"` breaks the input; stored XSS.
- [ ] **#12 Socket permissions (unverified).** Root-created socket with umask 022 likely rejects non-root `bin/led-control`, though docs show it run without sudo.
- [ ] **#13 No access control** on the web UI. Consider basic auth or binding to a specific interface.

## Smaller code issues

- [ ] **#14** Built-in playlists are regenerated every start (`playlist_manager.py:306`): web UI edits to them are lost, tracked JSON files get dirtied with new timestamps each run, and duration 8 is hardcoded instead of read from `settings.toml`.
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
- [ ] **#26** `stop` described as shutting down the daemon in CLAUDE.md, README (lines 193, 250, 255), and `led-control` help (see #8).
- [ ] **#27** `requirements.txt` doesn't say `rgbmatrix` must be built from rpi-rgb-led-matrix; `werkzeug` is redundant; Pillow is only used by `blink.py`.
- [ ] **#28** Cleanup: stray `package-lock.json`; `text_config.json` not in `.gitignore`; debug prints in `blink.py`; `run_demos.sh` duplicates `bin/led-demos` with a hardcoded venv path.
