import gtk
import pango

try:
    import gtksourceview
except ImportError:
    gtksourceview = None


class DiffViewer(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self, False, 6)

        swin = gtk.ScrolledWindow()
        swin.show()
        self.pack_start(swin, True, True, 0)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swin.set_shadow_type(gtk.SHADOW_IN)

        if gtksourceview:
            self.buffer = gtksourceview.SourceBuffer()
            slm = gtksourceview.SourceLanguagesManager()
            gsl = slm.get_language_from_mime_type("text/x-patch")
            self.buffer.set_highlight(True)
            self.buffer.set_language(gsl)
            sourceview = gtksourceview.SourceView(self.buffer)
        else:
            self.buffer = gtk.TextBuffer()
            sourceview = gtk.TextView(self.buffer)

        sourceview.show()
        swin.add(sourceview)
        sourceview.set_editable(False)
        sourceview.modify_font(pango.FontDescription("Monospace"))

    def set_diff(self, diff):
        self.buffer.set_text(diff.contents)
