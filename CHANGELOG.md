# Changelog

## 2026.10.01

### Renamed from archlinux-logout-gtk4

**What Changed.** The logout app's package and repo names carried a GTK version suffix that says nothing to users. Everything it installs was already named `archlinux-logout`, so only the package name and the references to it change. The source repo moved to `~/KIRO/archlinux-logout` and GitHub `kirodubes/archlinux-logout`.

**Technical Details.** Remote URL repointed. No code change: `/usr/bin/archlinux-logout`, `/usr/share/archlinux-logout/` and `/etc/archlinux-logout.conf` already had the neutral name.

**Files Modified.**
- `README.md` (install command, tree)
- `CLAUDE.md`

## 2026.09.28

### Miracle logout detection removed

**What Changed.** Removed the `miracle-wm` branch from the logout-command detection. Miracle has been
dropped from Kiro: `mir` broke on the boost 1.92 soname bump and can no longer be rebuilt (its `wlcs`
build dependency is gone), so `miracle-wm-git`, `mir` and `kiro-miracle` left nemesis_repo and ATT.

**Technical Details.** A leftover Miracle session now falls through to the generic handler, like any
other desktop logout doesn't know about.

**Files Modified.**
- `usr/share/archlinux-logout/Functions.py`

### Pin ruff to the classic rule set

**What Changed.** Added `ruff.toml` (same as ATT's). ruff 0.16 widened its implicit rule set, so the
global pre-commit hook began failing `up.sh` on untouched code (BLE001, PLW1510, I001...).

**Technical Details.** `select = ["E4", "E7", "E9", "F"]`, `line-length = 120`, `E402` ignored for
`gi.require_version()`. No code changes needed; `ruff check .` passes.

**Files Modified.**
- `ruff.toml` (new)

## 2026.07.18

### herbstluftwm (kiro-hlwm) logout detection

**What Changed.** Added a `herbstluftwm` pgrep fallback to `_detect_desktop()` so the
new **kiro-hlwm** edition is detected even when `DESKTOP_SESSION` is empty (parity with
the existing `ohmychadwm`/`chadwm`/`dusk` fallbacks). The `_get_logout()` branch for
`herbstluftwm` already existed, returning **`herbstclient quit`** — herbstluftwm's own
clean session exit (no `pkill` needed). Part of standing up kiro-hlwm via
`/kiro-create-x11-twm`.

**Technical Details.** `Functions.py::_detect_desktop()` — new `elif pgrep -x
herbstluftwm` sets `desktop = "herbstluftwm"` in the `desktop == "unknown"` block.
py_compile + ruff clean.

## 2026.07.09

### kiro-hyprland-dms logout entry

**What Changed.** Added a `_get_logout()` branch for the new **`kiro-hyprland-dms`** edition
(Hyprland + DankMaterialShell). Its session sets `DESKTOP_SESSION=kiro-hyprland-dms`, which had no
branch, so logout fell through to the generic `pkill kiro-hyprland-dms` fallback — no such process,
so logout silently did nothing (same gap `kiro-niri-dms` and `kiro-hyprland-noctalia` hit). The new
branch runs `dms kill 2>/dev/null; pkill -x dms` first (DMS's own teardown, in case it re-parents to
`systemd --user` as it does on niri rather than dying as a Hyprland child), then the same
uwsm-aware / Lua-aware Hyprland exit as the primary branch (`uwsm stop` when uwsm-managed, else
`hyprctl dispatch 'hl.dsp.exit()'` on 0.55+ Lua configs). Never `pkill` the compositor — it breaks
uwsm's ordered shutdown.

**Not yet boot-verified** (Wayland-GPU editions black-screen in VirtualBox) — confirm the DMS
teardown on a QEMU virtio-gpu / metal boot at ISO time; the `dms kill` is a harmless no-op if DMS
already dies with Hyprland.

### Files Modified
- `usr/share/archlinux-logout/Functions.py`

## 2026.07.05

### scroll + miracle-wm logout entries

**What Changed.** Added two `_get_logout()` branches. **scroll** (the new `kiro-scroll` edition,
`sway-scroll` package — a fork of sway) was falling through to the generic `pkill scroll`, which
kills the compositor but leaves the Kiro waybar stack (waybar/mako/hypridle/nm-applet/variety)
lingering → an unclean logout. Added an explicit branch mirroring `sway`:
`_waybar_stack + "pkill scroll"`. **miracle-wm** (package `miracle-wm-git`; Erik sometimes calls it
"magic-wm") got an explicit `pkill miracle-wm` branch — Mir-based, not a Kiro waybar edition, so no
stack; SIGTERM shuts Mir down cleanly.

**Verified** live on the riker test box (`DESKTOP_SESSION=scroll`): the installed copy was patched
and `_get_logout()` dry-called → `scroll` returns the waybar-stack + `pkill scroll` exit, `sway`
unchanged.

### Files Modified
- `usr/share/archlinux-logout/Functions.py`

## 2026.07.04

### niri-dms + hyprland-noctalia logout: add new editions + fix the renamed noctalia session

**What Changed.** The new `kiro-niri-dms` edition (niri + DankMaterialShell) could not log out at
all — Super+X did nothing. Found live on picard: the session identity is
`DESKTOP_SESSION=kiro-niri-dms`, but `_get_logout()` had no branch for it, so it fell through to the
generic `pkill kiro-niri-dms`, which matches no process (the compositor is `niri`, the shell is
`dms`/`qs`). Added an explicit branch. Also fixed the noctalia edition, whose session file was
renamed `kiro-niri.desktop` → `kiro-niri-noctalia.desktop` — its `kiro-niri` branch no longer
matched, so noctalia logout had regressed into the same no-op.

**Technical Details.**
- New `kiro-niri-dms` branch: `dms kill 2>/dev/null; pkill -x dms; pkill -x variety; niri msg action quit -s`.
  On this edition `dms` (the shell backend), its `qs` quickshell child, and `variety` are spawned as
  loose siblings under `systemd --user` (ppid = the user manager, **not** niri), so quitting the
  compositor alone would orphan them. `dms kill` is DankMaterialShell's own CLI to tear the shell
  (and its `qs`) down cleanly; `variety` is killed explicitly; then niri clean-quits.
- noctalia branch now matches `kiro-niri-noctalia` (new session id) with `kiro-niri` kept as an
  alias for pre-rename installs. Kill strategy unchanged (noctalia is a niri child, dies with the
  clean quit).
- **Verified live on picard.** After running the command the session tore down to the SDDM greeter
  with zero leftovers — no `niri`, `dms`, `qs`, `variety`, or `xdg-desktop-portal` processes
  remaining. (`niri msg action quit -s` prints a harmless socket-EOF as niri exits mid-reply; the
  quit succeeds.)
- New `kiro-hyprland-noctalia` edition (Hyprland + noctalia): `DESKTOP_SESSION=kiro-hyprland-noctalia`
  didn't match the `hyprland` branch and fell through to the same no-op. Added the session id (+ path
  form) to the Hyprland branch, so it gets the clean compositor exit (`hyprctl dispatch 'hl.dsp.exit()'`
  on 0.55+ Lua configs, else `hyprctl dispatch exit`; `uwsm stop` when uwsm-managed). noctalia is a
  Hyprland child, so the clean exit takes it down — no pre-kill needed.

**Files Modified.**
- `usr/share/archlinux-logout/Functions.py`

## 2026.07.03

### niri logout: quit the compositor cleanly instead of `pkill niri`

**What Changed.** Logging out of a niri session (both editions) needed the logout fired **twice**.
Found live on picard: niri runs as a **systemd user service** (`niri.service`, Type=notify), and
`niri-session` ends a session by force-stopping `graphical-session.target`. `_get_logout()`'s niri
branch used `pkill niri`, which hard-kills the compositor process out from under systemd — the shell
it had already killed (noctalia / the waybar stack) stayed dead while `niri --session` lingered,
leaving a bar-less half-session that only cleared on a second logout. Now both branches end the
session with niri's own `niri msg action quit -s` (`-s` skips the confirmation prompt), which stops
`graphical-session.target` and takes the spawned shell down with it — one press.

**Technical Details.**
- `_get_logout()` niri branch: `pkill niri` → `niri msg action quit -s`. The noctalia path does not
  pkill the shell first (it's a child of niri and dies with the clean quit); the ohmyniri path still
  pre-kills its loose `waybar/mako/hypridle/nm-applet/swayidle/variety` daemons as a guard, then
  clean-quits niri.
- **Distinguish the two niri editions by session name, not a runtime probe.** kiro-niri /
  kiro-ohmyniri now ship their own session entries (`kiro-niri.desktop` / `kiro-ohmyniri.desktop`), so
  `DESKTOP_SESSION` is `kiro-niri` / `kiro-ohmyniri` — added explicit dispatch branches for each. The
  old `pgrep -f 'qs -c noctalia-shell'` probe is kept only as the fallback for the plain upstream
  `niri` session (no Kiro session entry).
- Verified `niri msg action quit -s` exists on niri 26.04.

**Files Modified.**
- `usr/share/archlinux-logout/Functions.py`
- `../KIRO-PKG-BUILD-APPS/archlinux-logout-gtk4/PKGBUILD` (pkgrel 06 → 07)

## 2026.07.01

### Distinguish kiro-ohmyniri from kiro-niri for logout/lock (both share XDG_CURRENT_DESKTOP="niri")

**What Changed.** `kiro-ohmyniri` (new niri edition with kiro-hyprland's waybar/mako/swayidle/
variety shell) shipped with the exact same `XDG_CURRENT_DESKTOP="niri"` as `kiro-niri`
(noctalia-shell) — found live on picard when its logout button ran kiro-niri's noctalia-kill
command instead, leaving ohmyniri's actual companion daemons (waybar/mako/swayidle/variety)
orphaned. An `XDG_CURRENT_DESKTOP="niri:ohmyniri"` fix was tried first but doesn't work:
`_detect_desktop()` truncates at the first colon (`desktop.split(":")[0]`), so it collapses
straight back to `"niri"` before ever reaching the dispatch table.

**Technical Details.**
- `_get_logout()`'s niri branch now probes at runtime (`pgrep -f 'qs -c noctalia-shell'`) to
  tell the two editions apart instead of trusting the desktop string alone. noctalia running →
  kiro-niri's existing command; otherwise → `_waybar_stack + "pkill swayidle; pkill variety;
  pkill niri"` for kiro-ohmyniri.
- Added `gtklock` to `_WAYLAND_LOCKERS` (kiro-ohmyniri's locker — niri is Smithay-based, not
  wlroots, so hyprlock is unverified there). `resolve_lock_cmd`'s `shutil.which` preference-order
  scan already handles picking the right one per-machine; no per-edition branching needed.

**Files Modified.**
- `usr/share/archlinux-logout/Functions.py`

### Kill the full companion-daemon stack before exiting waybar-based Wayland TWMs; add labwc/mango/dwl logout support; fix niri's bar name

**What Changed.** Root-caused on picard (real-metal labwc test box): `archlinux-logout` was
taking 10-14s to render on `Super+X`. Traced through GTK a11y and xdg-desktop-portal red
herrings to the real cause — logging out of sway/river/wayfire/niri only `pkill`ed the
compositor itself, leaving `waybar`, `mako`, `hypridle`, and `nm-applet` running (all
independent top-level processes, not compositor children). Each crash/relogin cycle on picard
stacked a fresh set on top of the orphaned ones — found **6 separate `hypridle` processes**
fighting over the `org.freedesktop.ScreenSaver` D-Bus name, which destabilized the whole
session and was the actual source of the render delay. Also added logout support for three
KIROTUX editions not yet wired: labwc, mango, and dwl.

**Technical Details.**
- `_get_logout()` in `Functions.py`: the waybar-shipping branches (sway/river/wayfire/labwc/
  mango) now `pkill waybar; pkill mako; pkill hypridle; pkill nm-applet;` before the existing
  `pkill <compositor>` — all four companion daemons die first, then the compositor. `;` (not
  `&&`) so a non-running daemon's nonzero exit doesn't block the rest of the chain.
- Added `labwc` and `mango` (both ship the same waybar+mako+hypridle+nm-applet stack per their
  `kiro-labwc`/`kiro-mango` autostart scripts) and `dwl` (ships its own `dwlb` bar — no
  waybar-kill needed) to the desktop-detection table.
- Fixed niri's entry: it doesn't run waybar/mako/hypridle at all — it runs `noctalia-shell`
  (Quickshell, `qs -c noctalia-shell`) per `kiro-niri/etc/skel/.config/niri/cfg/autostart.kdl`.
  `pkill waybar` there was a silent no-op; now `pkill -f 'qs -c noctalia-shell'`.
- Verified live on picard: killed the 6 orphaned `hypridle` instances, deployed the fixed
  `Functions.py`, and confirmed `Super+X` renders immediately afterward.

**Files Modified.**
- `usr/share/archlinux-logout/Functions.py`

## 2026.06.30

### Lock screen now works on Plasma (native KScreenLocker, X11 + Wayland)

**What Changed.** Plasma lock was unreliable: on Wayland `resolve_lock_cmd` swapped the X11
locker for `hyprlock` (not installed on a stock Plasma box, so it fell back to betterlockscreen
which can't run on Wayland); on X11 it relied on betterlockscreen/i3lock-color actually being
installed, which isn't guaranteed on a Plasma box. Plasma now routes to the native KDE locker
via `loginctl lock-session` on **both** session types — always present on a Plasma install,
zero extra dependencies.

**Technical Details.**
- `Functions.py`: added module-level `session_kde` detection from `XDG_CURRENT_DESKTOP`
  (matches `kde`/`plasma`).
- `resolve_lock_cmd` reordered: the configured-locker check runs first (custom lockers pass
  through verbatim); then Plasma/KDE returns `loginctl lock-session` regardless of X11/Wayland;
  then the `sessionw` guard and `_WAYLAND_LOCKERS` (`hyprlock`) path handle other Wayland
  compositors. X11 non-Plasma sessions keep betterlockscreen unchanged.
- DE-agnostic and dependency-free — no hyprlock pull onto Plasma, no blur-cache pipeline needed.

**Tradeoff.** Plasma X11 users who had betterlockscreen now get the standard KScreenLocker
instead of its blurred-image lock — intentional, since Plasma ships its own locker and
betterlockscreen is not a guaranteed dependency there.

**Files Modified.**
- `usr/share/archlinux-logout/Functions.py`

## 2026.06.29

### Lock screen now works on Wayland / Hyprland

**What Changed.** The Lock action used `betterlockscreen -l` (i3lock-color), which is X11-only
and silently failed under a Wayland session (Hyprland). Locking now transparently falls back to
a Wayland locker (`hyprlock`) when running on Wayland, while X11 editions keep betterlockscreen
unchanged.

**Technical Details.**
- New `Functions.py::resolve_lock_cmd(cmd_lock)` — if `XDG_SESSION_TYPE == wayland` and the
  configured locker is X11-only (`betterlockscreen`/`i3lock`), it returns the first available
  Wayland locker (currently `hyprlock`; list `_WAYLAND_LOCKERS` is the single place to extend
  to swaylock/gtklock). Otherwise the configured command passes through verbatim.
- Routed **both** lock exec sites through the resolver: `archlinux-logout.py` lock else-branch
  and `Functions.py::cache_bl` (`os.system`). The betterlockscreen image-cache priming branch
  is intentionally kept on Wayland — `betterlockscreen -u` is pure ImageMagick and the blurred
  PNGs it writes to `~/.cache/betterlockscreen/current/` are exactly what hyprlock displays as
  its background.
- The shipped `/etc/archlinux-logout.conf` keeps `lock=betterlockscreen …` — the same package
  serves X11 (chadwm) and Wayland editions, so the swap is runtime session-detection only, not
  a config change.

**Files Modified.**
- `usr/share/archlinux-logout/Functions.py`
- `usr/share/archlinux-logout/archlinux-logout.py`

### Added to the new "Kiro Apps" menu
- Appended `X-Kiro-Apps;` to `archlinux-logout-settings.desktop` and
  `archlinux-betterlockscreen.desktop` (in `usr/share/applications/`) so both appear in
  the new Kiro Apps launcher folder. Non-destructive — still show under Settings/System.

### Settings window matured into a real standalone app

**What Changed.** The standalone `archlinux-logout --settings` window was reworked from a
popover-panel-in-a-window into a proper desktop app, matching the Alacritty Tweak Tool and
Fish Tweak Tool chrome:

- A real **`Gtk.HeaderBar`** title bar with window controls (minimise/maximise/close).
- The in-content header row now uses the shared Kiro pattern — a `#title` label on the left,
  a styled pink **♥ Support** button (`.support-button`), and a **Quit** button on the right.
- Settings are grouped into titled **cards** (Appearance / Buttons / Theme) instead of one
  flat grid.
- A bottom action bar, pinned outside the scroll area, holds **Open BetterLockScreen**
  (launches the `archlinux-betterlockscreen` companion) and **Save Settings** at the
  bottom-right.

The on-screen logout popover is unchanged — it still uses the compact flat panel.

**Technical Details.**
- `usr/share/archlinux-logout/GUI.py`: `SettingsPanel` now branches cleanly — the popover
  path keeps the flat grid (with Save inside); the `settings_only` path builds the
  header row, three `_settings_card()` titled frames, and the about body. The shared widgets
  (`buttons_grid`, `self.themes`) are constructed once and only parented in the branch that
  uses them (fixes a double-parent `gtk_box_append` assertion). Save button is stashed on
  `self.btn_save_settings` so the window can place it in the bottom bar. The header replaces
  the old inline-markup heart with a CSS-classed `♥ Support` button.
- `usr/share/archlinux-logout/archlinux-logout.py`: `_build_settings_window` sets a
  `Gtk.HeaderBar` titlebar, loads inline CSS (`_load_settings_css`: `#title`, `.info-label`,
  `.support-button`), and lays out `[scroller | separator | action bar]`. New
  `on_betterlockscreen_clicked` launches the companion via `Popen` in a daemon thread.
  Also added a `set_size_request(480, 500)` floor so the resizable window can't be dragged
  smaller than its content (buttons were clipping when shrunk).

**Files Modified.**
- `usr/share/archlinux-logout/GUI.py`
- `usr/share/archlinux-logout/archlinux-logout.py`

### BetterLockScreen companion gained the same top bars

**What Changed.** The `archlinux-betterlockscreen` GUI now carries the same two top bars as
Fish Tweak Tool / the logout settings window — it previously had neither:

- A real **`Gtk.HeaderBar`** title bar with window controls (minimise/maximise/close).
- An in-content **header row** above the body — a `#blstitle` label on the left, a
  `betterlockscreen v<version>` label, a pink **♥ Support** button (`.support-button`,
  opens the existing Credits/Support dialog), and a **Quit** button — followed by a separator.

The existing bottom **Credits** button is left in place (it opens the same Support dialog).

**Technical Details.**
- `usr/share/archlinux-betterlockscreen/archlinux-betterlockscreen.py`: added `_build_headerbar()`
  (plain `Gtk.HeaderBar` titlebar with `show_title_buttons`), called from `__init__`.
- `usr/share/archlinux-betterlockscreen/GUI.py`: new `hbox_header` content header packed at the
  top of `vbox` (with a separator); the inline CSS provider now also defines `#blstitle`,
  `.info-label`, and `.support-button`. **♥ Support** reuses `on_support_clicked`; **Quit**
  calls the window's `close` handler (which clears the lock file and quits).
- `usr/share/archlinux-betterlockscreen/Functions.py`: new `get_betterlockscreen_version()` —
  parses `VERSION=` out of the `betterlockscreen` script (display-free; `--version` would
  shell out to `xset` and need an X display).

**Files Modified.**
- `usr/share/archlinux-betterlockscreen/archlinux-betterlockscreen.py`
- `usr/share/archlinux-betterlockscreen/GUI.py`
- `usr/share/archlinux-betterlockscreen/Functions.py`

## 2026.06.27

### Settings window: header toolbar + "what this app does" body

**What Changed.** The standalone Settings window now opens with a toolbar at the top —
title **ArchLinux Logout Settings**, a pink **♥ Support** button (opens a Support-Kiro
dialog with the funding channels), and a **Quit** button — matching the other Kiro tweak
tools. Below the settings, a descriptive body explains what the app is (the logout power
screen) and what each control changes (opacity, icon/font size, show-text, which buttons,
theme). Both only appear in the standalone settings window, not the on-screen popover.

**Technical Details.**
- `usr/share/archlinux-logout/GUI.py`: added `_FUNDING`, `_open_url`, `_show_support_dialog`,
  and — inside `SettingsPanel`, gated on `settings_only` — the header toolbar (top) and the
  about body (bottom). The pink heart uses inline Pango markup (`#e0567a`) so no CSS file is
  needed.
- `usr/share/archlinux-logout/archlinux-logout.py`: `_build_settings_window` now wraps the
  panel in a `Gtk.ScrolledWindow`, makes the window resizable, and enlarges the default size
  (460×760) so the added header + body never clip.

## 2026.06.23

### What Changed
- **Fixed the Hyprland branch** in `Functions.py::_get_logout()`. The old branch only matched the
  legacy session name `hypr` (under the X11 `xsessions` path) and ran **`pkill Hypr`** — a hard kill.
  A modern Hyprland session reports `hyprland` (Wayland), so it didn't match and fell through to the
  generic `pkill` fallback; `pkill` also breaks uwsm's ordered shutdown.
- **Fixed Hyprland 0.55+ Lua-config logout.** After the above fix, logout still failed on the KIROTUX
  Hyprland edition: `hyprctl dispatch exit` errored with `hl.dispatch: expected a dispatcher`. Hyprland
  0.55 switched to a **Lua config**, where `hyprctl dispatch <X>` is evaluated as Lua `hl.dispatch(X)`,
  so the bare `exit` identifier is rejected. The branch now version-detects and emits the Lua dispatcher
  **`hyprctl dispatch 'hl.dsp.exit()'`** on 0.55+, keeping legacy `hyprctl dispatch exit` for older Hyprland.

### Technical Details
- New branch matches `hyprland` / `hypr` / the `wayland-sessions/hyprland` path and returns the
  **graceful** command: **`uwsm stop`** when the session is uwsm-managed (detected with a
  `systemctl --user is-active` check on the uwsm-created Hyprland wayland-wm unit), otherwise
  **`hyprctl dispatch exit`**. Never `pkill` — per the Hyprland wiki, killing the compositor skips
  uwsm's ordered shutdown.
- New helper `_hyprland_lua_config()` parses `hyprctl version` and returns `True` for major.minor
  `>= 0.55` (regex on the first `X.Y.Z` token, robust across the `Hyprland X.Y.Z built…` and `Tag: vX.Y.Z`
  output formats). The non-uwsm exit then branches on it: `hl.dsp.exit()` for Lua, bare `exit` for legacy.
- **Removed the dead duplicate Hyprland branch** further down the wayland section. Its `hyprland` /
  `wayland-sessions/hyprland` entries were unreachable (caught by the primary branch above), and its
  `hyprland-uwsm` entries wrongly returned `hyprctl dispatch exit`. Folded the `hyprland-uwsm` /
  `wayland-sessions/hyprland-uwsm` names into the single primary branch so all Hyprland variants share
  the uwsm-aware + Lua-aware logic.
- flake8 + ruff clean (max line length 120).

## 2026.06.21

### What Changed
- Added a **Plasma / KDE branch** to `Functions.py::_get_logout()`. Plasma was unhandled, so logout fell
  through to the generic `pkill <name>` fallback and ran **`pkill plasma`** — which only kills
  `plasmashell`. On Plasma 6 Wayland the compositor (`kwin_wayland`) and the rest of
  `graphical-session.target` kept running, holding **DRM-master**, so the next login could not drive the
  GPU and landed on a **black screen** (recoverable only by reboot).

### Technical Details
- New branch matches `plasma` / `plasmawayland` / `plasmax11` / `kde` (and the session-file paths) and
  returns `qdbus6 org.kde.Shutdown /Shutdown org.kde.Shutdown.logout` — Plasma 6's native logout, which
  works on both X11 and Wayland and stops `graphical-session.target` cleanly so `kwin_wayland` releases
  DRM-master.
- Diagnosed live on a Plasma box: after `pkill plasma`, `kwin_wayland` still held `/dev/dri/card1` and
  the new session logged `atomic commit failed: Permission denied`. The Kiro `systemd-logind` drop-in was
  ruled out (failure reproduced without it).
- flake8 + ruff clean (max line length 120).

## 2026.06.16

### What Changed
- Ported the ArchLinux Tweak Tool startup UTF-8 guard into **both** binaries — `archlinux-logout` and
  `archlinux-betterlockscreen` — so neither crashes on a non-UTF-8 system locale (latin-1 `fr_BE`,
  etc.). On a UTF-8 locale (incl. `fr_FR.UTF-8`/`it_IT.UTF-8`/`es_ES.UTF-8`) the guard is inert; the
  apps were already robust there. Part of the ecosystem-wide UTF-8 robustness audit of all Kiro GTK4
  apps.

### Technical Details
- `archlinux-logout.py` + `archlinux-betterlockscreen.py`: two blocks at the top of each entry point.
  (1) Re-exec with `-X utf8` + `PYTHONUTF8=1` only when `codecs.lookup(sys.getfilesystemencoding()).name
  != "utf-8"` — forces UTF-8 for stdout, `text=True` subprocess decoding and `open()` regardless of
  `LANG`; loop-safe. (2) When the current locale is not UTF-8, fall back to `C.UTF-8` so spawned child
  output stays readable. `codecs`/`os`/`sys` imports deduplicated into the guard; later imports carry
  `# noqa: E402`.
- The fullscreen-overlay (`archlinux-logout`) was given extra scrutiny since re-exec interacts with its
  monitor grab — re-exec happens before any GTK work, so the relaunched process builds the overlay
  cleanly. ruff + `py_compile` clean on both; re-exec verified under `nl_BE.iso88591`.

### Files Modified
- usr/share/archlinux-logout/archlinux-logout.py
- usr/share/archlinux-betterlockscreen/archlinux-betterlockscreen.py
- CHANGELOG.md

## 2026.05.31

### What Changed
- Added a standalone **settings mode** so ArchLinux Logout can be configured from the XFCE Settings Manager without launching the fullscreen power overlay. New `archlinux-logout --settings` opens just the configuration panel in a small decorated window; ships a new `.desktop` entry ("ArchLinux Logout Settings") with XFCE Settings categories.
- Added an **Exit** button to the standalone settings window (not shown in the overlay popover, which already has Cancel).
- Fixed a latent infinite-recursion bug in the save path (`_after_save` calling itself) that a global replace had introduced — would have broken Save in the overlay popover too.
- **archlinux-betterlockscreen**: replaced the `panel.png` image-as-background behind the in-app notification ("Lockscreen set successfully") with a CSS-styled bar, matching the fix already shipped in ArchLinux Tweak Tool. The notification no longer renders a stretched bitmap behind the text.

### Technical Details
- `GUI.py`: extracted the settings widget tree out of the overlay popover into a shared `SettingsPanel(self, Gtk, fn)` builder, used by both the popover (overlay mode) and the new settings window.
- `archlinux-logout.py`: `TransparentWindow.__init__` takes `settings_only`; in that mode it builds a small decorated window via `_build_settings_window()` and returns early — skipping fullscreen, monitor detection, background CSS, and async pixbuf loading. The power keybinds are **not** wired in settings mode so pressing "S"/"R"/etc. can't trigger a real action.
- The `--settings` branch sits at the `__main__` lock-file guard and bypasses the singleton entirely (never creates `/tmp/archlinux-logout.lock`), so it opens even while the overlay is up or after a stale-lock crash. Flag is parsed from `sys.argv` directly (not via GApplication) and the app runs with `app.run(None)`.
- `on_save_clicked` now calls `_after_save()`, which pops down the popover in overlay mode or closes the window in settings mode.
- Launcher `usr/bin/archlinux-logout` now forwards `"$@"`.

### Files Modified
- usr/share/archlinux-logout/GUI.py
- usr/share/archlinux-logout/archlinux-logout.py
- usr/bin/archlinux-logout
- usr/share/applications/archlinux-logout-settings.desktop (created)
- usr/share/archlinux-betterlockscreen/GUI.py
- CHANGELOG.md

## 2026.05.21

### What Changed
- Added the four other required markdown scaffold files (created stubs for whichever of `IDEAS.md` / `TODO.md` / `CLAUDE.md` were missing) per the new ecosystem MD-scaffold rule codified in [Kiro-HQ/CLAUDE.md](/home/erik/Insync/Kiro/Kiro-HQ/CLAUDE.md#required-markdown-scaffold-every-repo). README was already substantial; left untouched.

### Files Modified
- CHANGELOG.md
- IDEAS.md (created where missing)
- TODO.md (created where missing)
- CLAUDE.md (created where missing)

## 2026.05.03

**What Changed**
Full code quality and GTK4 correctness pass across both apps. Added session-agnostic pkill fallback, fixed GTK3 deprecated API usage, corrected signal handler signatures, fixed GLib timeout double-remove bug, and enforced project coding rules throughout.

**Technical Details**
- `_get_logout()` pkill fallback: if no named DE matches, extracts bare name from `DESKTOP_SESSION`/`XDG_CURRENT_DESKTOP` and returns `"pkill <name>"` — makes logout work on any unrecognised WM
- `__exec_cmd` now spawns `subprocess.Popen` in a daemon thread instead of blocking `os.system()` call
- `subprocess.call()` in `archlinux-betterlockscreen.py::set_lockscreen` replaced with `Popen().wait()`
- All `Gtk.Image` + `set_from_pixbuf()` (GTK3 deprecated) replaced with `Gtk.Picture` + `set_paintable(Gdk.Texture.new_for_pixbuf())` across betterlockscreen GUI.py, Support.py, Splash.py
- `btnsearch`/`btndefault` `.connect("clicked", handler, self.fb)` fixed — GTK4 `clicked` only emits the widget; extra `self.fb` arg was silently dropped at runtime causing `fb` param to always be `None`
- Dead `fb` parameter removed from `on_load_clicked` and `on_default_clicked`
- `timeOut()` now returns `False` to signal one-shot; `close_in_app_notification()` no longer calls `GLib.source_remove()` (double-remove caused GLib warning)
- Unused `subprocess`, `threading` imports removed from betterlockscreen `Functions.py`
- Unused `os` import removed from betterlockscreen `GUI.py`
- All unused callback `widget` params renamed to `_widget` across both apps per GTK4 convention
- `Gtk.AlertDialog` (GTK 4.10+) confirmed safe — Arch Linux ships GTK 4.16+, no version guard needed

**Files Modified**
- `usr/share/archlinux-logout/Functions.py`
- `usr/share/archlinux-logout/archlinux-logout.py`
- `usr/share/archlinux-betterlockscreen/archlinux-betterlockscreen.py`
- `usr/share/archlinux-betterlockscreen/GUI.py`
- `usr/share/archlinux-betterlockscreen/Support.py`
- `usr/share/archlinux-betterlockscreen/Splash.py`
- `usr/share/archlinux-betterlockscreen/Functions.py`

---

## 2026.04.16

**What Changed**
README fully rewritten with comprehensive documentation: installation, dependencies, features, theming, keyboard shortcuts, session support (X11/Wayland), troubleshooting, and links to video tutorials.

**Technical Details**
Content-only change; no code modified.

**Files Modified**
- `README.md`

---

## 2026.04.14

**What Changed**
Added the `neocandy` theme.

**Technical Details**
Full set of 14 SVGs (7 actions × normal + blur variant) plus `theme.css` added under `usr/share/archlinux-logout-themes/themes/neocandy/`.

**Files Modified**
- `usr/share/archlinux-logout-themes/themes/neocandy/` (15 new files)

---

## 2026.04.13

**What Changed**
Settings popover gained per-button visibility checkboxes. Removed monitor-geometry-based auto-scaling of icon sizes in favour of fixed defaults.

**Technical Details**
- Added a `Gtk.Grid` of `Gtk.CheckButton` widgets (one per action: cancel, shutdown, restart, suspend, hibernate, lock, logout) to the settings popover.
- Save action now serialises the checkbox state back to `buttons=` in the config file.
- Removed `_set_scaled_icon_sizes()` which computed sizes from monitor resolution; defaults set to 80px main / 32px aux.

**Files Modified**
- `usr/share/archlinux-logout/GUI.py`
- `usr/share/archlinux-logout/archlinux-logout.py`

---

## 2026.04.09

**What Changed**
Minor config default update and session-detection fix in the main window.

**Technical Details**
Config default value adjusted; 7 lines changed in the main window (likely Wayland/X11 session detection path).

**Files Modified**
- `etc/archlinux-logout.conf`
- `usr/share/archlinux-logout/archlinux-logout.py`

---

## 2026.04.08

**What Changed**
Refinements to DE detection logic and monitor handling.

**Technical Details**
- `Functions.py`: cleaned up redundant DE detection code.
- `archlinux-logout.py`: improved multi-monitor detection path.
- Minor GUI/main fixes.

**Files Modified**
- `usr/share/archlinux-logout/Functions.py`
- `usr/share/archlinux-logout/GUI.py`
- `usr/share/archlinux-logout/archlinux-logout.py`

---

## 2026.04.06

**What Changed**
Initial project commit and extensive iterative development in a single day. Established the full application architecture: GTK4 logout overlay + betterlockscreen companion app.

**Technical Details**
- `_get_logout()` split into `_detect_desktop()` (env var + process-based detection) and a command-lookup function; added `pgrep`-based fallback for ohmychadwm/chadwm.
- GUI refactored around a `make_card()` factory: each button is a `Gtk.Box` card that owns its own `GestureClick` and `EventControllerMotion` controllers, replacing an earlier approach where gesture targets were separate from the visual widget.
- Icon loading moved to a background thread (`threading.Thread`) with `GLib.idle_add(_build_gui)` so the dark overlay appears immediately while SVGs load asynchronously.
- `set_widget_pixbuf()` helper added to handle GTK4 `Gdk.Texture`/pixbuf API differences.
- `GUI.py` reduced to a pure UI builder (no logic); all state and signal handling stays in `TransparentWindow`.
- betterlockscreen companion app restructured with the same three-file split.

**Files Modified**
- `usr/share/archlinux-logout/archlinux-logout.py`
- `usr/share/archlinux-logout/GUI.py`
- `usr/share/archlinux-logout/Functions.py`
- `usr/share/archlinux-betterlockscreen/archlinux-betterlockscreen.py`
- `usr/share/archlinux-betterlockscreen/Functions.py`
- `usr/share/archlinux-betterlockscreen/GUI.py`
- `usr/share/archlinux-betterlockscreen/Splash.py`
- `usr/share/archlinux-betterlockscreen/Support.py`
- `etc/archlinux-logout.conf`
- `README.md`
