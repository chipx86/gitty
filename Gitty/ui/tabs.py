from datetime import datetime

import gobject
import gtk

from Gitty.git.commits import Commit
from Gitty.ui.commits import CommitsTree


class ProjectTab(gtk.VBox):
    def __init__(self, path):
        gtk.VBox.__init__(self, False, 0)
        self.path = path

        self.set_border_width(6)

        paned = gtk.VPaned()
        paned.show()
        self.pack_start(paned, True, True, 0)

        widget = self.__build_top_pane()
        widget.show()
        paned.pack1(widget, True)

        widget = self.__build_bottom_pane()
        widget.show()
        paned.pack2(widget, False)

    def __build_top_pane(self):
        vbox = gtk.VBox(False, 6)

        swin = gtk.ScrolledWindow()
        swin.show()
        vbox.pack_start(swin, True, True, 0)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        swin.set_shadow_type(gtk.SHADOW_IN)

        self.commits_tree = CommitsTree()
        self.commits_tree.show()
        swin.add(self.commits_tree)

        hbox = gtk.HBox(False, 6)
        hbox.show()
        vbox.pack_start(hbox, False, False, 0)

        label = gtk.Label("<b>SHA1 ID:</b>")
        label.show()
        hbox.pack_start(label, False, False, 0)
        label.set_use_markup(True)

        self.sha1_label = gtk.Label("7128dffd91967e921f478fabde373a2b6e492cfd")
        self.sha1_label.show()
        hbox.pack_start(self.sha1_label, False, False, 0)
        self.sha1_label.set_max_width_chars(40)
        self.sha1_label.set_selectable(True)

        return vbox

    def __build_bottom_pane(self):
        paned = gtk.HPaned()
        return paned
