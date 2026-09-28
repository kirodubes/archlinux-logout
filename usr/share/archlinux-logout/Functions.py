# =====================================================
#        Authors Brad Heffernan and Erik Dubois
# =====================================================

import subprocess
import os
import re
import shutil
from pathlib import Path
import configparser

envvar = os.environ.get("XDG_SESSION_TYPE", "")
sessionw = False
if envvar == "wayland":
    sessionw = True

# Plasma/KDE Wayland gets the native KScreenLocker via logind rather than hyprlock.
_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
session_kde = "kde" in _desktop or "plasma" in _desktop

home = os.path.expanduser("~")

# X11-only lockers — betterlockscreen wraps i3lock-color, neither runs on Wayland.
_X11_LOCKERS = ("betterlockscreen", "i3lock")
# Wayland lockers, in preference order. hyprlock first (Kiro's Hyprland edition);
# gtklock is kiro-ohmyniri's locker (niri is Smithay-based, not wlroots — hyprlock
# is unverified there). Add swaylock here to extend coverage further.
_WAYLAND_LOCKERS = ("hyprlock", "gtklock")


def resolve_lock_cmd(cmd_lock):
    """Swap an X11-only lock command for the right locker on the current session."""
    first_word = cmd_lock.split(maxsplit=1)[0] if cmd_lock.split() else ""
    if first_word not in _X11_LOCKERS:
        return cmd_lock
    # Plasma (X11 or Wayland): hand off to KScreenLocker via logind — always present
    # on a Plasma install, no dependency on betterlockscreen/i3lock-color.
    if session_kde:
        return "loginctl lock-session"
    if not sessionw:
        return cmd_lock
    # Other Wayland compositors (Hyprland etc.): i3lock/betterlockscreen can't grab
    # the session, so fall back to the first available native Wayland locker.
    for locker in _WAYLAND_LOCKERS:
        if shutil.which(locker):
            return locker
    return cmd_lock

base_dir = os.path.dirname(os.path.realpath(__file__))
working_dir = "".join(
    [str(Path(__file__).parents[2]), "/share/archlinux-logout-themes/"]
)
if os.path.isfile(home + "/.config/archlinux-logout/archlinux-logout.conf"):
    config = home + "/.config/archlinux-logout/archlinux-logout.conf"
else:
    config = "".join([str(Path(__file__).parents[3]), "/etc/archlinux-logout.conf"])
root_config = "".join([str(Path(__file__).parents[3]), "/etc/archlinux-logout.conf"])


def _get_position(lists, value):
    data = [string for string in lists if value in string]
    position = lists.index(data[0])
    return position


def set_widget_pixbuf(widget, pixbuf):
    from gi.repository import Gdk, GLib
    fmt = Gdk.MemoryFormat.R8G8B8A8 if pixbuf.get_has_alpha() else Gdk.MemoryFormat.R8G8B8
    texture = Gdk.MemoryTexture.new(
        pixbuf.get_width(),
        pixbuf.get_height(),
        fmt,
        GLib.Bytes.new(pixbuf.get_pixels()),
        pixbuf.get_rowstride(),
    )
    widget.set_paintable(texture)


def _get_themes():
    y = [x for x in os.listdir(working_dir + "themes")]
    y.sort()
    return y


def cache_bl(self, GLib):
    if os.path.isfile("/usr/bin/betterlockscreen"):
        with subprocess.Popen(
            ["betterlockscreen", "-u", self.wallpaper],
            shell=False,
            stdout=subprocess.PIPE,
        ) as f:
            for line in f.stdout:
                line = str(line)
                line = line.split(maxsplit=1)[1]
                line = line[:-3]
                GLib.idle_add(
                    self.lbl_stat.set_markup,
                    '<span size="x-large"><b>' + line + "</b></span>",
                )

        GLib.idle_add(self.lbl_stat.set_text, "")
        os.unlink("/tmp/archlinux-logout.lock")
        os.system(resolve_lock_cmd(self.cmd_lock))
        from gi.repository import Gtk
        app = Gtk.Application.get_default()
        if app:
            GLib.idle_add(app.quit)
    else:
        print("not installed betterlockscreen.")


def get_config(self, Gdk, Gtk, config):
    try:
        self.parser = configparser.RawConfigParser()
        self.parser.read(config)

        # Set some safe defaults
        self.opacity = 60
        self.show_on_monitor = 0

        if self.parser.has_section("settings"):
            if self.parser.has_option("settings", "opacity"):
                self.opacity = int(self.parser.get("settings", "opacity")) / 100
            if self.parser.has_option("settings", "buttons"):
                self.buttons = self.parser.get("settings", "buttons").split(",")
            if self.parser.has_option("settings", "icon_size"):
                self.icon = int(self.parser.get("settings", "icon_size"))
            if self.parser.has_option("settings", "font_size"):
                self.font = int(self.parser.get("settings", "font_size"))
            if self.parser.has_option("settings", "show_text"):
                self.show_text = self.parser.getboolean("settings", "show_text")
            if self.parser.has_option("settings", "show_on_monitor"):
                self.show_on_monitor = self.parser.get("settings", "show_on_monitor")

        if self.parser.has_section("commands"):
            if self.parser.has_option("commands", "lock"):
                self.cmd_lock = str(self.parser.get("commands", "lock"))
            if self.parser.has_option("commands", "shutdown"):
                self.cmd_shutdown = str(self.parser.get("commands", "shutdown"))
            if self.parser.has_option("commands", "restart"):
                self.cmd_restart = str(self.parser.get("commands", "restart"))
            if self.parser.has_option("commands", "suspend"):
                self.cmd_suspend = str(self.parser.get("commands", "suspend"))
            if self.parser.has_option("commands", "hibernate"):
                self.cmd_hibernate = str(self.parser.get("commands", "hibernate"))

        if self.parser.has_section("binds"):
            if self.parser.has_option("binds", "lock"):
                self.binds["lock"] = self.parser.get("binds", "lock").capitalize()
            if self.parser.has_option("binds", "restart"):
                self.binds["restart"] = self.parser.get("binds", "restart").capitalize()
            if self.parser.has_option("binds", "shutdown"):
                self.binds["shutdown"] = self.parser.get(
                    "binds", "shutdown"
                ).capitalize()
            if self.parser.has_option("binds", "suspend"):
                self.binds["suspend"] = self.parser.get("binds", "suspend").capitalize()
            if self.parser.has_option("binds", "hibernate"):
                self.binds["hibernate"] = self.parser.get(
                    "binds", "hibernate"
                ).capitalize()
            if self.parser.has_option("binds", "logout"):
                self.binds["logout"] = self.parser.get("binds", "logout").capitalize()
            if self.parser.has_option("binds", "cancel"):
                self.binds["cancel"] = self.parser.get("binds", "cancel").capitalize()
            if self.parser.has_option("binds", "settings"):
                self.binds["settings"] = self.parser.get(
                    "binds", "settings"
                ).capitalize()

        if self.parser.has_section("themes"):
            if self.parser.has_option("themes", "theme"):
                self.theme = self.parser.get("themes", "theme")

        if len(self.theme) > 1:
            style_provider = Gtk.CssProvider()
            style_provider.load_from_path(
                working_dir + "themes/" + self.theme + "/theme.css"
            )

            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                style_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
    except Exception as e:
        print(e)
        os.unlink(home + "/.config/archlinux-logout/archlinux-logout.conf")
        if not os.path.isfile(home + "/.config/archlinux-logout/archlinux-logout.conf"):
            shutil.copy(
                root_config, home + "/.config/archlinux-logout/archlinux-logout.conf"
            )


def _detect_desktop():
    desktop = "unknown"
    try:
        desktop = (
            os.environ.get("DESKTOP_SESSION")
            or os.environ.get("XDG_CURRENT_DESKTOP")
            or os.environ.get("XDG_SESSION_DESKTOP")
            or "unknown"
        )
        desktop = desktop.split(":")[0].strip().lower()
    except Exception:
        desktop = "unknown"

    # in case display manager ly is active
    status = os.system("systemctl is-active --quiet ly")
    if status == 0:
        try:
            out = subprocess.run(
                ["sh", "-c", "env | grep XDG_CURRENT_DESKTOP"],
                shell=False,
                stdout=subprocess.PIPE,
            )
            desktop = out.stdout.decode().split("=")[1].strip().split(":")[0].lower()
        except Exception:
            desktop = "unknown"

    if desktop == "unknown":
        try:
            if subprocess.run(
                ["pgrep", "-x", "ohmychadwm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0:
                desktop = "ohmychadwm"
            elif subprocess.run(
                ["pgrep", "-x", "chadwm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0:
                desktop = "chadwm"
            elif subprocess.run(
                ["pgrep", "-x", "dusk"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0:
                desktop = "dusk"
            elif subprocess.run(
                ["pgrep", "-x", "herbstluftwm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0:
                desktop = "herbstluftwm"
        except Exception:
            pass

    return desktop


def _hyprland_lua_config():
    """Return True when Hyprland uses the 0.55+ Lua config (needs `hl.dsp.exit()`)."""
    try:
        out = subprocess.run(["hyprctl", "version"], capture_output=True, text=True).stdout
    except Exception:
        return False
    m = re.search(r"v?(\d+)\.(\d+)\.\d+", out)
    return bool(m) and (int(m.group(1)), int(m.group(2))) >= (0, 55)


def _get_logout():
    desktop = _detect_desktop()

    print("Your desktop is " + desktop)
    if desktop in ("herbstluftwm", "/usr/share/xsessions/herbstluftwm"):
        return "herbstclient quit"
    elif desktop in ("bspwm", "/usr/share/xsessions/bspwm"):
        return "pkill bspwm"
    elif desktop in ("jwm", "/usr/share/xsessions/jwm"):
        return "pkill jwm"
    elif desktop in ("openbox", "/usr/share/xsessions/openbox"):
        return "pkill openbox"
    elif desktop in ("awesome", "/usr/share/xsessions/awesome"):
        return "pkill awesome"
    elif desktop in ("qtile", "/usr/share/xsessions/qtile"):
        return "pkill qtile"
    elif desktop in ("xmonad", "/usr/share/xsessions/xmonad"):
        return "pkill xmonad"
    elif desktop in ("worm", "/usr/share/xsessions/worm"):
        return "pkill worm"
    elif desktop in ("berry", "/usr/share/xsessions/berry"):
        return "pkill berry"
    elif desktop in ("Xmonad", "/usr/share/xsessions/xmonad"):
        return "pkill xmonad"
    elif desktop in ("dwm", "/usr/share/xsessions/dwm"):
        return "pkill dwm"
    elif desktop in ("chadwm", "/usr/share/xsessions/chadwm"):
        return "pkill chadwm"
    elif desktop in ("ohmychadwm", "/usr/share/xsessions/ohmychadwm"):
        shutdown_script = os.path.expanduser("~/.config/ohmychadwm/scripts/shutdown_ohmychadwm.sh")
        if os.path.isfile(shutdown_script):
            return shutdown_script
        else:
            return "pkill ohmychadwm"
    elif desktop in ("flexi", "/usr/share/xsessions/flexi"):
        return "pkill flexi"
    elif desktop in ("sunset", "/usr/share/xsessions/sunset"):
        return "pkill sunset"
    elif desktop in ("i3", "/usr/share/xsessions/i3"):
        return "pkill i3"
    elif desktop in ("i3-with-shmlog", "/usr/share/xsessions/i3-with-shmlog"):
        return "pkill i3-with-shmlog"
    elif desktop in ("lxqt", "/usr/share/xsessions/lxqt"):
        return "pkill lxqt"
    elif desktop in ("spectrwm", "/usr/share/xsessions/spectrwm"):
        return "pkill spectrwm"
    elif desktop in ("xfce", "/usr/share/xsessions/xfce"):
        return "xfce4-session-logout -f -l"
    elif desktop in ("icewm", "/usr/share/xsessions/icewm"):
        return "pkill icewm"
    elif desktop in ("icewm-session", "/usr/share/xsessions/icewm-session"):
        return "pkill icewm-session"
    elif desktop in ("cwm", "/usr/share/xsessions/cwm"):
        return "pkill cwm"
    elif desktop in ("fvwm3", "/usr/share/xsessions/fvwm3"):
        return "pkill fvwm3"
    elif desktop in ("stumpwm", "/usr/share/xsessions/stumpwm"):
        return "pkill stumpwm"
    elif desktop in ("leftwm", "/usr/share/xsessions/leftwm"):
        return "pkill leftwm"
    elif desktop in ("hyprland", "hypr", "hyprland-uwsm", "kiro-hyprland","kiro-hyprland-noctalia","kiro-hyprland-noctura",
                     "/usr/share/wayland-sessions/hyprland", "/usr/share/wayland-sessions/hyprland-uwsm",
                     "/usr/share/wayland-sessions/kiro-hyprland-noctalia","/usr/share/wayland-sessions/kiro-hyprland-noctura",
                     "/usr/share/wayland-sessions/kiro-hyprland",):
        # Hyprland (Wayland). Under uwsm use its graceful, ordered shutdown; otherwise the
        # native compositor exit. Never pkill — it's a hard kill and breaks uwsm's shutdown.
        # kiro-hyprland-noctalia ships its own session (DESKTOP_SESSION=kiro-hyprland-noctalia)
        # but is plain Hyprland underneath; noctalia-shell is a Hyprland child so the clean
        # compositor exit takes it down — same handling as any other Hyprland session.
        try:
            uwsm_managed = subprocess.run(
                ["systemctl", "--user", "is-active", "--quiet", "wayland-wm@Hyprland.service"]
            ).returncode == 0
        except Exception:
            uwsm_managed = False
        if uwsm_managed:
            return "uwsm stop"
        # Hyprland 0.55+ runs a Lua config: `hyprctl dispatch exit` is parsed as Lua
        # `hl.dispatch(exit)` and rejected — the dispatcher must be `hl.dsp.exit()`.
        if _hyprland_lua_config():
            return "hyprctl dispatch 'hl.dsp.exit()'"
        return "hyprctl dispatch exit"
    elif desktop in ("kiro-hyprland-dms", "/usr/share/wayland-sessions/kiro-hyprland-dms"):
        # Hyprland + DankMaterialShell edition. dms (the shell backend) + its qs
        # quickshell child are started by `dms run` from hyprland.lua. `dms kill` is
        # DMS's own CLI to tear the shell (and qs) down cleanly — run it first in case
        # DMS re-parents to `systemd --user` (as it does on niri) rather than staying a
        # Hyprland child, then do the same uwsm-aware / Lua-aware Hyprland exit as the
        # primary branch (uwsm stop when uwsm-managed; never pkill — it breaks uwsm's
        # ordered shutdown).
        try:
            uwsm_managed = subprocess.run(
                ["systemctl", "--user", "is-active", "--quiet", "wayland-wm@Hyprland.service"]
            ).returncode == 0
        except Exception:
            uwsm_managed = False
        _dms = "dms kill 2>/dev/null; pkill -x dms; "
        if uwsm_managed:
            return _dms + "uwsm stop"
        if _hyprland_lua_config():
            return _dms + "hyprctl dispatch 'hl.dsp.exit()'"
        return _dms + "hyprctl dispatch exit"
    elif desktop in ("dk", "/usr/share/xsessions/dk"):
        return "dkcmd exit"
    elif desktop in ("dusk", "/usr/share/xsessions/dusk"):
        # Exact-match kill so it doesn't also catch duskc (dusk's D-Bus control
        # client) or the dusk-status.sh bar feeder. dusk dying ends the session;
        # run.sh's loop breaks on the resulting non-zero exit.
        return "pkill -x dusk"
    elif desktop in ("wmderland", "/usr/share/xsessions/wmderland"):
        return "pkill wmderland"
    elif desktop in ("gnome", "/usr/share/xsessions/gnome"):
        return "gnome-session-quit --logout --no-prompt"
    elif desktop in ("gnome-xorg", "/usr/share/xsessions/gnome-xorg"):
        return "gnome-session-quit --logout --no-prompt"
    elif desktop in ("gnome-classic", "/usr/share/xsessions/gnome-classic"):
        return "gnome-session-quit --logout --no-prompt"
    elif desktop in ("nimdow", "/usr/share/xsessions/nimdow"):
        return "pkill nimdow"
    elif desktop in ("oxwm", "/usr/share/xsessions/oxwm"):
        return "pkill oxwm"
    # wayland desktops
    # These ship waybar/mako/hypridle/nm-applet as separate top-level processes
    # (not children of the compositor), so pkill-ing the compositor alone leaves
    # them orphaned across restarts/TWM switches on the same box — they pile up
    # and fight each other (e.g. hypridle over org.freedesktop.ScreenSaver).
    # Kill the companion daemons first, then the compositor.
    _waybar_stack = "pkill waybar; pkill mako; pkill hypridle; pkill nm-applet; "
    if desktop in ("sway", "/usr/share/wayland-sessions/sway"):
        return _waybar_stack + "pkill sway"
    elif desktop in ("scroll", "/usr/share/wayland-sessions/scroll"):
        # scroll is a fork of sway (kiro-scroll edition, sway-scroll package) with the
        # same DM-launched session model and the same Kiro waybar stack. Without this
        # explicit entry it falls through to the default "pkill scroll", which leaves
        # waybar/mako/hypridle/variety lingering -> unclean logout. Mirror sway.
        return _waybar_stack + "pkill scroll"
    elif desktop in ("river", "/usr/share/wayland-sessions/river"):
        return _waybar_stack + "pkill river"
    elif desktop in ("wayfire", "/usr/share/wayland-sessions/wayfire"):
        return _waybar_stack + "pkill wayfire"
    elif desktop in ("newm", "/usr/share/wayland-sessions/newm"):
        return "pkill newm"
    # niri runs as a systemd user service (niri.service, Type=notify): its own
    # `niri msg action quit -s` cleanly stops graphical-session.target and takes the
    # shell it spawned down with it. `pkill niri` hard-kills the compositor out from
    # under systemd, leaving a half-dead session (shell killed, niri lingering) that
    # looked like logout "needs two presses". The two Kiro niri editions now ship
    # their own session entries (kiro-niri.desktop / kiro-ohmyniri.desktop), so
    # DESKTOP_SESSION distinguishes them directly — no runtime probe needed.
    elif desktop in ("kiro-niri-noctalia", "kiro-niri",
                     "/usr/share/wayland-sessions/kiro-niri-noctalia",
                     "/usr/share/wayland-sessions/kiro-niri"):
        # noctalia-shell is a child of niri, so the clean quit takes it down.
        # Session file was renamed kiro-niri.desktop -> kiro-niri-noctalia.desktop;
        # the old id is kept as an alias so pre-rename installs still match.
        return "niri msg action quit -s"
    elif desktop in ("kiro-ohmyniri", "/usr/share/wayland-sessions/kiro-ohmyniri"):
        # Kill the loose waybar/mako/swayidle/variety daemons first, then clean-quit.
        return _waybar_stack + "pkill swayidle; pkill variety; niri msg action quit -s"
    elif desktop in ("kiro-niri-dms", "/usr/share/wayland-sessions/kiro-niri-dms"):
        # DankMaterialShell edition. dms (the shell backend), its qs quickshell child
        # and variety are spawned as loose siblings under `systemd --user`, NOT as niri
        # children, so quitting the compositor alone orphans them. `dms kill` is DMS's
        # own CLI to tear the shell (and its qs) down cleanly; kill variety too, then
        # clean-quit niri (Type=notify service) so graphical-session.target stops.
        return "dms kill 2>/dev/null; pkill -x dms; pkill -x variety; niri msg action quit -s"
    elif desktop in ("niri", "/usr/share/wayland-sessions/niri"):
        # Plain upstream niri session (no Kiro session entry): fall back to the
        # runtime shell probe to tell the editions apart.
        try:
            noctalia_running = subprocess.run(
                ["pgrep", "-f", "qs -c noctalia-shell"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            ).returncode == 0
        except Exception:
            noctalia_running = False
        if noctalia_running:
            return "niri msg action quit -s"
        return _waybar_stack + "pkill swayidle; pkill variety; niri msg action quit -s"
    elif desktop in ("labwc", "/usr/share/wayland-sessions/labwc"):
        return _waybar_stack + "pkill labwc"
    elif desktop in ("mango", "kiro-mango", "/usr/share/wayland-sessions/mango"):
        # kiro-mango.desktop's file id is "kiro-mango" (its own DesktopNames=mango;wlroots
        # sits alongside upstream mangowm's mango.desktop, so it can't reuse that filename),
        # but DESKTOP_SESSION is derived from the filename and is checked before
        # XDG_CURRENT_DESKTOP in _detect_desktop() -> without this alias it falls through
        # to "pkill kiro-mango", which matches nothing since the process is just "mango".
        return _waybar_stack + "pkill mango"
    elif desktop in ("dwl", "/usr/share/wayland-sessions/dwl"):
        # dwl ships its own suckless-style bar (dwlb), not waybar.
        return "pkill dwl"
    elif desktop in ("oxwm", "/usr/share/wayland-sessions/oxwm"):
        return "pkill oxwm"
    elif desktop in (
        "plasma", "plasmawayland", "plasmax11", "kde", "kde-plasma",
        "/usr/share/wayland-sessions/plasma",
        "/usr/share/xsessions/plasma",
        "/usr/share/wayland-sessions/plasmawayland",
    ):
        # Plasma 6 native logout (X11 + Wayland). Stops graphical-session.target
        # cleanly so kwin_wayland releases DRM-master; a bare "pkill plasma" only
        # kills plasmashell and leaves the compositor holding the GPU -> next
        # login is a black screen.
        return "qdbus6 org.kde.Shutdown /Shutdown org.kde.Shutdown.logout"
    if desktop and desktop != "unknown":
        name = desktop.rstrip("/").split("/")[-1]
        return "pkill " + name
    return None


def button_active(self, data, GdkPixbuf):
    try:
        icon_size = getattr(self, "main_icon_size", self.icon)
        if data == self.binds["shutdown"]:
            psh = GdkPixbuf.Pixbuf().new_from_file_at_size(
                os.path.join(
                    working_dir, "themes/" + self.theme + "/shutdown_blur.svg"
                ),
                icon_size,
                icon_size,
            )
            set_widget_pixbuf(self.imagesh, psh)
            self.lbl1.set_markup('<span foreground="white">Shutdown</span>')
        elif data == self.binds["restart"]:
            pr = GdkPixbuf.Pixbuf().new_from_file_at_size(
                os.path.join(working_dir, "themes/" + self.theme + "/restart_blur.svg"),
                icon_size,
                icon_size,
            )
            set_widget_pixbuf(self.imager, pr)
            self.lbl2.set_markup('<span foreground="white">Restart</span>')
        elif data == self.binds["suspend"]:
            ps = GdkPixbuf.Pixbuf().new_from_file_at_size(
                os.path.join(working_dir, "themes/" + self.theme + "/suspend_blur.svg"),
                icon_size,
                icon_size,
            )
            set_widget_pixbuf(self.images, ps)
            self.lbl3.set_markup('<span foreground="white">Suspend</span>')
        elif data == self.binds["lock"]:
            plk = GdkPixbuf.Pixbuf().new_from_file_at_size(
                os.path.join(working_dir, "themes/" + self.theme + "/lock_blur.svg"),
                icon_size,
                icon_size,
            )
            set_widget_pixbuf(self.imagelk, plk)
            self.lbl4.set_markup('<span foreground="white">Lock</span>')
        elif data == self.binds["logout"]:
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                os.path.join(working_dir, "themes/" + self.theme + "/logout_blur.svg"),
                icon_size,
                icon_size,
            )
            set_widget_pixbuf(self.imagelo, plo)
            self.lbl5.set_markup('<span foreground="white">Logout</span>')
        elif data == self.binds["cancel"]:
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                os.path.join(working_dir, "themes/" + self.theme + "/cancel_blur.svg"),
                icon_size,
                icon_size,
            )
            set_widget_pixbuf(self.imagec, plo)
            self.lbl6.set_markup('<span foreground="white">Cancel</span>')
        elif data == self.binds["hibernate"]:
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                os.path.join(
                    working_dir, "themes/" + self.theme + "/hibernate_blur.svg"
                ),
                icon_size,
                icon_size,
            )
            set_widget_pixbuf(self.imageh, plo)
            self.lbl7.set_markup('<span foreground="white">Hibernate</span>')
    except Exception:
        pass


def button_toggled(self, data):
    self.Esh.set_sensitive(False)
    self.Er.set_sensitive(False)
    self.Es.set_sensitive(False)
    self.Elk.set_sensitive(False)
    self.El.set_sensitive(False)
    self.Ec.set_sensitive(False)
    self.Eh.set_sensitive(False)

    if data == self.binds["shutdown"]:
        self.Esh.set_sensitive(True)
    elif data == self.binds["restart"]:
        self.Er.set_sensitive(True)
    elif data == self.binds["suspend"]:
        self.Es.set_sensitive(True)
    elif data == self.binds["lock"]:
        self.Elk.set_sensitive(True)
    elif data == self.binds["logout"]:
        self.El.set_sensitive(True)
    elif data == self.binds["cancel"]:
        self.Ec.set_sensitive(True)
    elif data == self.binds["hibernate"]:
        self.Eh.set_sensitive(True)


def file_check(file):
    if os.path.isfile(file):
        return True
