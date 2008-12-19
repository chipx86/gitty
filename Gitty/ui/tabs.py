from datetime import datetime

import gobject
import gtk

from Gitty.git.client import Client
from Gitty.git.commits import Commit
from Gitty.ui.commits import CommitsTree, ReferencesTree
from Gitty.ui.sourceview import SourceView


class ProjectTab(gtk.VBox):
    def __init__(self, path):
        gtk.VBox.__init__(self, False, 0)
        self.client = Client(path)

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
        def on_references_toggled(toggle):
            if toggle.get_active():
                self.refs_swin.show()
            else:
                self.refs_swin.hide()

        vbox = gtk.VBox(False, 6)

        buttonbox = gtk.HButtonBox()
        buttonbox.show()
        vbox.pack_start(buttonbox, False, False, 0)
        buttonbox.set_layout(gtk.BUTTONBOX_START)

        refs_button = gtk.ToggleButton("References")
        refs_button.show()
        buttonbox.pack_start(refs_button, False, False, 0)
        refs_button.set_active(True)
        refs_button.connect('toggled', on_references_toggled)

        paned = gtk.HPaned()
        paned.show()
        vbox.pack_start(paned, True, True, 0)
        paned.set_position(200) # XXX Hardcoding sucks

        # Build the references list
        self.refs_swin = gtk.ScrolledWindow()
        self.refs_swin.show()
        paned.pack1(self.refs_swin, False)
        self.refs_swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.refs_swin.set_shadow_type(gtk.SHADOW_IN)

        self.refs_tree = ReferencesTree()
        self.refs_tree.show()
        self.refs_swin.add(self.refs_tree)
        self.refs_tree.connect('reference_changed',
            lambda w, ref: self.commits_tree.select_reference(ref))

        # Build the commits list
        swin = gtk.ScrolledWindow()
        swin.show()
        paned.pack2(swin, True)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        swin.set_shadow_type(gtk.SHADOW_IN)

        self.commits_tree = CommitsTree()
        self.commits_tree.show()
        swin.add(self.commits_tree)

        self.commits_tree.connect('commit_changed', self.on_commit_changed)
        self.commits_tree.connect('references_changed',
                                  lambda w, refs: self.refs_tree.load(refs))

        self.commits_tree.update_commits()

        return vbox

    def __build_bottom_pane(self):
        vbox = gtk.VBox(False, 6)

        hbox = gtk.HBox(False, 6)
        hbox.show()
        vbox.pack_start(hbox, False, False, 0)

        label = gtk.Label("<b>SHA1 ID:</b>")
        label.show()
        hbox.pack_start(label, False, False, 0)
        label.set_use_markup(True)

        self.sha1_label = gtk.Label()
        self.sha1_label.show()
        hbox.pack_start(self.sha1_label, False, False, 0)
        self.sha1_label.set_max_width_chars(40)
        self.sha1_label.set_selectable(True)

        paned = gtk.HPaned()
        paned.show()
        vbox.pack_start(paned, True, True, 0)

        self.content_notebook = gtk.Notebook()
        self.content_notebook.show()
        paned.pack1(self.content_notebook, True)

        self.diff_viewer = SourceView()
        self.diff_viewer.show()
        self.content_notebook.append_page(self.diff_viewer, gtk.Label("Diff"))
        self.diff_viewer.set_mimetype("text/x-patch")

        self.old_version_view = SourceView()
        self.old_version_view.show()
        self.content_notebook.append_page(self.old_version_view,
                                          gtk.Label("Old Version"))

        self.new_version_view = SourceView()
        self.new_version_view.show()
        self.content_notebook.append_page(self.new_version_view,
                                          gtk.Label("New Version"))

        return vbox

    def on_commit_changed(self, widget, commit):
        self.sha1_label.set_text(commit.commit_sha1)
        self.diff_viewer.set_text(self.get_commit_contents(commit))

        self.old_version_view.set_text(self.get_commit_contents(commit))
        self.new_version_view.set_text(self.get_commit_contents(commit))

    def on_references_clicked(self, widget):
        pass


    def get_commit_contents(self, commit):
        diff = self.client.diff_tree(commit.commit_sha1, commit.parent_sha1[0])

        header = self.client.get_commit_header(commit.commit_sha1)

        contents  = "Author:    %s  %s\n" % (header["author"]["name"],
                                             header["author"]["time"])
        contents += "Committer: %s  %s\n" % (header["committer"]["name"],
                                             header["committer"]["time"])
        contents += "Parent:    %s (%s)\n" % (header["parent"], "")
        contents += "Child:     %s (%s)\n" % ("", "")
        contents += "Branch:    %s\n" % ("")

        contents += "\n%s\n\n" % header["message"]
        contents += diff

        return contents
