# =====================================================
#        Authors Brad Heffernan and Erik Dubois
# =====================================================

import os
import sys

import alo_i18n as i18n
from alo_i18n import N_, _


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


# Funding channels — GitHub Sponsors first (~100% payout). Keep in sync with
# kiro-website .github/FUNDING.yml if those change.
_FUNDING = [
    ("GitHub Sponsors", "https://github.com/sponsors/erikdubois", _("best value — almost all goes to the project")),
    ("Ko-fi", "https://ko-fi.com/erikdubois", _("buy a coffee — one-off tip")),
    ("Patreon", "https://www.patreon.com/kiroproject", _("membership tiers + perks")),
    ("YouTube membership", "https://www.youtube.com/@ErikDubois/join", _("join on YouTube")),
    ("PayPal", "https://www.paypal.me/erikdubois", _("direct one-off")),
]


def _open_url(Gtk, parent, url):
    Gtk.UriLauncher.new(url).launch(parent, None, None)


def _show_support_dialog(Gtk, parent):
    dlg = Gtk.Window(title=_("Support Kiro"), transient_for=parent, modal=True)
    dlg.set_default_size(440, -1)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    for side in ("start", "end", "top", "bottom"):
        getattr(box, f"set_margin_{side}")(18)

    heading = Gtk.Label()
    heading.set_xalign(0.0)
    heading.set_markup(_("<b>Support Kiro</b>"))
    box.append(heading)

    intro = Gtk.Label()
    intro.set_xalign(0.0)
    intro.set_wrap(True)
    intro.set_max_width_chars(52)
    intro.set_label(
        _("Kiro and its tools are built by one person, for the community — and kept free. "
          "If ArchLinux Logout saves you time, a little support keeps the work going. "
          "Thank you for being here.")
    )
    box.append(intro)

    for name, url, note in _FUNDING:
        btn = Gtk.Button()
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        lbl = Gtk.Label()
        lbl.set_xalign(0.0)
        lbl.set_markup(f"<b>{name}</b>")
        sub = Gtk.Label(label=note)
        sub.set_xalign(0.0)
        content.append(lbl)
        content.append(sub)
        btn.set_child(content)
        btn.connect("clicked", lambda _w, u=url: _open_url(Gtk, dlg, u))
        box.append(btn)

    close = Gtk.Button(label=_("Close"))
    close.set_halign(Gtk.Align.END)
    close.connect("clicked", lambda _w: dlg.close())
    box.append(close)

    dlg.set_child(box)
    dlg.present()


def _settings_card(Gtk, title, child):
    """Wrap a settings group in a titled frame (the standalone window's 'card' look)."""
    child.set_margin_start(10)
    child.set_margin_end(10)
    child.set_margin_top(8)
    child.set_margin_bottom(10)
    title_lbl = Gtk.Label()
    title_lbl.set_markup(f"<b>{title}</b>")
    frame = Gtk.Frame()
    frame.set_label_widget(title_lbl)
    frame.set_child(child)
    frame.set_margin_bottom(12)
    return frame


def SettingsPanel(self, Gtk, fn):
    """Build the settings widget tree, shared by the overlay popover and the standalone settings window."""
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    vbox.set_margin_start(10)
    vbox.set_margin_end(10)
    vbox.set_margin_top(10)
    vbox.set_margin_bottom(10)

    lbl_opacity = Gtk.Label()
    lbl_opacity.set_markup(_("<b>Opacity:</b>"))
    lbl_opacity.set_halign(Gtk.Align.START)
    lbl_opacity.set_valign(Gtk.Align.END)

    lbl_icon_size = Gtk.Label()
    lbl_icon_size.set_markup(_("<b>Icon size:</b>"))
    lbl_icon_size.set_halign(Gtk.Align.START)
    lbl_icon_size.set_valign(Gtk.Align.END)

    lbl_theme = Gtk.Label()
    lbl_theme.set_markup(_("<b>Theme:</b>"))
    lbl_theme.set_halign(Gtk.Align.START)
    lbl_theme.set_valign(Gtk.Align.CENTER)

    lbl_font_size = Gtk.Label()
    lbl_font_size.set_markup(_("<b>Font size:</b>"))
    lbl_font_size.set_halign(Gtk.Align.START)
    lbl_font_size.set_valign(Gtk.Align.END)

    try:
        vals = self.opacity * 100
        ad1 = Gtk.Adjustment(value=vals, lower=0, upper=100, step_increment=5, page_increment=10, page_size=0)
    except Exception:
        ad1 = Gtk.Adjustment(value=60, lower=0, upper=100, step_increment=5, page_increment=10, page_size=0)

    self.hscale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad1)
    self.hscale.set_digits(0)
    self.hscale.set_draw_value(True)
    self.hscale.set_value_pos(Gtk.PositionType.TOP)
    self.hscale.set_hexpand(True)
    self.hscale.set_size_request(150, 0)
    self.hscale.set_valign(Gtk.Align.START)

    try:
        vals = self.font
        ad1f = Gtk.Adjustment(value=vals, lower=0, upper=80, step_increment=5, page_increment=10, page_size=0)
    except Exception:
        ad1f = Gtk.Adjustment(value=60, lower=0, upper=80, step_increment=5, page_increment=10, page_size=0)

    self.fonts = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad1f)
    self.fonts.set_digits(0)
    self.fonts.set_draw_value(True)
    self.fonts.set_value_pos(Gtk.PositionType.TOP)
    self.fonts.set_hexpand(True)
    self.fonts.set_size_request(150, 0)
    self.fonts.set_valign(Gtk.Align.START)

    try:
        valsi = self.icon
        ad1i = Gtk.Adjustment(value=valsi, lower=0, upper=300, step_increment=5, page_increment=10, page_size=0)
    except Exception:
        ad1i = Gtk.Adjustment(value=60, lower=0, upper=300, step_increment=5, page_increment=10, page_size=0)

    self.icons = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=ad1i)
    self.icons.set_digits(0)
    self.icons.set_draw_value(True)
    self.icons.set_value_pos(Gtk.PositionType.TOP)
    self.icons.set_hexpand(True)
    self.icons.set_size_request(150, 0)
    self.icons.set_valign(Gtk.Align.START)

    lists = fn._get_themes()
    theme_model = Gtk.StringList.new(lists)
    self.themes = Gtk.DropDown(model=theme_model)
    active = lists.index(self.theme) if self.theme in lists else 0
    self.themes.set_selected(active)

    btn_save_settings = Gtk.Button(label=_("Save Settings"))
    btn_save_settings.connect("clicked", self.on_save_clicked)
    self.btn_save_settings = btn_save_settings

    hbox_opacity = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    hbox_opacity.append(lbl_opacity)
    hbox_opacity.append(self.hscale)

    hbox_icon_size = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    hbox_icon_size.append(lbl_icon_size)
    hbox_icon_size.append(self.icons)

    hbox_font_size = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    hbox_font_size.append(lbl_font_size)
    hbox_font_size.append(self.fonts)

    lbl_show_text = Gtk.Label()
    lbl_show_text.set_markup(_("<b>Show text:</b>"))
    lbl_show_text.set_halign(Gtk.Align.START)
    lbl_show_text.set_valign(Gtk.Align.CENTER)

    self.chk_show_text = Gtk.CheckButton()
    self.chk_show_text.set_active(self.show_text)

    hbox_show_text = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
    hbox_show_text.append(lbl_show_text)
    hbox_show_text.append(self.chk_show_text)

    # --- Button visibility checkboxes ---
    _all_buttons = ["cancel", "shutdown", "restart", "suspend", "hibernate", "lock", "logout"]
    _btn_display = {
        "cancel": N_("Cancel"), "shutdown": N_("Shut down"), "restart": N_("Restart"),
        "suspend": N_("Suspend"), "hibernate": N_("Hibernate"), "lock": N_("Lock"), "logout": N_("Log out"),
    }

    buttons_grid = Gtk.Grid()
    buttons_grid.set_column_spacing(16)
    buttons_grid.set_row_spacing(4)

    for i, btn_name in enumerate(_all_buttons):
        chk = Gtk.CheckButton(label=_(_btn_display[btn_name]))
        chk.set_active(btn_name in self.buttons)
        setattr(self, f"chk_btn_{btn_name}", chk)
        buttons_grid.attach(chk, i % 2, i // 2, 1, 1)

    settings_only = getattr(self, "settings_only", False)

    if not settings_only:
        # --- Overlay popover: compact flat grid (Save lives inside) ---
        lbl_buttons_section = Gtk.Label()
        lbl_buttons_section.set_markup(_("<b>Buttons:</b>"))
        lbl_buttons_section.set_halign(Gtk.Align.START)
        lbl_buttons_section.set_valign(Gtk.Align.CENTER)

        vbox_buttons_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox_buttons_section.append(lbl_buttons_section)
        vbox_buttons_section.append(buttons_grid)

        hbox_theme = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        hbox_theme.append(lbl_theme)
        hbox_theme.append(self.themes)

        hbox_save = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        hbox_save.append(btn_save_settings)

        grid_settings = Gtk.Grid()
        grid_settings.set_row_spacing(20)
        grid_settings.attach(hbox_opacity, 0, 1, 1, 1)
        grid_settings.attach(hbox_icon_size, 0, 2, 1, 1)
        grid_settings.attach(hbox_font_size, 0, 3, 1, 1)
        grid_settings.attach(hbox_show_text, 0, 4, 1, 1)
        grid_settings.attach(vbox_buttons_section, 0, 5, 1, 1)
        grid_settings.attach(hbox_theme, 0, 6, 1, 1)
        grid_settings.attach(hbox_save, 0, 7, 1, 1)
        vbox.append(grid_settings)
        return vbox

    # --- Standalone settings window: header + cards + about ---
    hbox_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    hbox_header.set_margin_bottom(8)

    lbl_app_title = Gtk.Label(label=_("ArchLinux Logout Settings"), xalign=0)
    lbl_app_title.set_name("title")
    lbl_app_title.set_hexpand(True)

    btn_support = Gtk.Button(label=_("♥ Support"))
    btn_support.set_tooltip_text(_("Support Kiro's development"))
    btn_support.add_css_class("support-button")
    btn_support.connect("clicked", lambda _w: _show_support_dialog(Gtk, self))

    btn_quit = Gtk.Button(label=_("Quit"))
    btn_quit.connect("clicked", self.on_exit_clicked)

    language_dropdown, language_note, btn_restart = _language_controls(self, Gtk)
    hbox_header.append(lbl_app_title)
    hbox_header.append(language_dropdown)
    hbox_header.append(btn_restart)
    hbox_header.append(btn_support)
    hbox_header.append(btn_quit)
    vbox.append(hbox_header)
    vbox.append(language_note)
    vbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

    appearance = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    appearance.append(hbox_opacity)
    appearance.append(hbox_icon_size)
    appearance.append(hbox_font_size)
    appearance.append(hbox_show_text)
    vbox.append(_settings_card(Gtk, _("Appearance"), appearance))

    vbox.append(_settings_card(Gtk, _("Buttons"), buttons_grid))

    theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    theme_box.append(self.themes)
    vbox.append(_settings_card(Gtk, _("Theme"), theme_box))

    lbl_about = Gtk.Label()
    lbl_about.set_wrap(True)
    lbl_about.set_xalign(0.0)
    lbl_about.set_margin_top(4)
    lbl_about.add_css_class("info-label")
    lbl_about.set_markup(
        _("<b>What is this?</b>\n"
          "ArchLinux Logout is the power screen shown when you log out — the row of buttons "
          "for Shutdown, Restart, Suspend, Hibernate, Lock, Logout and Cancel.\n\n"
          "<b>What you can change here</b>\n"
          "• <b>Opacity</b> — how see-through the logout screen's background is\n"
          "• <b>Icon size</b> — how big the power-button icons are\n"
          "• <b>Font size</b> — the size of the button labels\n"
          "• <b>Show text</b> — whether labels appear under the icons\n"
          "• <b>Buttons</b> — which power actions are offered (tick the ones you want)\n"
          "• <b>Theme</b> — the visual style and icon set of the logout screen\n\n"
          "Click <b>Save Settings</b> to apply. Changes take effect the next time the "
          "logout screen opens.")
    )
    vbox.append(lbl_about)

    return vbox


def GUI(self, Gtk, GdkPixbuf, working_dir, os, Gdk, fn):
    def apply_icon_widget_size(container, image, size):
        container.set_halign(Gtk.Align.CENTER)
        container.set_valign(Gtk.Align.START)
        container.set_vexpand(False)
        container.set_hexpand(False)
        image.set_size_request(size, size)
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.START)
        image.set_vexpand(False)
        image.set_hexpand(False)

    def build_icon_widget(svg_path, size):
        picture = Gtk.Picture()
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        picture.set_can_shrink(True)
        picture.set_size_request(size, size)
        self._pending_pixbufs.append((svg_path, picture, size))
        return picture

    def normalize_button_label(label):
        label.set_halign(Gtk.Align.CENTER)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_xalign(0.5)
        label.set_wrap(False)
        label.set_single_line_mode(True)
        label.set_margin_top(0)

    def normalize_button_card(card):
        card_width = max(self.main_icon_size + 48, 150)
        card.set_halign(Gtk.Align.CENTER)
        card.set_valign(Gtk.Align.START)
        card.set_size_request(card_width, -1)
        card.set_margin_top(0)
        card.set_margin_bottom(0)

    mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    mainbox2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
    topbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    lblbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

    lbl = Gtk.Label(label="")

    self.lbl_stat = Gtk.Label()

    lblbox.append(lbl)
    lblbox.append(self.lbl_stat)

    overlayFrame = Gtk.Overlay()
    overlayFrame.set_child(lblbox)
    overlayFrame.add_overlay(topbox)
    overlayFrame.add_overlay(mainbox)

    self.set_child(overlayFrame)

    # --- Settings button (gear icon) ---
    self.Eset = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.Eset.set_name("settings")

    eset_click = Gtk.GestureClick()
    eset_click.connect(
        "pressed",
        lambda g, n, x, y: self.on_click(self.Eset, self.binds["settings"]),
    )
    self.Eset.add_controller(eset_click)

    eset_motion = Gtk.EventControllerMotion()
    eset_motion.connect(
        "enter", lambda c, x, y: self.on_mouse_in(self.Eset, self.binds["settings"])
    )
    eset_motion.connect(
        "leave", lambda c: self.on_mouse_out(self.Eset, self.binds["settings"])
    )
    self.Eset.add_controller(eset_motion)

    self.imageset = build_icon_widget(
        os.path.join(working_dir, "configure.svg"), self.aux_icon_size)
    apply_icon_widget_size(self.Eset, self.imageset, self.aux_icon_size)
    self.Eset.append(self.imageset)

    # --- Light/wallpaper button ---
    self.Elig = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.Elig.set_name("light")

    elig_click = Gtk.GestureClick()
    elig_click.connect(
        "pressed", lambda g, n, x, y: self.on_click(self.Elig, "light")
    )
    self.Elig.add_controller(elig_click)

    elig_motion = Gtk.EventControllerMotion()
    elig_motion.connect("enter", lambda c, x, y: self.on_mouse_in(self.Elig, "light"))
    elig_motion.connect("leave", lambda c: self.on_mouse_out(self.Elig, "light"))
    self.Elig.add_controller(elig_motion)

    self.imagelig = build_icon_widget(
        os.path.join(working_dir, "light.svg"), self.aux_icon_size)
    apply_icon_widget_size(self.Elig, self.imagelig, self.aux_icon_size)
    self.Elig.append(self.imagelig)

    # --- Button cards: each card IS the gesture target (no inner wrapper box) ---
    # self.Esh/Er/etc. point directly to the card so set_sensitive works on the whole card

    def make_card(bind_key):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        click = Gtk.GestureClick()
        click.connect("pressed", lambda g, n, x, y: self.on_click(card, bind_key))
        card.add_controller(click)
        motion = Gtk.EventControllerMotion()
        motion.connect("enter", lambda c, x, y: self.on_mouse_in(card, bind_key))
        motion.connect("leave", lambda c: self.on_mouse_out(card, bind_key))
        card.add_controller(motion)
        return card

    self.Esh  = make_card(self.binds["shutdown"])
    self.Er   = make_card(self.binds["restart"])
    self.Es   = make_card(self.binds["suspend"])
    self.Elk  = make_card(self.binds["lock"])
    self.El   = make_card(self.binds["logout"])
    self.Ec   = make_card(self.binds["cancel"])
    self.Eh   = make_card(self.binds["hibernate"])

    hbox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
    hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)

    # Map button names to (card, image_attr, label_attr, label_text, svg_name)
    button_defs = {
        "shutdown": (self.Esh,  "imagesh",  "lbl1", _("Shut down ({key})").format(key=self.binds["shutdown"]), "shutdown"),
        "restart":  (self.Er,   "imager",   "lbl2", _("Restart ({key})").format(key=self.binds["restart"]), "restart"),
        "suspend":  (self.Es,   "images",   "lbl3", _("Suspend ({key})").format(key=self.binds["suspend"]), "suspend"),
        "lock":     (self.Elk,  "imagelk",  "lbl4", _("Lock ({key})").format(key=self.binds["lock"]), "lock"),
        "logout":   (self.El,   "imagelo",  "lbl5", _("Log out ({key})").format(key=self.binds["logout"]), "logout"),
        "cancel":   (self.Ec,   "imagec",   "lbl6", _("Cancel ({key})").format(key=self.binds["cancel"]), "cancel"),
        "hibernate":(self.Eh,   "imageh",   "lbl7", _("Hibernate ({key})").format(key=self.binds["hibernate"]), "hibernate"),
    }

    for button in self.buttons:
        if button not in button_defs:
            continue
        card, img_attr, lbl_attr, lbl_text, svg = button_defs[button]

        img = build_icon_widget(
            os.path.join(working_dir, "themes/" + self.theme + f"/{svg}.svg"),
            self.main_icon_size)
        apply_icon_widget_size(card, img, self.main_icon_size)
        setattr(self, img_attr, img)

        lbl = Gtk.Label()
        lbl.set_markup(f'<span size="{str(self.font)}000">{lbl_text}</span>')
        lbl.set_name("lbl")
        normalize_button_label(lbl)
        lbl.set_valign(Gtk.Align.CENTER)
        setattr(self, lbl_attr, lbl)
        lbl.set_visible(self.show_text)

        icon_overlay = Gtk.Overlay()
        icon_overlay.set_child(img)
        icon_overlay.add_overlay(lbl)
        icon_overlay.set_size_request(self.main_icon_size, self.main_icon_size)
        icon_overlay.set_halign(Gtk.Align.CENTER)
        icon_overlay.set_valign(Gtk.Align.START)
        card.append(icon_overlay)

    # Convenience references for labels used in on_mouse_in/out
    # (set to empty label if button not shown, to avoid AttributeError)
    _dummy = Gtk.Label()
    for attr in ("lbl1","lbl2","lbl3","lbl4","lbl5","lbl6","lbl7"):
        if not hasattr(self, attr):
            setattr(self, attr, _dummy)

    card_map = {
        "shutdown": self.Esh,
        "cancel":   self.Ec,
        "restart":  self.Er,
        "suspend":  self.Es,
        "lock":     self.Elk,
        "logout":   self.El,
        "hibernate":self.Eh,
    }

    button_widgets = []
    for button in self.buttons:
        if button == "lock" and fn.sessionw:
            continue
        if button in card_map:
            button_widgets.append(card_map[button])

    split_index = len(button_widgets) if len(button_widgets) <= 5 else (len(button_widgets) + 1) // 2
    first_row = button_widgets[:split_index]
    second_row = button_widgets[split_index:]

    for widget in button_widgets:
        normalize_button_card(widget)
        widget.set_margin_start(10)
        widget.set_margin_end(10)

    for widget in first_row:
        hbox1.append(widget)

    for widget in second_row:
        hbox2.append(widget)

    hbox1.set_halign(Gtk.Align.CENTER)
    hbox2.set_halign(Gtk.Align.CENTER)

    mainbox2.set_halign(Gtk.Align.CENTER)
    mainbox2.append(hbox1)
    if second_row:
        mainbox2.append(hbox2)

    mainbox.set_valign(Gtk.Align.CENTER)
    mainbox.append(mainbox2)

    topbox.set_halign(Gtk.Align.START)
    topbox.set_valign(Gtk.Align.START)
    topbox.set_margin_top(16)
    topbox.set_margin_start(16)
    topbox.append(self.Elig)
    topbox.append(self.Eset)

    # --- Settings popover ---
    self.popover = Gtk.Popover()
    self.popover2 = Gtk.Popover()

    self.popover.set_child(SettingsPanel(self, Gtk, fn))
    self.popover.set_position(Gtk.PositionType.TOP)

    hbox8 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

    plbl = Gtk.Label()
    plbl.set_markup(
        _('<span size="large">You can change the lockscreen wallpaper\nwith <b>Archlinux BetterLockScreen</b></span>')
    )
    plbl.set_halign(Gtk.Align.END)
    hbox8.append(plbl)

    self.popover2.set_child(hbox8)
    self.popover2.set_position(Gtk.PositionType.TOP)

    # Set popover parents (GTK4 replaces set_relative_to)
    self.popover.set_parent(self.Eset)
    self.popover2.set_parent(self.Elig)
