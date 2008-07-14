import gtk
import os


from Gitty.ui.tabs import ProjectTab


ui_def = """
<ui>
 <menubar name="MenuBar">
  <menu action="GittyMenu">
   <menuitem action="QuitAction" />
  </menu>
 </menubar>
</ui>
"""

class GittyWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.set_title("Gitty")
        self.set_default_size(800, 600)

        self.ui_manager = gtk.UIManager()
        self.ui_manager.insert_action_group(self.__create_action_group(), 0)
        self.ui_manager.add_ui_from_string(ui_def)

        main_vbox = gtk.VBox(0, False)
        main_vbox.show()
        self.add(main_vbox)

        menubar = self.ui_manager.get_widget("/MenuBar")
        menubar.show()
        main_vbox.pack_start(menubar, False, False, 0)

        self.notebook = gtk.Notebook()
        self.notebook.show()
        main_vbox.pack_start(self.notebook, True, True, 0)

        self.new_tab(os.getcwd())

    def new_tab(self, path):
        tab = ProjectTab(path)
        tab.show()
        self.notebook.append_page(tab, gtk.Label(path))

    def __create_action_group(self):
        action_group = gtk.ActionGroup("GittyActions")
        action_group.add_actions((
            ("GittyMenu", None, "_Gitty"),
            ("QuitAction", gtk.STOCK_QUIT, "_Quit", "<control>Q", "Quit",
             self.__on_quit),
        ),)

        return action_group

    def __on_quit(self, action):
        self.destroy()
