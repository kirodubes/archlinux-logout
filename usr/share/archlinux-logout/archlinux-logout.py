# =====================================================
#        Authors Brad Heffernan, Fennec and Erik Dubois
# =====================================================

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
import shutil  # noqa: E402
import GUI  # noqa: E402
import Functions as fn  # noqa: E402
from alo_i18n import _  # noqa: E402
import threading  # noqa: E402
import signal  # noqa: E402
from distro import id  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gtk, GdkPixbuf, Gdk, GLib, Gio  # noqa


class TransparentWindow(Gtk.ApplicationWindow):
    distr = id()

    cmd_shutdown = "systemctl poweroff"
    cmd_restart = "systemctl reboot"
    cmd_suspend = "systemctl suspend"
    cmd_hibernate = "systemctl hibernate"

    if distr == "artix":
        if os.path.isfile("/usr/bin/loginctl"):
            cmd_shutdown = "loginctl poweroff"
            cmd_restart = "loginctl reboot"
            cmd_suspend = "loginctl suspend"
            cmd_hibernate = "loginctl hibernate"

    cmd_lock = 'betterlockscreen -l dim -- --time-str="%H:%M"'
    wallpaper = "/usr/share/archlinux-betterlockscreen/wallpapers/wallpaper.jpg"
    d_buttons = [
        "cancel",
        "shutdown",
        "restart",
        "suspend",
        "hibernate",
        "lock",
        "logout",
    ]
    binds = {
        "lock": "K",
        "restart": "R",
        "shutdown": "S",
        "suspend": "U",
        "hibernate": "H",
        "logout": "L",
        "cancel": "Escape",
        "settings": "P",
    }
    theme = "handy"
    hover = "#ffffff"
    icon = 80
    font = 11
    show_text = False
    buttons = None
    active = False
    opacity = 0.8
    main_icon_size = 80
    aux_icon_size = 32

    def __init__(self, app, settings_only=False):
        super().__init__(application=app, title=_("ArchLinux Logout"))

        self.settings_only = settings_only

        self.set_decorated(False)

        self.connect("close-request", self.on_close)

        # In settings mode the power keybinds must NOT be wired — otherwise
        # pressing "S"/"R"/etc. in the settings window would fire a real action.
        if not settings_only:
            key_controller = Gtk.EventControllerKey()
            key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
            key_controller.connect("key-pressed", self.on_keypress)
            self.add_controller(key_controller)

        self.connect("notify::fullscreened", self.on_window_state_changed)
        self.__is_fullscreen = False

        if not fn.os.path.isdir(fn.home + "/.config/archlinux-logout"):
            fn.os.mkdir(fn.home + "/.config/archlinux-logout")

        if not fn.os.path.isfile(
            fn.home + "/.config/archlinux-logout/archlinux-logout.conf"
        ):
            shutil.copy(
                fn.root_config,
                fn.home + "/.config/archlinux-logout/archlinux-logout.conf",
            )

        self.width = 0
        self.display = Gdk.Display.get_default()

        fn.get_config(self, Gdk, Gtk, fn.config)

        if self.buttons is None or self.buttons == [""]:
            self.buttons = self.d_buttons

        self.main_icon_size = self.icon
        self.aux_icon_size = 32

        if settings_only:
            self._build_settings_window()
            return

        self._apply_background_css()
        self.display_on_monitor()

        # Show the dark background immediately, load icons on next idle cycle
        self.present()
        GLib.idle_add(self._build_gui)

    def _build_settings_window(self):
        self.set_title(_("ArchLinux Logout Settings"))
        self.set_decorated(True)
        self.set_resizable(True)
        self.set_default_size(520, 800)
        # Floor the window so it can't be dragged smaller than its content
        self.set_size_request(480, 500)

        headerbar = Gtk.HeaderBar()
        headerbar.set_show_title_buttons(True)
        self.set_titlebar(headerbar)

        self._load_settings_css()

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_child(GUI.SettingsPanel(self, Gtk, fn))
        outer.append(scroller)

        outer.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        action_bar.set_margin_start(12)
        action_bar.set_margin_end(12)
        action_bar.set_margin_top(8)
        action_bar.set_margin_bottom(10)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        action_bar.append(spacer)

        btn_betterlockscreen = Gtk.Button(label=_("Open BetterLockScreen"))
        btn_betterlockscreen.set_tooltip_text(_("Configure the lock screen wallpaper and blur"))
        btn_betterlockscreen.connect("clicked", self.on_betterlockscreen_clicked)
        action_bar.append(btn_betterlockscreen)
        action_bar.append(self.btn_save_settings)

        outer.append(action_bar)

        self.set_child(outer)
        self.present()

    def _load_settings_css(self):
        css = (
            b"label#title { font-size: 20px; font-weight: 600; }"
            b"label.info-label { color: alpha(currentColor, 0.65); font-size: 11px; }"
            b".support-button { color: #e0567a; }"
            b".support-button:hover { background-color: alpha(#e0567a, 0.18); }"
        )
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            self.display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def on_betterlockscreen_clicked(self, _widget):
        t = threading.Thread(
            target=lambda: fn.subprocess.Popen(["archlinux-betterlockscreen"]),
            daemon=True,
        )
        t.start()

    def _after_save(self):
        if getattr(self, "popover", None):
            self.popover.popdown()
        elif self.settings_only:
            self.close()

    def on_exit_clicked(self, _widget):
        self.close()

    def _build_gui(self):
        self._pending_pixbufs = []
        GUI.GUI(self, Gtk, GdkPixbuf, fn.working_dir, fn.os, Gdk, fn)
        self.set_focusable(True)
        self.grab_focus()
        if not fn.os.path.isfile("/tmp/archlinux-logout.lock"):
            with open("/tmp/archlinux-logout.lock", "w") as f:
                f.write("")
        t = threading.Thread(target=self._load_pixbufs_async, daemon=True)
        t.start()
        return False

    def _load_pixbufs_async(self):
        for svg_path, widget, size in self._pending_pixbufs:
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_size(svg_path, size, size)
                fmt = Gdk.MemoryFormat.R8G8B8A8 if pb.get_has_alpha() else Gdk.MemoryFormat.R8G8B8
                texture = Gdk.MemoryTexture.new(
                    pb.get_width(), pb.get_height(), fmt,
                    GLib.Bytes.new(pb.get_pixels()), pb.get_rowstride(),
                )
                GLib.idle_add(widget.set_paintable, texture)
            except Exception as e:
                print(f"[WARN]: Could not load {svg_path}: {e}")

    def _apply_background_css(self):
        css = (
            f"window {{ background-color: rgba(0, 0, 0, {self.opacity}); }}"
            " label#lbl {"
            "   color: white;"
            "   background-color: rgba(0, 0, 0, 0.55);"
            "   padding: 4px 10px;"
            "   border-radius: 4px;"
            " }"
        )
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            self.display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
        )

    def _cleanup_runtime_files(self):
        for path in ("/tmp/archlinux-logout.lock", "/tmp/archlinux-logout.pid"):
            try:
                fn.os.unlink(path)
            except FileNotFoundError:
                pass
            except Exception:
                pass

    def display_on_monitor(self):
        print("#### Archlinux Logout ####")
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()

        if session_type == "wayland":
            print("[WARN]: Session type = wayland, mouse position can't be tracked")
            self.display_on_default()
            return

        if session_type == "x11":
            print("[DEBUG]: Session type = x11")
            try:
                import subprocess

                result = subprocess.run(
                    ["xdotool", "getmouselocation", "--shell"],
                    capture_output=True,
                    text=True,
                    timeout=0.3,
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    x_vals = [line.split("=")[1] for line in lines if line.startswith("X=")]
                    y_vals = [line.split("=")[1] for line in lines if line.startswith("Y=")]
                    if x_vals and y_vals:
                        x = int(x_vals[0])
                        y = int(y_vals[0])
                        print(f"[DEBUG]: Mouse position x={x} y={y}")
                        monitor = self._get_monitor_at_point(x, y)
                        if monitor:
                            geometry = monitor.get_geometry()
                            print(
                                f"[DEBUG]: Monitor: Dimension={geometry.width}x{geometry.height}"
                            )
                            self.set_size_request(geometry.width, geometry.height)
                            self.fullscreen_on_monitor(monitor)
                            return
            except Exception as e:
                print(f"[DEBUG]: Could not get mouse position via xdotool: {e}")

        self.display_on_default()

    def _get_monitor_at_point(self, x, y):
        monitors = self.display.get_monitors()
        for i in range(monitors.get_n_items()):
            monitor = monitors.get_item(i)
            geom = monitor.get_geometry()
            if (
                geom.x <= x < geom.x + geom.width
                and geom.y <= y < geom.y + geom.height
            ):
                return monitor
        return monitors.get_item(0)

    def display_on_default(self):
        monitors = self.display.get_monitors()
        monitor = monitors.get_item(0)
        if monitor:
            geometry = monitor.get_geometry()
            print("[DEBUG]: Showing on first monitor")
            print(f"[DEBUG]: Dimension: {geometry.width}x{geometry.height}")
            self.set_size_request(geometry.width, geometry.height)
            self.fullscreen_on_monitor(monitor)

    def _apply_save_lines(self, lines):
        pos_opacity = fn._get_position(lines, "opacity")
        pos_size = fn._get_position(lines, "icon_size")
        pos_theme = fn._get_position(lines, "theme=")
        pos_font = fn._get_position(lines, "font_size=")
        pos_show_text = fn._get_position(lines, "show_text")

        lines[pos_opacity] = "opacity=" + str(int(self.hscale.get_value())) + "\n"
        lines[pos_size] = "icon_size=" + str(int(self.icons.get_value())) + "\n"
        lines[pos_theme] = "theme=" + self.themes.get_selected_item().get_string() + "\n"
        lines[pos_font] = "font_size=" + str(int(self.fonts.get_value())) + "\n"
        lines[pos_show_text] = "show_text=" + str(self.chk_show_text.get_active()) + "\n"

        self.show_text = self.chk_show_text.get_active()
        for attr in ("lbl1", "lbl2", "lbl3", "lbl4", "lbl5", "lbl6", "lbl7"):
            lbl = getattr(self, attr, None)
            if lbl:
                lbl.set_visible(self.show_text)

        # Save button visibility selection
        _all_buttons = ["cancel", "shutdown", "restart", "suspend", "hibernate", "lock", "logout"]
        selected = [b for b in _all_buttons
                    if getattr(self, f"chk_btn_{b}", None) and getattr(self, f"chk_btn_{b}").get_active()]
        new_buttons_line = "buttons=" + ",".join(selected) + "\n"
        for idx, line in enumerate(lines):
            if line.strip().startswith("buttons="):
                lines[idx] = new_buttons_line
                break

    def on_save_clicked(self, _widget):
        try:
            with open(
                fn.home + "/.config/archlinux-logout/archlinux-logout.conf", "r"
            ) as f:
                lines = f.readlines()

            self._apply_save_lines(lines)

            with open(
                fn.home + "/.config/archlinux-logout/archlinux-logout.conf", "w"
            ) as f:
                f.writelines(lines)
            self._after_save()
        except Exception:
            fn.os.unlink(fn.home + "/.config/archlinux-logout/archlinux-logout.conf")
            if not fn.os.path.isfile(
                fn.home + "/.config/archlinux-logout/archlinux-logout.conf"
            ):
                shutil.copy(
                    fn.root_config,
                    fn.home + "/.config/archlinux-logout/archlinux-logout.conf",
                )
            with open(
                fn.home + "/.config/archlinux-logout/archlinux-logout.conf", "r"
            ) as f:
                lines = f.readlines()

            self._apply_save_lines(lines)

            with open(
                fn.home + "/.config/archlinux-logout/archlinux-logout.conf", "w"
            ) as f:
                f.writelines(lines)
            self._after_save()

    def _cancel_hover_timer(self):
        if getattr(self, "_hover_timer_id", None):
            GLib.source_remove(self._hover_timer_id)
            self._hover_timer_id = None

    def _start_hover_timer(self, lbl):
        self._cancel_hover_timer()

        def show_label():
            lbl.set_visible(True)
            self._hover_timer_id = None
            return False
        self._hover_timer_id = GLib.timeout_add(2000, show_label)

    def on_mouse_in(self, widget, data):
        widget.set_cursor(Gdk.Cursor.new_from_name("pointer"))

        if data == self.binds.get("shutdown"):
            psh = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/shutdown_blur.svg"
                ),
                self.main_icon_size,
                self.main_icon_size,
            )
            fn.set_widget_pixbuf(self.imagesh, psh)
            self.lbl1.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">{_("Shut down ({key})").format(key=data)}</span>'
            )
            self._start_hover_timer(self.lbl1)
        elif data == self.binds.get("restart"):
            pr = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/restart_blur.svg"
                ),
                self.main_icon_size,
                self.main_icon_size,
            )
            fn.set_widget_pixbuf(self.imager, pr)
            self.lbl2.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">{_("Restart ({key})").format(key=data)}</span>'
            )
            self._start_hover_timer(self.lbl2)
        elif data == self.binds.get("suspend"):
            ps = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/suspend_blur.svg"
                ),
                self.main_icon_size,
                self.main_icon_size,
            )
            fn.set_widget_pixbuf(self.images, ps)
            self.lbl3.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">{_("Suspend ({key})").format(key=data)}</span>'
            )
            self._start_hover_timer(self.lbl3)
        elif data == self.binds.get("lock"):
            plk = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/lock_blur.svg"
                ),
                self.main_icon_size,
                self.main_icon_size,
            )
            fn.set_widget_pixbuf(self.imagelk, plk)
            self.lbl4.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">{_("Lock ({key})").format(key=data)}</span>'
            )
            self._start_hover_timer(self.lbl4)
        elif data == self.binds.get("logout"):
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/logout_blur.svg"
                ),
                self.main_icon_size,
                self.main_icon_size,
            )
            fn.set_widget_pixbuf(self.imagelo, plo)
            self.lbl5.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">{_("Log out ({key})").format(key=data)}</span>'
            )
            self._start_hover_timer(self.lbl5)
        elif data == self.binds.get("cancel"):
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/cancel_blur.svg"
                ),
                self.main_icon_size,
                self.main_icon_size,
            )
            fn.set_widget_pixbuf(self.imagec, plo)
            self.lbl6.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">{_("Cancel ({key})").format(key=data)}</span>'
            )
            self._start_hover_timer(self.lbl6)
        elif data == self.binds.get("hibernate"):
            plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(
                    fn.working_dir, "themes/" + self.theme + "/hibernate_blur.svg"
                ),
                self.main_icon_size,
                self.main_icon_size,
            )
            fn.set_widget_pixbuf(self.imageh, plo)
            self.lbl7.set_markup(
                f'<span size="{str(self.font)}000" foreground="{self.hover}">{_("Hibernate ({key})").format(key=data)}</span>'
            )
            self._start_hover_timer(self.lbl7)
        elif data == self.binds.get("settings"):
            pset = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(fn.working_dir, "configure_blur.svg"),
                self.aux_icon_size,
                self.aux_icon_size,
            )
            fn.set_widget_pixbuf(self.imageset, pset)
        elif data == "light":
            pset = GdkPixbuf.Pixbuf().new_from_file_at_size(
                fn.os.path.join(fn.working_dir, "light_blur.svg"),
                self.aux_icon_size,
                self.aux_icon_size,
            )
            fn.set_widget_pixbuf(self.imagelig, pset)

    def on_mouse_out(self, widget, data):
        widget.set_cursor(None)
        self._cancel_hover_timer()

        if not self.active:
            if data == self.binds.get("shutdown"):
                psh = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/shutdown.svg"
                    ),
                    self.main_icon_size,
                    self.main_icon_size,
                )
                fn.set_widget_pixbuf(self.imagesh, psh)
                self.lbl1.set_markup(
                    f'<span size="{str(self.font)}000">{_("Shut down ({key})").format(key=data)}</span>'
                )
                self.lbl1.set_visible(self.show_text)
            elif data == self.binds.get("restart"):
                pr = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/restart.svg"
                    ),
                    self.main_icon_size,
                    self.main_icon_size,
                )
                fn.set_widget_pixbuf(self.imager, pr)
                self.lbl2.set_markup(
                    f'<span size="{str(self.font)}000">{_("Restart ({key})").format(key=data)}</span>'
                )
                self.lbl2.set_visible(self.show_text)
            elif data == self.binds.get("suspend"):
                ps = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/suspend.svg"
                    ),
                    self.main_icon_size,
                    self.main_icon_size,
                )
                fn.set_widget_pixbuf(self.images, ps)
                self.lbl3.set_markup(
                    f'<span size="{str(self.font)}000">{_("Suspend ({key})").format(key=data)}</span>'
                )
                self.lbl3.set_visible(self.show_text)
            elif data == self.binds.get("lock"):
                plk = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/lock.svg"
                    ),
                    self.main_icon_size,
                    self.main_icon_size,
                )
                fn.set_widget_pixbuf(self.imagelk, plk)
                self.lbl4.set_markup(
                    f'<span size="{str(self.font)}000">{_("Lock ({key})").format(key=data)}</span>'
                )
                self.lbl4.set_visible(self.show_text)
            elif data == self.binds.get("logout"):
                plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/logout.svg"
                    ),
                    self.main_icon_size,
                    self.main_icon_size,
                )
                fn.set_widget_pixbuf(self.imagelo, plo)
                self.lbl5.set_markup(
                    f'<span size="{str(self.font)}000">{_("Log out ({key})").format(key=data)}</span>'
                )
                self.lbl5.set_visible(self.show_text)
            elif data == self.binds.get("cancel"):
                plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/cancel.svg"
                    ),
                    self.main_icon_size,
                    self.main_icon_size,
                )
                fn.set_widget_pixbuf(self.imagec, plo)
                self.lbl6.set_markup(
                    f'<span size="{str(self.font)}000">{_("Cancel ({key})").format(key=data)}</span>'
                )
                self.lbl6.set_visible(self.show_text)
            elif data == self.binds.get("hibernate"):
                plo = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(
                        fn.working_dir, "themes/" + self.theme + "/hibernate.svg"
                    ),
                    self.main_icon_size,
                    self.main_icon_size,
                )
                fn.set_widget_pixbuf(self.imageh, plo)
                self.lbl7.set_markup(
                    f'<span size="{str(self.font)}000">{_("Hibernate ({key})").format(key=data)}</span>'
                )
                self.lbl7.set_visible(self.show_text)
            elif data == self.binds.get("settings"):
                pset = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(fn.working_dir, "configure.svg"),
                    self.aux_icon_size,
                    self.aux_icon_size,
                )
                fn.set_widget_pixbuf(self.imageset, pset)
            elif data == "light":
                pset = GdkPixbuf.Pixbuf().new_from_file_at_size(
                    fn.os.path.join(fn.working_dir, "light.svg"),
                    self.aux_icon_size,
                    self.aux_icon_size,
                )
                fn.set_widget_pixbuf(self.imagelig, pset)

    def on_click(self, widget, data):
        self.click_button(widget, data)

    def on_window_state_changed(self, window, pspec):
        self.__is_fullscreen = window.is_fullscreen()

    def on_keypress(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.click_button(None, self.binds.get("cancel"))
            return True

        self.shortcut_keys = [
            self.binds.get("cancel"),
            self.binds.get("shutdown"),
            self.binds.get("restart"),
            self.binds.get("suspend"),
            self.binds.get("logout"),
            self.binds.get("lock"),
            self.binds.get("hibernate"),
            self.binds.get("settings"),
        ]

        for key in self.shortcut_keys:
            if keyval == Gdk.keyval_to_lower(Gdk.keyval_from_name(key)):
                self.click_button(None, key)
                return True

        return False

    def click_button(self, widget, data=None):
        if data != self.binds.get("settings") and data != "light":
            self.active = True
            fn.button_toggled(self, data)
            fn.button_active(self, data, GdkPixbuf)

        if data == self.binds.get("logout"):
            command = fn._get_logout()
            if not command:
                self.message_box(
                    _("No logout command could be detected for this desktop session."),
                    _("Logout command not found"),
                )
                self.active = False
                return
            self._cleanup_runtime_files()
            self.__exec_cmd(command)
            self.get_application().quit()

        elif data == self.binds.get("restart"):
            self._cleanup_runtime_files()
            self.__exec_cmd(self.cmd_restart)
            self.get_application().quit()

        elif data == self.binds.get("shutdown"):
            self._cleanup_runtime_files()
            self.__exec_cmd(self.cmd_shutdown)
            self.get_application().quit()

        elif data == self.binds.get("suspend"):
            self._cleanup_runtime_files()
            self.__exec_cmd(self.cmd_suspend)
            self.get_application().quit()

        elif data == self.binds.get("hibernate"):
            self._cleanup_runtime_files()
            self.__exec_cmd(self.cmd_hibernate)
            self.get_application().quit()

        elif data == self.binds.get("lock"):
            if self.cmd_lock.startswith("betterlockscreen") and not fn.os.path.isdir(
                fn.home + "/.cache/betterlockscreen"
            ):
                if fn.os.path.isfile(self.wallpaper):
                    self.lbl_stat.set_markup(
                        _('<span size="x-large"><b>Caching lockscreen images for a faster locking next time</b></span>')
                    )
                    t = threading.Thread(target=fn.cache_bl, args=(self, GLib))
                    t.daemon = True
                    t.start()
                else:
                    self.lbl_stat.set_markup(
                        _('<span size="x-large"><b>Choose a wallpaper with archlinux-betterlockscreen</b></span>')
                    )
                    self.Ec.set_sensitive(True)
                    self.active = False
            else:
                self._cleanup_runtime_files()
                self.__exec_cmd(fn.resolve_lock_cmd(self.cmd_lock))
                self.get_application().quit()

        elif data == self.binds.get("settings"):
            self.themes.grab_focus()
            self.popover.popup()

        elif data == "light":
            self.popover2.popup()

        else:
            self._cleanup_runtime_files()
            self.get_application().quit()

    def __exec_cmd(self, cmdline):
        t = threading.Thread(target=lambda: fn.subprocess.Popen(cmdline, shell=True), daemon=True)
        t.start()

    def on_close(self, _widget):
        self._cleanup_runtime_files()
        self.get_application().quit()
        return False

    def message_box(self, message, title):
        dialog = Gtk.AlertDialog(message=title, detail=message)
        dialog.show(self)


class ArchLinuxLogoutApp(Gtk.Application):
    def __init__(self, settings_only=False):
        super().__init__(application_id="org.archlinux.logout", flags=Gio.ApplicationFlags.NON_UNIQUE)
        self.settings_only = settings_only

    def do_activate(self):
        TransparentWindow(self, settings_only=self.settings_only)


def signal_handler(sig, frame):
    print("\nArchLinux-Logout is Closing.")
    for path in ("/tmp/archlinux-logout.lock", "/tmp/archlinux-logout.pid"):
        try:
            fn.os.unlink(path)
        except Exception:
            pass
    app = Gtk.Application.get_default()
    if app:
        app.quit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)

    # Settings mode opens only the configuration window — it must bypass the
    # fullscreen-overlay lock-file singleton entirely (it never creates the lock).
    if "--settings" in sys.argv:
        app = ArchLinuxLogoutApp(settings_only=True)
        app.run(None)
    elif not fn.os.path.isfile("/tmp/archlinux-logout.lock"):
        try:
            with open("/tmp/archlinux-logout.pid", "w") as f:
                f.write(str(fn.os.getpid()))
        except PermissionError:
            print("[WARN]: Could not write /tmp/archlinux-logout.pid (permission denied)")
        app = ArchLinuxLogoutApp()
        app.run(sys.argv)
    else:
        print(
            "ArchLinux-logout did not close properly. Remove /tmp/archlinux-logout.lock with sudo."
        )
