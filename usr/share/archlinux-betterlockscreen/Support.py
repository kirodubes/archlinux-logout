import gi
from Functions import os
from abl_i18n import _

gi.require_version('Gtk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf, Gdk  # noqa

base_dir = os.path.dirname(os.path.realpath(__file__))


class Support(Gtk.Window):

    def __init__(self, parent):
        super().__init__(title=_("Credits"))
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

        label = Gtk.Label()
        label.set_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_markup(
            _("Big thank you to our developers for their work on this project.\n"
              "<b>Brad Heffernan</b> is the driving force aka developer behind the Betterlockscreen GUI. "
              "With the help of <b>Erik Dubois</b> we were able to give our users an easy and efficient tool.")
        )

        # --- Logo ---
        logo = GdkPixbuf.Pixbuf().new_from_file_at_size(
            os.path.join(base_dir, 'images/archlinux.png'), 100, 100)
        logo_image = Gtk.Picture()
        logo_image.set_paintable(Gdk.Texture.new_for_pixbuf(logo))

        label.set_margin_start(10)
        label.set_margin_end(10)
        hbox.append(label)

        vbox.append(logo_image)
        vbox.append(hbox)
