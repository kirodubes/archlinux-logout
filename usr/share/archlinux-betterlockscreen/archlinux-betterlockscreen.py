#!/usr/bin/env python3

# =================================================================
# =                  Author: Brad Heffernan                       =
# =================================================================

# ── Force Python UTF-8 mode on a non-UTF-8 locale ─────────────────────────
# Never crash on a non-UTF-8 system locale (e.g. latin-1 fr_BE). Under such a
# locale Python encodes stdout and subprocess output with latin-1, so any
# non-ASCII glyph raises a Unicode error. UTF-8 mode forces UTF-8 regardless of
# LANG. Re-exec only when the locale's encoding is not UTF-8 — a normal UTF-8
# desktop is left untouched; the guard is loop-safe (the re-exec'd process is
# UTF-8 already).
import codecs
import os
import sys

if codecs.lookup(sys.getfilesystemencoding()).name != "utf-8":
    os.environ["PYTHONUTF8"] = "1"
    os.execv(sys.executable, [sys.executable, "-X", "utf8", *sys.argv])

# Spawned terminals inherit our locale; if it is not UTF-8 their output renders
# as mojibake. Keep the user's locale when it is already UTF-8, otherwise fall
# back to C.UTF-8 so child output stays readable.
_cur_locale = os.environ.get("LC_ALL") or os.environ.get("LC_CTYPE") or os.environ.get("LANG") or ""
if "utf-8" not in _cur_locale.lower() and "utf8" not in _cur_locale.lower():
    os.environ["LANG"] = "C.UTF-8"
    os.environ["LC_ALL"] = "C.UTF-8"

import gi  # noqa: E402
import Functions as fn  # noqa: E402
import GUI  # noqa: E402
import Support  # noqa: E402
from abl_i18n import _  # noqa: E402
import subprocess  # noqa: E402
import threading as th  # noqa: E402
import webbrowser  # noqa: E402

gi.require_version('Gtk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib, Gio  # noqa


class Main(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=_("ArchLinux BetterLockScreen"))
        self.set_default_size(1100, 700)
        self.connect("close-request", self.close)
        self._build_headerbar()

        self.timeout_id = None
        self.image_path = None

        if not fn.os.path.isdir(fn.config):
            fn.os.mkdir(fn.config)

        if not fn.os.path.isfile(fn.config + fn.settings):
            with open(fn.config + fn.settings, "w") as f:
                f.write("path=")

        self.loc = Gtk.Entry()
        self.search = Gtk.Entry()
        self.status = Gtk.Label(label="")
        self.hbox3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.fb = Gtk.FlowBox()
        self.fb.set_valign(Gtk.Align.START)
        self.fb.set_min_children_per_line(1)
        self.fb.set_max_children_per_line(30)
        self.fb.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.fb.connect("child-activated", self.on_item_clicked)

        scrolled.set_child(self.fb)
        self.hbox3.append(scrolled)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)

        self._load_gen = 0
        saved = fn.get_saved_path()
        self.loc.set_text(saved if fn.os.path.isdir(saved) else fn.default_wallpapers)

        GUI.GUI(self, Gtk, GdkPixbuf, Gdk, th, fn)

        with open("/tmp/archlinux-betterlock.lock", "w") as f:
            f.write("")

        # Defer flowbox loading so the window is shown first
        GLib.idle_add(self._load_initial_flowbox)

    def _build_headerbar(self):
        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)
        self.set_titlebar(header)

    def _load_initial_flowbox(self):
        self._start_load(self.loc.get_text())
        return False

    def _start_load(self, path):
        self._clear_flowbox()
        self._load_gen += 1
        # Widgets are read here on the GTK thread; the worker only gets plain values
        t = th.Thread(target=self.create_flowbox, args=(path, self.search.get_text(), self._load_gen))
        t.daemon = True
        t.start()

    def _append_if_current(self, picture, gen):
        # Images queued by an older load may still arrive after the grid was cleared
        if gen == self._load_gen:
            self.fb.append(picture)
        return False

    def on_default_clicked(self, _widget):
        self.loc.set_text(fn.default_wallpapers)
        self._start_load(fn.default_wallpapers)

    def on_preset_selected(self, dropdown, _pspec):
        item = dropdown.get_selected_item()
        if item is None:
            return
        self.loc.set_text(item.get_string())
        self._start_load(item.get_string())

    def on_support_clicked(self, _widget):
        sup = Support.Support(self)
        sup.present()

    def on_apply_clicked(self, _widget):
        if self.image_path is None:
            fn.show_in_app_notification(self, _("You need to select an image first"))
        else:
            self.btnset.set_sensitive(False)
            self.apply_spinner.start()
            self.status.set_text(_("creating lockscreen images....wait for the message at the top"))
            t = th.Thread(target=self.set_lockscreen)
            t.daemon = True
            t.start()

    def _apply_done(self, status):
        self.apply_spinner.stop()
        self.btnset.set_sensitive(True)
        self.status.set_text(status)
        return False

    def set_lockscreen(self):
        command = ["betterlockscreen", "-u", self.image_path,
                   "--blur", str(int(self.blur.get_value()) / 100)]
        try:
            subprocess.Popen(command, shell=False).wait()
            fn.show_in_app_notification(self, _("Lockscreen set successfully"))
            GLib.idle_add(self._apply_done, "")
        except Exception:
            GLib.idle_add(self._apply_done, _("ERROR: is betterlockscreen installed?"))

    def on_item_clicked(self, _flowbox, child):
        image = child.get_child()
        if image:
            self.image_path = image.get_name()

    def on_load_clicked(self, _widget):
        self._start_load(self.loc.get_text())

    def on_search_clicked(self, _widget):
        self._start_load(self.loc.get_text())

    def _clear_flowbox(self):
        while True:
            child = self.fb.get_child_at_index(0)
            if child is None:
                break
            self.fb.remove(child)

    def on_browse_clicked(self, _widget):
        dialog = Gtk.FileDialog(title=_("Please choose a folder"))
        dialog.set_initial_folder(Gio.File.new_for_path(fn.home))
        dialog.select_folder(self, None, self._on_browse_response)

    def _on_browse_response(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            path = folder.get_path()
            self.loc.set_text(path)
            self._start_load(path)
        except Exception as e:
            print(f"[DEBUG]: Folder dialog: {e}")

    def create_flowbox(self, paths, search, gen):
        paths = paths.strip().rstrip("/") or fn.default_wallpapers

        if not fn.os.path.isdir(paths):
            GLib.idle_add(self.status.set_text, _("That directory not found!"))
            return 0
        # Every way of loading (dropdown, Browse, Load, Default) passes here, so this remembers them all
        fn.save_path(paths)
        GLib.idle_add(self.status.set_text, _("Loading images..."))
        ext = (".png", ".jpg", ".jpeg", ".webp")
        images = []
        # followlinks stays False so a symlink loop can't make the walk endless
        for root, dirs, files in fn.os.walk(paths):
            dirs.sort()
            images.extend(fn.os.path.join(root, x) for x in sorted(files)
                          if x.lower().endswith(ext) and search in x)
        for image in images:
            # A newer load started; stop filling the grid with this folder
            if gen != self._load_gen:
                return 0
            # Skip a broken or half-downloaded file instead of ending the whole load on it
            try:
                pb = GdkPixbuf.Pixbuf().new_from_file_at_size(image, 320, 180)
            except GLib.Error as e:
                print(f"[WARN]: Skipping {image}: {e.message}")
                continue
            pimage = Gtk.Picture()
            pimage.set_name(image)
            pimage.set_paintable(Gdk.Texture.new_for_pixbuf(pb))
            pimage.set_can_shrink(False)
            pimage.set_content_fit(Gtk.ContentFit.FILL)
            pimage.set_size_request(320, 180)
            GLib.idle_add(self._append_if_current, pimage, gen)
        GLib.idle_add(self.status.set_text, "")

    def on_social_clicked(self, widget, link):
        t = th.Thread(target=self.weblink, args=(link,))
        t.daemon = True
        t.start()

    def weblink(self, link):
        webbrowser.open_new_tab(link)

    def tooltip_callback(self, widget, x, y, keyboard_mode, tooltip, text):
        tooltip.set_text(text)
        return True

    def close(self, widget):
        try:
            fn.os.unlink("/tmp/archlinux-betterlock.lock")
        except Exception:
            pass
        self.get_application().quit()
        return False


class BetterLockScreenApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.archlinux.betterlockscreen")

    def do_activate(self):
        # A second launch activates this running instance again: raise its window instead of reporting our own
        # lock file. The lock still catches what GTK can't: another session bus, a crash.
        window = self.get_active_window()
        if window is not None:
            window.present()
            return
        if not fn.os.path.isfile("/tmp/archlinux-betterlock.lock"):
            try:
                with open("/tmp/archlinux-betterlock.pid", "w") as f:
                    f.write(str(fn.os.getpid()))
            except PermissionError:
                print("[WARN]: Could not write /tmp/archlinux-betterlock.pid")
            win = Main(self)
            win.present()
        else:
            # Create a temporary window as parent so dialogs have a transient parent
            self._lock_parent = Gtk.Window(application=self)
            self._lock_parent.set_decorated(False)
            self._lock_parent.set_default_size(1, 1)
            self._lock_parent.present()
            dialog = Gtk.AlertDialog(
                message=_("Lock File Found"),
                detail=_(
                    "The lock file has been found. This indicates there is already "
                    "an instance of ArchLinux Betterlockscreen GUI running.\n"
                    "Click Yes to remove the lock file and try running again."
                ),
                buttons=[_("No"), _("Yes")],
                default_button=1,
                cancel_button=0,
            )
            dialog.choose(self._lock_parent, None, self._on_lock_dialog_response)

    def _on_lock_dialog_response(self, dialog, result):
        try:
            button = dialog.choose_finish(result)
        except Exception:
            self._lock_parent.destroy()
            return
        if button == 1:  # Yes
            pid = ""
            try:
                with open("/tmp/archlinux-betterlock.pid", "r") as f:
                    pid = f.read().strip()
            except Exception:
                pass
            if pid and fn.checkIfProcessRunning(int(pid)):
                alert = Gtk.AlertDialog(
                    message=_("Application Running!"),
                    detail=_("You first need to close the existing application"),
                )
                alert.show(self._lock_parent)
            else:
                fn.os.unlink("/tmp/archlinux-betterlock.lock")
                self._lock_parent.destroy()
                self.do_activate()
        else:
            self._lock_parent.destroy()
            self.quit()


if __name__ == "__main__":
    app = BetterLockScreenApp()
    app.run(sys.argv)
