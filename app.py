import os
import threading
from concurrent.futures import ThreadPoolExecutor
import gi

os.environ["GDK_BACKEND"] = "x11"

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib  # Added GLib
from search import SearchInFiles as search


class SpotlightClone(Gtk.Window):
    def __init__(self):
        super().__init__(title="Spotlight Clone")
        self.set_default_size(600, 300)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)

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
        self.file_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.file_list_box.get_style_context().add_class("file-list-box")

        vbox.pack_start(self.file_list_box, True, True, 0)

        # Apply CSS
        self.apply_styles()

        self.show_all()

    def apply_styles(self):
        """Apply CSS styles to the window."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window {
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 30px;
                outline: none; 
                box-shadow: none;
                border: none; 
            }
            .custom-search-entry {
                color: black;
                font-size: 22px;
                padding: 5px;
                outline: none; 
                box-shadow: none;
                border: none; 
            }
            .file-list-box {
                background-color: rgba(255, 255, 255, 0.95);
                padding: 10px;
                border-radius: 20px;
            }
        """)
        style_context = self.get_style_context()
        style_context.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_key_press(self, widget, event):
        """Debounce search input and update results."""
        if self.debounce_timer:
            self.debounce_timer.cancel()

        def debounce_search():
            search_text = widget.get_text()
            future = self.executor.submit(search.search_files, search_text)
            result = future.result() or {}  # Ensure result is a dictionary
            # **Fix: Update UI safely from the main thread**
            GLib.idle_add(self.update_file_list, result)

        self.debounce_timer = threading.Timer(0.3, debounce_search)
        self.debounce_timer.start()
        return False

    def update_file_list(self, results):
        """Updates the file list safely from the main thread."""
        # Clear previous results
        for child in self.file_list_box.get_children():
            self.file_list_box.remove(child)

        self.search_results = results  # Store results

        # Create buttons for search results
        for filename, filepath in self.search_results.items():
            button = Gtk.Button(label=filename)
            button.connect("clicked", self.open_file, filepath)
            self.file_list_box.pack_start(button, False, False, 0)

        self.show_all()
        return False  

    def open_file(self, button, filepath):
        """Opens the selected file."""
        os.system(f'xdg-open "{filepath}"')
        self.executor.shutdown(wait=False)
        Gtk.main_quit()

    def close_window(self, widget):
        """Closes the window and opens the first search result (if any)."""
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


# Run the application
win = SpotlightClone()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
