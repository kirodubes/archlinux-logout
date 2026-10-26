# =================================================================
# =                  Author: Brad Heffernan                       =
# =================================================================
import os
import psutil
import gi
from os.path import expanduser

gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk  # noqa


home = expanduser("~")
base_dir = os.path.dirname(os.path.realpath(__file__))
config = home + "/.config/archlinux-betterlockscreen/"
settings = "settings.conf"
default_wallpapers = "/usr/share/archlinux-betterlockscreen/wallpapers"
resolutions = [
    "640x360",
    "800x600",
    "1024x768",
    "1280x720",
    "1280x800",
    "1280x1024",
    "1360x768",
    "1366x768",
    "1440x900",
    "1536x864",
    "1600x900",
    "1680x1050",
    "1920x1080",
    "1920x1200",
    "2048x1152",
    "2560x1080",
    "2560x1440",
    "3440x1440",
    "3840x2160"
]


def _get_position(lists, string):
    nlist = [x for x in lists if string in x]
    position = lists.index(nlist[0])
    return position


def get_saved_path():
    with open(config + settings, "r") as f:
        lines = f.readlines()
    pos = _get_position(lines, "path=")
    return lines[pos].split("=")[1].strip()


def save_path(path):
    """Remember the folder that was loaded last."""
    with open(config + settings, "w") as f:
        f.write("path=" + path)


def preset_folders():
    """Return the known wallpaper folders that exist on this system."""
    candidates = [
        default_wallpapers,
        "/usr/share/backgrounds",
        home + "/.config/variety",
        home + "/Templates/wallpapers",
        home + "/Pictures",
    ]
    return [folder for folder in candidates if os.path.isdir(folder)]


def get_betterlockscreen_version():
    """Return the installed betterlockscreen version, or 'unknown'."""
    # Parse the script directly — `betterlockscreen --version` shells out to xset
    # and needs an X display, which is not always available at startup.
    for path in ("/usr/bin/betterlockscreen", "/bin/betterlockscreen"):
        try:
            with open(path, "r") as f:
                for line in f:
                    if line.strip().startswith("VERSION="):
                        return line.split("=", 1)[1].strip().strip('"')
        except OSError:
            continue
    return "unknown"


def show_in_app_notification(self, message):
    if self.timeout_id is not None:
        GLib.source_remove(self.timeout_id)
        self.timeout_id = None

    self.notification_label.set_markup(
        '<span foreground="white">' + message + '</span>'
    )
    self.notification_revealer.set_reveal_child(True)
    self.timeout_id = GLib.timeout_add(3000, timeOut, self)


def timeOut(self):
    close_in_app_notification(self)
    return False


def close_in_app_notification(self):
    self.notification_revealer.set_reveal_child(False)
    self.timeout_id = None


def MessageBox(parent, title, message):
    dialog = Gtk.AlertDialog(message=title, detail=message)
    dialog.show(parent)


def checkIfProcessRunning(processName):
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
            if processName == pinfo['pid']:
                return True
        except (psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess):
            pass
    return False
