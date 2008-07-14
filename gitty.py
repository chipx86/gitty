#!/usr/bin/env python

import gobject
import gtk

from Gitty.ui.app import GittyWindow


if __name__ == "__main__":
    mainwin = GittyWindow()
    mainwin.show()
    mainwin.connect("destroy", lambda *w: gtk.main_quit())

    gtk.main()
