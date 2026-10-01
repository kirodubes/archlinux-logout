# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A GTK4-based fullscreen power management overlay for Arch Linux. Provides shutdown, restart, suspend, hibernate, lock, and logout via themed SVG buttons on a transparent fullscreen window. Ships as `archlinux-logout` in the `nemesis_repo` package repo.

## Running

```bash
python3 usr/share/archlinux-logout/archlinux-logout.py
```

Or if installed system-wide:

```bash
archlinux-logout
```

## Linting

```bash
flake8 usr/share/archlinux-logout/
flake8 usr/share/archlinux-betterlockscreen/
```

Max line length is 120. Always run flake8 before considering any Python change done.

## Architecture

The main app lives in [usr/share/archlinux-logout/](usr/share/archlinux-logout/) across three files with strict separation of concerns:

- [archlinux-logout.py](usr/share/archlinux-logout/archlinux-logout.py) — `TransparentWindow` (GTK4 `ApplicationWindow` subclass). Owns the app lifecycle, keyboard shortcuts, monitor detection, and all power action handlers. Reads config, wires signals, handles save-on-change.
- [GUI.py](usr/share/archlinux-logout/GUI.py) — pure UI builder, no logic. Called once to construct the widget tree (overlay, buttons, settings popover). Returns widget references back to the main window.
- [Functions.py](usr/share/archlinux-logout/Functions.py) — utilities: config parsing, icon loading, DE detection, theme enumeration, session type detection, lock file management.

### Config layering

System defaults at `/etc/archlinux-logout.conf`; user overrides at `~/.config/archlinux-logout/archlinux-logout.conf`. Both are INI-format with `[settings]`, `[commands]`, `[binds]`, and `[themes]` sections. The app reads system defaults first, then overlays user config.

### Desktop environment detection

`Functions.py::_detect_desktop()` maps 50+ DEs and WMs (X11 and Wayland) to their correct logout commands. If you add support for a new WM, add it here. The main window checks `DESKTOP_SESSION`, `XDG_CURRENT_DESKTOP`, and running process names to identify the DE.

### Theme system

Themes live in `usr/share/archlinux-logout-themes/themes/<theme-name>/`. Each theme provides SVG icons for all 7 actions (`shutdown.svg`, `restart.svg`, etc.) plus `*_blur.svg` hover-state variants and a `theme.css`. Hover effects show the blur variant after a 2-second delay. Adding a theme means adding a directory with all required SVGs.

### Icon loading

Icons are loaded asynchronously in a background thread (via `threading`) to avoid blocking the GTK main loop. Do not move icon loading back to the main thread.

### Multi-monitor / session detection

On X11, the active monitor is determined via `xdotool getmouselocation` (mouse position). On Wayland, it falls back to the primary monitor. Session type is detected from `$WAYLAND_DISPLAY` / `$XDG_SESSION_TYPE`. The `archlinux-betterlockscreen` companion app handles lock screen caching with blur effects.

### Artix Linux

The main window detects Artix at startup and substitutes `openrc`-compatible power commands in place of `systemctl` equivalents.

## Current State (2026.05.03)

Both apps are clean against project coding rules and GTK4 API correctness:

- All `subprocess.call()` and `os.system()` GUI-callback violations fixed
- All unused callback params named `_widget` / `_flowbox`
- All `Gtk.Image.set_from_pixbuf()` (GTK3 deprecated) replaced with `Gtk.Picture` + `Gdk.Texture.new_for_pixbuf()`
- GTK4 signal handler signatures verified correct throughout
- `_get_logout()` has a session-agnostic `pkill <name>` fallback for unrecognised WMs
- `Gtk.AlertDialog` (GTK 4.10+) is safe — Arch ships GTK 4.16+

## Maybe Todos (performance)

- **Parallelize SVG loading** — replace single background thread in `_load_pixbufs_async` with `ThreadPoolExecutor(max_workers=4)`. Icons fill in ~4x faster; small change, high impact on perceived load time vs GTK3 variant.
- **Pre-cache hover textures** — extend `_load_pixbufs_async` to also load all `*_blur.svg` variants and store as `self._textures[key]`. Then `on_mouse_in`/`on_mouse_out` swap paintables instead of re-decoding SVG from disk on every hover event.
- **Move `xdotool` call after `present()`** — currently `display_on_monitor()` blocks window from appearing while xdotool runs (50–150ms on X11). Restructure so window presents first, then resolves monitor.
- **Remove `from distro import id` at class body level** — runs at import time before `__init__`; move into `__init__` to defer the file I/O.

## Known Non-Issues

- Markdown linter (MD036/MD032) warns on CHANGELOG.md — pre-existing format, intentional
- `dbus-launch` warning at startup when run outside a full desktop session — env issue, not a code bug; solvable via launcher script wrapping with `dbus-run-session` if needed
