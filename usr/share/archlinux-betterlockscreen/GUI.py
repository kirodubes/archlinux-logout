# =================================================================
# =                  Author: Brad Heffernan                       =
# =================================================================

import os
import sys

import abl_i18n as i18n
from abl_i18n import _


def _language_controls(self, Gtk):
    codes = [None, *i18n.available()]
    labels = [_("System ({language})").format(language=i18n.name(i18n.SYSTEM))]
    labels.extend(i18n.name(code) for code in codes[1:])
    dropdown = Gtk.DropDown.new_from_strings(labels)
    dropdown.set_tooltip_text(_("Language"))
    dropdown.set_selected(codes.index(i18n.chosen()))

    note = Gtk.Label(label="", xalign=0)
    note.set_visible(False)
    restart = Gtk.Button(label=_("Restart now"), visible=False)

    def on_language_changed(_dropdown, _pspec):
        code = codes[dropdown.get_selected()]
        i18n.save_choice(code)
        changed = (code or i18n.SYSTEM) != (i18n.ACTIVE or i18n.SYSTEM)
        note.set_text(_("Saved. The app shows the new language when it starts again.") if changed else "")
        note.set_visible(changed)
        restart.set_visible(changed)

    def on_restart(_widget):
        argv = [sys.executable, os.path.abspath(sys.argv[0]), *sys.argv[1:]]
        i18n.restore_environment()
        os.execv(sys.executable, argv)

    dropdown.connect("notify::selected", on_language_changed)
    restart.connect("clicked", on_restart)
    return dropdown, note, restart


def GUI(self, Gtk, GdkPixbuf, Gdk, th, fn):

    self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
    self.vbox.set_margin_start(10)
    self.vbox.set_margin_end(10)
    self.vbox.set_margin_top(10)
    self.vbox.set_margin_bottom(10)
    self.set_child(self.vbox)

    hbox_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    hbox5 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    hbox6 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    hbox7 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    hbox8 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

    # =======================================================
    #                       TOP BAR (content header)
    # =======================================================
    title = Gtk.Label(label=_("ArchLinux BetterLockScreen"), xalign=0)
    title.set_name("blstitle")
    title.set_hexpand(True)

    version = fn.get_betterlockscreen_version()
    ver_text = _("betterlockscreen v{version}").format(version=version) if version[:1].isdigit() else _(
        "betterlockscreen {version}"
    ).format(version=version)
    lbl_version = Gtk.Label(label=ver_text)
    lbl_version.add_css_class("info-label")
    lbl_version.set_valign(Gtk.Align.CENTER)

    btn_support = Gtk.Button(label=_("♥ Support"))
    btn_support.set_tooltip_text(_("Support development"))
    btn_support.add_css_class("support-button")
    btn_support.connect("clicked", self.on_support_clicked)

    btn_quit = Gtk.Button(label=_("Quit"))
    btn_quit.connect("clicked", self.close)

    language_dropdown, language_note, btn_restart = _language_controls(self, Gtk)
    hbox_header.append(title)
    hbox_header.append(lbl_version)
    hbox_header.append(language_dropdown)
    hbox_header.append(btn_restart)
    hbox_header.append(btn_support)
    hbox_header.append(btn_quit)

    # =======================================================
    #                       App Notifications
    # =======================================================

    self.notification_revealer = Gtk.Revealer()
    self.notification_revealer.set_reveal_child(False)

    self.notification_label = Gtk.Label()
    self.notification_label.set_hexpand(True)

    notification_bg = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    notification_bg.set_size_request(-1, 30)
    notification_bg.add_css_class("notification-bar")
    notification_bg.append(self.notification_label)

    css_notif = Gtk.CssProvider()
    css_notif.load_from_data(
        b".notification-bar { background-color: #1a1a1a; }"
        b"label#blstitle { font-size: 20px; font-weight: 600; }"
        b"label.info-label { color: alpha(currentColor, 0.65); font-size: 11px; }"
        b".support-button { color: #e0567a; }"
        b".support-button:hover { background-color: alpha(#e0567a, 0.18); }"
    )
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css_notif,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )

    self.notification_revealer.set_child(notification_bg)

    language_note.set_margin_start(10)
    language_note.set_margin_end(10)
    self.vbox.append(hbox_header)
    self.vbox.append(language_note)
    self.vbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

    hbox1.append(self.notification_revealer)
    self.notification_revealer.set_hexpand(True)

    # ==========================================================
    #                       LOCATIONS
    # ==========================================================
    lbl = Gtk.Label(label=_("Enter Location"))
    self.loc.set_size_request(280, 0)
    btnbrowse = Gtk.Button(label="...")
    btnsearch = Gtk.Button(label=_("Load"))
    btndefault = Gtk.Button(label=_("Default"))

    btnsearch.connect("clicked", self.on_load_clicked)
    btndefault.connect("clicked", self.on_default_clicked)
    btnbrowse.connect("clicked", self.on_browse_clicked)

    btnsearch.set_size_request(130, 0)

    presets = fn.preset_folders()
    dd_presets = Gtk.DropDown.new_from_strings(presets)
    dd_presets.set_tooltip_text(_("Known wallpaper folders - pick one to load it"))
    # notify::selected only fires on a change, so start empty unless the current folder is a preset;
    # otherwise the preselected entry could never be picked
    current = self.loc.get_text()
    dd_presets.set_selected(presets.index(current) if current in presets else Gtk.INVALID_LIST_POSITION)
    dd_presets.connect("notify::selected", self.on_preset_selected)

    lbl.set_margin_start(10)
    lbl.set_margin_end(0)
    hbox6.append(lbl)
    hbox6.append(dd_presets)
    hbox6.append(self.loc)
    btnbrowse.set_margin_start(5)
    hbox6.append(btnbrowse)
    hbox6.append(btnsearch)

    btndefault.set_halign(Gtk.Align.END)
    btndefault.set_hexpand(True)
    hbox6.append(btndefault)

    # ==========================================================
    #                       SEARCH
    # ==========================================================
    lblS = Gtk.Label(label=_("Search: "))
    self.search.set_size_request(180, 0)
    btnsearcher = Gtk.Button(label=_("Search"))

    btnsearcher.connect("clicked", self.on_search_clicked)
    btnsearcher.set_size_request(130, 0)

    hbox8.append(lblS)
    hbox8.append(self.search)
    hbox8.append(btnsearcher)

    # ==========================================================
    #                       APPLY BUTTON
    # ==========================================================
    lbl_lock_hint = Gtk.Label(label=_("To lock the screen: press Super + X, then K"))
    lbl_lock_hint.add_css_class("info-label")
    lbl_lock_hint.set_halign(Gtk.Align.END)
    lbl_lock_hint.set_hexpand(True)
    hbox2.append(lbl_lock_hint)

    # Spins while betterlockscreen builds its lockscreen images, which takes several seconds
    self.apply_spinner = Gtk.Spinner()
    self.apply_spinner.set_tooltip_text(_("Creating lockscreen images..."))
    hbox2.append(self.apply_spinner)

    self.btnset = Gtk.Button(label=_("Apply Image"))
    self.btnset.connect("clicked", self.on_apply_clicked)
    self.btnset.set_halign(Gtk.Align.END)
    hbox2.append(self.btnset)

    # ==========================================================
    #                       CREDITS
    # ==========================================================
    credits = Gtk.Button(label=_("Credits"))
    credits.connect("clicked", self.on_support_clicked)
    hbox2.prepend(credits)

    # ==========================================================
    #                       STATUS
    # ==========================================================
    hbox5.append(self.status)
    self.status.set_hexpand(True)

    # ==========================================================
    #                       BLUR SLIDER
    # ==========================================================
    ad1 = Gtk.Adjustment(value=100, lower=0, upper=100,
                         step_increment=1, page_increment=100, page_size=0)

    self.blur = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad1)
    self.blur.set_digits(0)
    self.blur.set_hexpand(True)
    self.blur.set_draw_value(True)
    self.blur.set_size_request(100, 0)
    self.blur.set_valign(Gtk.Align.START)

    label = Gtk.Label(label=_("Blur intensity"))
    hbox7.append(label)
    hbox7.append(self.blur)
    self.blur.set_hexpand(True)

    hbox2.prepend(hbox7)

    # ==========================================================
    #                       PACK TO WINDOW
    # ==========================================================

    self.vbox.append(hbox1)          # notify
    self.vbox.append(hbox6)          # load row
    self.vbox.append(hbox8)          # search row
    self.vbox.append(self.hbox3)     # images
    self.hbox3.set_vexpand(True)
    self.hbox3.set_hexpand(True)
    self.vbox.append(hbox5)          # status
    self.vbox.append(hbox2)          # settings row
