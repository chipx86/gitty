import cairo
import gobject
import gtk
import math
import pango
from xml.sax.saxutils import escape

from Gitty.git.commits import Commit, CommitGraph, Reference


class ReferencesCellRenderer(gtk.GenericCellRenderer):
    __gproperties__ = {
        "references": (gobject.TYPE_PYOBJECT, "References", "References",
                       gobject.PARAM_READWRITE),
    }

    def __init__(self):
        gtk.GenericCellRenderer.__init__(self)
        self.references = []

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def build_box_layout(self, text, widget):
        layout = widget.create_pango_layout("")
        layout.set_markup("<small>%s</small>" % text)
        layout.set_single_paragraph_mode(True)
        return layout

    def draw_text(self, layout, window, widget, expose_area,
                  x_offset, y_offset, state=gtk.STATE_NORMAL):
        widget.get_style().paint_layout(
            window, state, True, expose_area,
            widget, "cellrenderertext",
            x_offset, y_offset, layout)

    def draw_box(self, ctx, window, widget, expose_area,
                 text, x_offset, y_offset, fill_color, stroke_color):
        layout = self.build_box_layout(text, widget)
        text_width, text_height = layout.get_pixel_size()
        width = text_width + 10
        height = text_height + 3

        ctx.rectangle(x_offset + 0.5, y_offset + 0.5, width, height)
        ctx.set_source_rgb(fill_color[0], fill_color[1], fill_color[2])
        ctx.fill_preserve()

        ctx.set_source_rgb(stroke_color[0], stroke_color[1],
                           stroke_color[2])
        ctx.stroke()

        self.draw_text(layout, window, widget, expose_area,
                       x_offset + (width  - text_width)  / 2,
                       y_offset + (height - text_height) / 2)

        return width + 1

    def render_reference(self, ctx, window, widget, expose_area,
                         ref, x_offset, y_offset):
        parts = ref.name.split("/")

        ctx.set_line_width(1)

        if parts[0] == "heads":
            x_offset += self.draw_box(ctx, window, widget, expose_area,
                                      parts[1], x_offset, y_offset,
                                      (0.5, 1, 0.5), (0.2, 0.65, 0.2))
        elif parts[0] == "remotes":
            x_offset += self.draw_box(ctx, window, widget, expose_area,
                                      "/".join(parts[:-1]), x_offset, y_offset,
                                      (0.96, 0.78, 0.48),
                                      (0.56, 0.35, 0.01))
            x_offset += self.draw_box(ctx, window, widget, expose_area,
                                      parts[-1], x_offset - 1, y_offset,
                                      (0.5, 1, 0.5), (0.2, 0.65, 0.2))
        elif parts[0] == "tags":
            layout = self.build_box_layout(parts[1], widget)
            text_width, text_height = layout.get_pixel_size()
            width = text_width + 14
            height = text_height + 4

            x1 = x_offset + 0.5
            x2 = x1 + width
            y1 = y_offset + 0.5
            y2 = y1 + height

            ctx.move_to(x1, y1 + height / 2)
            ctx.line_to(x1 + 5, y1)
            ctx.line_to(x2, y1)
            ctx.line_to(x2, y2)
            ctx.line_to(x1 + 5, y2)
            ctx.line_to(x1, y1 + height / 2)

            ctx.set_source_rgb(1.00, 0.91, 0.51)
            ctx.fill_preserve()

            ctx.set_source_rgb(0.87, 0.73, 0.1)
            ctx.stroke()

            self.draw_text(layout, window, widget, expose_area,
                           x_offset + (width  - text_width)  / 2 + 2,
                           y_offset + (height - text_height) / 2)

            x_offset += width + 1
        elif parts[0] == "stash":
            x_offset += self.draw_box(ctx, window, widget, expose_area,
                                      parts[0], x_offset, y_offset,
                                      (0.9, 0.9, 0.9), (0.2, 0.2, 0.2))
        else:
            return (False, x_offset)

        return (True, x_offset)


    def on_render(self, window, widget, bg_area, cell_area, expose_area, flags):
        ctx = window.cairo_create()
        ctx.rectangle(bg_area.x, bg_area.y, bg_area.width, bg_area.height)
        ctx.clip()

        x_offset = cell_area.x + 1
        y_offset = cell_area.y + 1

        # Draw the tags and branches
        for ref in self.references:
            self.render_reference(ctx, window, widget, expose_area,
                                  ref, x_offset, y_offset)


    def on_get_size(self, widget, cell_area=None):
        layout = self.build_box_layout("", widget)
        text_width, text_height = layout.get_pixel_size()

        names_len = 0

        for ref in self.references:
            names_len += len(ref.name)

        width = names_len
        height = text_height + 3

        return (0, 0, width, height)


class CommitCellRenderer(ReferencesCellRenderer):
    __gproperties__ = {
        "commit": (gobject.TYPE_PYOBJECT, "Commit", "Commit",
                   gobject.PARAM_READWRITE),
    }

    def __init__(self):
        ReferencesCellRenderer.__init__(self)
        self.commit = None
        self._box_size = None

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

        if pspec.name == "commit":
            self.set_property("references", value.references)


    def on_render(self, window, widget, bg_area, cell_area, expose_area, flags):
        ctx = window.cairo_create()
        ctx.rectangle(bg_area.x, bg_area.y, bg_area.width, bg_area.height)
        ctx.clip()

        box_size = self.__get_box_size(widget)

        ctx.set_line_width(box_size / 8)
        ctx.set_line_cap(cairo.LINE_CAP_SQUARE)

        bg_area_y2 = bg_area.y + bg_area.height

        # Draw the lines into the cell
        for start, end, color in self.commit.in_lines:
            ctx.move_to(cell_area.x + box_size * start + box_size / 2,
                        bg_area.y - bg_area.height / 2)

            if start - end > 1:
                ctx.line_to(cell_area.x + box_size * start, bg_area.y)
                ctx.line_to(cell_area.x + box_size * end + box_size, bg_area.y)
            elif start - end < -1:
                ctx.line_to(cell_area.x + box_size * start + box_size,
                            bg_area.y)
                ctx.line_to(cell_area.x + box_size * end, bg_area.y)

            ctx.line_to(cell_area.x + box_size * end + box_size / 2,
                        bg_area.y + bg_area.height / 2)

            self.set_color(ctx, color, 0, 0.65)
            ctx.stroke()

        # Draw the lines out of the cell
        for start, end, color in self.commit.out_lines:
            ctx.move_to(cell_area.x + box_size * start + box_size / 2,
                        bg_area.y + bg_area.height / 2)

            if start - end > 1:
                ctx.line_to(cell_area.x + box_size * start, bg_area_y2)
                ctx.line_to(cell_area.x + box_size * end + box_size, bg_area_y2)
            elif start - end < -1:
                ctx.line_to(cell_area.x + box_size * start + box_size,
                            bg_area_y2)
                ctx.line_to(cell_area.x + box_size * end, bg_area_y2)

            ctx.line_to(cell_area.x + box_size * end + box_size / 2,
                        bg_area.y + bg_area.height * 1.5)

            self.set_color(ctx, color, 0, 0.65)
            ctx.stroke()

        # Draw the revision node in the right column
        column, color = self.commit.node
        x_offset = cell_area.x + box_size * column + box_size / 2
        ctx.arc(x_offset, cell_area.y + cell_area.height / 2,
                box_size / 4, 0, 2 * math.pi)

        self.set_color(ctx, color, 0, 0.5)
        ctx.stroke_preserve()

        self.set_color(ctx, color, 0.5, 1)
        ctx.fill()

        #x_offset = box_size * column + box_size
        #y_offset = (cell_area.height - text_height) / 2

        line_y = cell_area.y + cell_area.height / 2
        x_offset += box_size / 4 + 1
        y_offset = cell_area.y + 1

        self.commit.ref_boxes = []

        # Draw the tags and branches
        for ref in self.commit.references:
            # Draw the line to the box
            ctx.set_line_width(box_size / 8)
            ctx.move_to(x_offset, line_y)
            x_offset += box_size / 2
            ctx.line_to(x_offset, line_y)
            self.set_color(ctx, color, 0, 0.5)
            ctx.stroke()

            parts = ref.name.split("/")

            box = {
                'ref': ref.name,
                'type': parts[0],
                'x': x_offset - cell_area.x,
                'y': y_offset - cell_area.y,
                'width': 0,
                'height': cell_area.height,
            }

            known, x_offset = self.render_reference(ctx, window, widget,
                                                    expose_area, ref,
                                                    x_offset, y_offset)

            if known:
                box['width'] = x_offset - box['x']
                self.commit.ref_boxes.append(box)


        layout = self.__build_layout(widget)
        text_width, text_height = layout.get_pixel_size()
        x_offset += 10
        y_offset = cell_area.y + (cell_area.height - text_height) / 2

        if flags & gtk.CELL_RENDERER_SELECTED:
            if widget.is_focus():
                state = gtk.STATE_SELECTED
            else:
                state = gtk.STATE_ACTIVE
        else:
            state = gtk.STATE_NORMAL

        self.draw_text(layout, window, widget, expose_area,
                       x_offset, y_offset, state)

    def on_get_size(self, widget, cell_area=None):
        box_size = self.__get_box_size(widget)

        cols = self.commit.node[0]
        for start, end, color in self.commit.in_lines + self.commit.out_lines:
            col = int(max(cols, start, end))

        x, y, w, h = super(CommitCellRenderer, self).on_get_size(widget,
                                                                 cell_area)

        w += box_size * (cols + 1)

        return (x, y, w, h)

    def __build_layout(self, widget):
        layout = widget.create_pango_layout("")
        layout.set_markup("<small>%s</small>" % escape(self.commit.message))
        layout.set_single_paragraph_mode(True)
        return layout

    def set_color(self, ctx, color, bg, fg):
        colors = [
            (1, 0, 0),
            (1, 1, 0),
            (0, 1, 0),
            (0, 1, 1),
            (0, 0, 1),
            (1, 0, 1),
        ]

        color %= len(colors)
        ctx.set_source_rgb((colors[color][0] * fg) or bg,
                           (colors[color][1] * fg) or bg,
                           (colors[color][2] * fg) or bg)

    def __get_box_size(self, widget):
        if not self._box_size:
            pango_ctx = widget.get_pango_context()
            font_desc = widget.get_style().font_desc
            metrics = pango_ctx.get_metrics(font_desc)

            ascent = pango.PIXELS(metrics.get_ascent())
            descent = pango.PIXELS(metrics.get_descent())

            self._box_size = ascent + descent + 6

        return self._box_size


class CommitsTree(gtk.TreeView):
    __gsignals__ = {
        'commit_changed': (gobject.SIGNAL_RUN_FIRST,
                           gobject.TYPE_NONE,
                           (gobject.TYPE_PYOBJECT,)),
        'references_changed': (gobject.SIGNAL_RUN_FIRST,
                               gobject.TYPE_NONE,
                               (gobject.TYPE_PYOBJECT,)),
    }

    COLUMN_COMMIT = 0
    COLUMN_AUTHOR = 1
    COLUMN_DATE = 2

    def __init__(self):
        self.model = gtk.ListStore(gobject.TYPE_PYOBJECT, # Commit
                                   gobject.TYPE_STRING,   # Author
                                   gobject.TYPE_STRING)   # Date

        gtk.TreeView.__init__(self, self.model)

        self.selected_commit = None
        self.references = {}

        column = gtk.TreeViewColumn("Commit", CommitCellRenderer(),
                                    commit=self.COLUMN_COMMIT)
        column.set_resizable(True)
        column.set_expand(True)
        self.append_column(column)

        column = gtk.TreeViewColumn("Author", gtk.CellRendererText(),
                                    markup=self.COLUMN_AUTHOR)
        column.set_resizable(True)
        self.append_column(column)

        column = gtk.TreeViewColumn("Date", gtk.CellRendererText(),
                                    markup=self.COLUMN_DATE)
        column.set_resizable(True)
        #column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        self.append_column(column)

        self.connect("button-press-event", self.on_button_press)
        self.get_selection().connect("changed", self.on_selection_changed)

        self.set_search_equal_func(self.__search_equal_func)
        self.set_search_column(self.COLUMN_COMMIT)

        self.graph = CommitGraph()

    def update_commits(self):
        self.model.clear()
        self.references = {}

        for commit in self.graph.get_commits():
            i = commit.author.find("<")
            author_name = commit.author[0:i - 1]
            iter = self.model.append((
                commit,
                "<small>%s</small>" % escape(author_name),
                "<small>%s</small>" % escape(commit.date)
            ))

            for ref in commit.references:
                self.references[ref] = iter;

        self.emit('references_changed', self.references.keys())

        self.queue_resize()

    def select_reference(self, ref):
        if ref in self.references:
            iter = self.references[ref]
            self.get_selection().select_iter(iter)
            self.scroll_to_cell(self.model.get_path(iter), use_align=True,
                                row_align=0.5)

    def on_button_press(self, widget, event):
        if event.button == 3:
            path, col, cell_x, cell_y = self.get_path_at_pos(int(event.x),
                                                             int(event.y))
            self.set_cursor(path, col, 0)

            commit = self.model.get(self.model.get_iter(path),
                                    self.COLUMN_COMMIT)[0]

            if commit:
                # We got the commit. See if we clicked a ref.
                for ref in commit.ref_boxes:
                    print "Comparing %d, %d to %d - %d, %d - %d" % \
                        (cell_x, cell_y, ref['x'], ref['x'] + ref['width'],
                         ref['y'], ref['y'] + ref['height'])

                    if (ref['x'] <= cell_x <= ref['x'] + ref['width'] and
                        ref['y'] <= cell_y <= ref['y'] + ref['height']):
                        print ref
                        break

            return True

        return False

    def on_selection_changed(self, selection):
        i = selection.get_selected()[1]

        if i:
            commit = self.model.get(i, self.COLUMN_COMMIT)[0]

            if commit != self.selected_commit:
                self.selected_commit = commit
                self.emit('commit_changed', commit)

    def __search_equal_func(self, model, column, key, iter):
        commit = model.get(iter, column)[0]
        assert isinstance(commit, Commit)

        # Oddly, we return False to indicate a match.
        return not commit.message.lower().startswith(key.lower())


class ReferencesTree(gtk.TreeView):
    __gsignals__ = {
        'reference_changed': (gobject.SIGNAL_RUN_FIRST,
                              gobject.TYPE_NONE,
                              (gobject.TYPE_PYOBJECT,)),
    }

    def __init__(self):
        self.model = gtk.ListStore(gobject.TYPE_PYOBJECT) # Commit
        gtk.TreeView.__init__(self, self.model)

        column = gtk.TreeViewColumn("References", ReferencesCellRenderer(),
                                    references=0)
        self.append_column(column)

        self.set_headers_visible(False)
        self.set_search_equal_func(self.__search_equal_func)
        self.set_search_column(0)

        self.get_selection().connect("changed", self.on_selection_changed)

    def load(self, references):
        self.model.clear()

        for reference in references:
            self.model.append(([reference],))

        self.queue_resize()

    def on_selection_changed(self, selection):
        i = selection.get_selected()[1]

        if i:
            reference = self.model.get(i, 0)[0]
            self.emit('reference_changed', reference[0])

    def __search_equal_func(self, model, column, key, iter):
        commit = model.get(iter, column)[0]
        assert isinstance(commit, Commit)

        # Oddly, we return False to indicate a match.
        return not key.lower() in \
               "/".join([ref.name.lower() for ref in commit.references])
