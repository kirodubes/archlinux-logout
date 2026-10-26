import gi
import Functions
from Functions import os

gi.require_version('Gtk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf, Gdk  # noqa

base_dir = os.path.dirname(os.path.realpath(__file__))


class Support(Gtk.Window):

    def __init__(self, parent):
        super().__init__(title="Credits - Support Development")
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(550, 100)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        self.set_child(vbox)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        label = Gtk.Label()
        label.set_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_markup(
            "Big thank you to our developers for their work on this project.\n"
            "<b>Brad Heffernan</b> is the driving force aka developer behind the Betterlockscreen GUI. \n"
            "With the help of <b>Erik Dubois</b> we were able to give our users an easy and efficient tool. \n"
            "If you want to thank and support <b>Brad</b> personally for his initiative and efforts "
            "then you can do so by following the links."
        )

        # --- PayPal button ---
        pbpp = GdkPixbuf.Pixbuf().new_from_file_at_size(
            os.path.join(base_dir, 'images/paypal.png'), 54, 54)
        ppimage = Gtk.Picture()
        ppimage.set_paintable(Gdk.Texture.new_for_pixbuf(pbpp))

        paypal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        paypal_click = Gtk.GestureClick()
        paypal_click.connect(
            "pressed",
            lambda g, n, x, y: self._open_link("https://PayPal.Me/heffserver")
        )
        paypal_box.add_controller(paypal_click)
        paypal_box.set_tooltip_text("Buy BradHeff a coffee")
        paypal_box.append(ppimage)

        # --- Logo ---
        logo = GdkPixbuf.Pixbuf().new_from_file_at_size(
            os.path.join(base_dir, 'images/archlinux.png'), 100, 100)
        logo_image = Gtk.Picture()
        logo_image.set_paintable(Gdk.Texture.new_for_pixbuf(logo))

        label.set_margin_start(10)
        label.set_margin_end(10)
        hbox.append(label)

        paypal_box.set_margin_start(10)
        hbox2.append(paypal_box)

        hbox3.set_halign(Gtk.Align.CENTER)
        hbox3.append(hbox2)

        vbox.append(logo_image)
        vbox.append(hbox)

        # pack end equivalents — just append in reverse order with END align
        hbox3.set_valign(Gtk.Align.END)
        hbox3.set_vexpand(True)
        vbox.append(hbox3)

    def _open_link(self, link):
        t = Functions.threading.Thread(target=self._weblink, args=(link,))
        t.daemon = True
        t.start()

    def _weblink(self, link):
        Functions.subprocess.call(
            ["bash", "-c", "exo-open --launch webbrowser " + link], shell=False
        )
