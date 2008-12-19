import gtk
import pango

try:
    import gtksourceview
except ImportError:
    gtksourceview = None


class SourceView(gtk.ScrolledWindow):
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)

        if gtksourceview:
            self.buffer = gtksourceview.SourceBuffer()
            self.buffer.set_highlight(True)
            sourceview = gtksourceview.SourceView(self.buffer)
        else:
            self.buffer = gtk.TextBuffer()
            sourceview = gtk.TextView(self.buffer)

        sourceview.show()
        self.add(sourceview)
        sourceview.set_editable(False)
        sourceview.modify_font(pango.FontDescription("Monospace"))

    def set_mimetype(self, mimetype):
        if gtksourceview:
            slm = gtksourceview.SourceLanguagesManager()
            gsl = slm.get_language_from_mime_type(mimetype)
            self.buffer.set_language(gsl)

    def set_text(self, text):
        self.buffer.set_text(unicode(text))
