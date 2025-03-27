import os
import threading
from concurrent.futures import ThreadPoolExecutor
import gi
import cairo  # Import Cairo correctly

os.environ["GDK_BACKEND"] = "x11"

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from search import SearchInFiles as search  # Import your search module


class SpotlightClone(Gtk.Window):
    def __init__(self):
        super().__init__(title="Spotlight Clone")
        self.set_default_size(600, 50)
        self.set_size_request(600, 50)
        screen = Gdk.Screen.get_default()
        monitor = screen.get_primary_monitor()
        geometry = screen.get_monitor_geometry(monitor)
        window_width, window_height = self.get_size()
        x = (geometry.width - window_width) // 2
        y = (geometry.height - window_height) // 2 - 100  
        self.move(x, y)
        self.set_decorated(False)
        
        # Enable transparency & allow input
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_accept_focus(True)
        self.set_can_focus(True)
        self.set_keep_above(True)

        # Thread pool for search
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Debounce timer
        self.debounce_timer = None

        # Dictionary to store search results
        self.search_results = {}

        # UI Setup
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        # Search Entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search...")
        self.search_entry.get_style_context().add_class("custom-search-entry")
        self.search_entry.connect("activate", self.close_window)
        self.search_entry.connect("key-press-event", self.on_key_press)
        vbox.pack_start(self.search_entry, False, False, 0)

        # File List Container
        self.file_title = Gtk.Label(label="File Results:")
        self.file_title.hide()
        self.file_title.get_style_context().add_class("title")

        self.file_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.file_list_box.get_style_context().add_class("file-list-box")
        self.file_list_box.hide()
  

         # Application List Container
        self.app_title = Gtk.Label(label="Applications Results:")
        self.app_title.hide()
        self.app_title.get_style_context().add_class("title")

        self.app_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.app_list_box.get_style_context().add_class("file-list-box")
        self.app_list_box.hide()

        # Pack the file list box into the main vbox
        vbox.pack_start(self.file_title, False, False, 0)  
        vbox.pack_start(self.file_list_box, True, True, 1)  
        vbox.pack_start(self.app_title, False, False, 0)
        vbox.pack_start(self.app_list_box, True, True, 1)


        # Apply CSS
        self.apply_styles()

        # Draw transparency
        self.connect("draw", self.draw_transparent_background)

        self.show_all()

    def apply_styles(self):
        """Apply CSS styles to the window."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window {
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 15px;
                outline: none;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                border: none;
            }
            .custom-search-entry {
                color: black;
                font-size: 22px;
                padding: 10px;
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.3);
                border: none;
                box-shadow: none;
            }
            .file-list-box {
                background-color: rgba(255, 255, 255, 0.6);
                padding: 10px;
                border-radius: 10px;
            }
            .title {
                color: white;
                font-size: 20px;
                margin: 10px;
            }
        """)
        style_context = self.get_style_context()
        style_context.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def draw_transparent_background(self, widget, cr):
        """Make window background fully transparent."""
        cr.set_source_rgba(1, 1, 1, 0)
        cr.set_operator(cairo.Operator.SOURCE)
        cr.paint()

    def on_key_press(self, widget, event):
        """Debounce search input and update results."""
        if event.keyval == Gdk.KEY_Escape:
            self.close_window()
            return

        if self.debounce_timer:
            self.debounce_timer.cancel()

        def debounce_search():
            search_text = widget.get_text()
            future_files = self.executor.submit(search.search_files, search_text)
            result_files = future_files.result() or {} 
            

            future_apps = self.executor.submit(search.search_application, search_text)
            result_apps = future_apps.result() or {} 
            GLib.idle_add(self.update_list, result_apps, result_files)

            

        self.debounce_timer = threading.Timer(0.3, debounce_search)
        self.debounce_timer.start()
        return False



    def update_list(self, results_apps, results_files):
        """Updates the file list safely from the main thread."""
        for child in self.file_list_box.get_children():
            self.file_list_box.remove(child)
        
        for child in self.app_list_box.get_children():
            self.app_list_box.remove(child)

        self.search_results_files = results_files  
        self.search_results_apps = results_apps


        if not results_files and not results_apps:
            self.hide_box()
            self.resize(600, 50) 
            return

        self.show_box()

        # Create buttons for files results
        for filename, filepath in self.search_results_files.items():
            button = Gtk.Button(label=filename)
            button.connect("clicked", self.open_file, filepath)
            self.file_list_box.pack_start(button, False, False, 0)
        
        for appname, appcommand in self.search_results_apps.items():
            button = Gtk.Button(label=appname)
            button.connect("clicked", self.run_apps, appcommand)
            self.app_list_box.pack_start(button, False, False, 0)


        self.resize(600, 300)
        self.show_all()
        return False

    # Opens the selected file
    def open_file(self, button, filepath):
        search.open_file(filepath)
        self.executor.shutdown(wait=False)
        Gtk.main_quit()

    # Opens the selected application.    
    def run_apps(self, button, command):
        search.run_applications(command)
        self.executor.shutdown(wait=False)
        Gtk.main_quit()

    # Closes the window and opens the first search result (if any)
    def close_window(self):
        if self.debounce_timer:
            self.debounce_timer.cancel()

        if self.search_results:
            first_key = next(iter(self.search_results))
            first_value = self.search_results[first_key]
            print(f"Opening file: {first_value}")
            search.open_file(first_value)
        else:
            print("No search results to open.")

        self.executor.shutdown(wait=False)
        Gtk.main_quit()

    def show_box(self):
        self.file_list_box.show()
        self.file_title.show()
        self.app_title.show()
        self.app_list_box.show()

    def hide_box(self):
        self.file_list_box.hide()
        self.file_title.hide()
        self.app_title.hide()
        self.app_list_box.hide()





# Run the application
win = SpotlightClone()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
