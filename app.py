import os
import threading
from concurrent.futures import ThreadPoolExecutor
import gi
import cairo  # Import Cairo correctly

os.environ["GDK_BACKEND"] = "x11"

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

from search import SearchInFiles as search  # Import your search module
from gi.repository import GdkPixbuf

screen = Gdk.Screen.get_default()
monitor = screen.get_primary_monitor()
geometry = screen.get_monitor_geometry(monitor)
window_width, window_height = 900, 50
Y_CENTER = geometry.y + (geometry.height - window_height) // 2


class SpotlightClone(Gtk.Window):
    def __init__(self):
        # Add icon cache dictionaries
        self.file_icon_cache = {}
        self.app_icon_cache = {}
        self.pixbuf_cache = {}  
        # Initialize the SpotlightClone window with UI setup and configurations.
        super().__init__(title="Spotlight")
        self.set_default_size(900, 50)
        self.set_size_request(900, 50)
        screen = self.get_screen()
        monitor = screen.get_primary_monitor()
        geometry = screen.get_monitor_geometry(monitor)  # has x, y, width, height
        window_width, window_height = self.get_size()
        # center on that monitor:
        self.x = geometry.x + (geometry.width - window_width) // 2
        self.y = geometry.y + (geometry.height - window_height) // 2
        self.move(self.x, self.y)
        self.set_decorated(False)
        self.first_app_command = ''
        self.set_size_request(600, 50)
        
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
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Debounce timer
        self.debounce_timer = None

        # Dictionary to store search results
        self.search_results = {}

        # UI Setup
        vbox_general = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox_general)

        # Search Entry
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search...")
        self.search_entry.get_style_context().add_class("custom-search-entry")
        self.search_entry.connect("activate", self.close_window)
        self.search_entry.connect("key-press-event", self.on_key_press)
        vbox_general.pack_start(self.search_entry, False, False, 0)

        # File List Container
        self.file_title = Gtk.Label(label="File Results:")
        self.file_title.hide()
        self.file_title.get_style_context().add_class("title")

        self.file_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)  # Reduced spacing
        self.file_list_box.get_style_context().add_class("file-list-box")
        self.file_list_box.hide()

        # Directory List Container
        self.dir_title = Gtk.Label(label="Directories Results:")
        self.dir_title.hide()
        self.dir_title.get_style_context().add_class("title")

        self.dir_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)  # Reduced spacing
        self.dir_list_box.get_style_context().add_class("file-list-box")
        self.dir_list_box.hide()

        # Application List Container
        self.app_title = Gtk.Label(label="Applications Results:")
        self.app_title.hide()
        self.app_title.get_style_context().add_class("title")

        self.app_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)  # Reduced spacing
        self.app_list_box.get_style_context().add_class("file-list-box")
        self.app_list_box.hide()

        # Pack the file list box into the main vbox
        self.vbox_list_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.vbox_list_container.pack_start(self.app_title, False, False, 0)
        self.vbox_list_container.pack_start(self.app_list_box, True, True, 1)
        self.vbox_list_container.pack_start(self.file_title, False, False, 0)
        self.vbox_list_container.pack_start(self.file_list_box, True, True, 1)
        self.vbox_list_container.pack_start(self.dir_title, False, False, 0)
        self.vbox_list_container.pack_start(self.dir_list_box, True, True, 1)
        

        # Add vbox_list_container to vbox_general
        vbox_general.pack_start(self.vbox_list_container, True, True, 1)

        # Apply CSS
        self.apply_styles()

        # Draw transparency
        self.connect("draw", self.draw_transparent_background)

        self.show_all()
        self.vbox_list_container.hide()

    
    def apply_styles(self):
        # Apply CSS styles to the window.
        css_provider = Gtk.CssProvider()
        css_file_path = os.path.join(os.path.dirname(__file__), "assets/styles.css")
        with open(css_file_path, "rb") as css_file:
            css_provider.load_from_data(css_file.read())
        style_context = self.get_style_context()
        style_context.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def draw_transparent_background(self, widget, cr):
        # Make window background fully transparent.
        cr.set_source_rgba(1, 1, 1, 0)
        cr.set_operator(cairo.Operator.SOURCE)
        cr.paint()

    def on_key_press(self, widget, event):
        # Debounce search input and update results.
        if event.keyval == Gdk.KEY_Escape:
            self.close_window(widget)
            return

        if event.keyval == Gdk.KEY_Return:
            search.run_applications(self.first_app_command)
            return

        if self.debounce_timer:
            self.debounce_timer.cancel()

        def debounce_search():
            search_text = widget.get_text()
            if self.executor._shutdown:
                return

            future_files = self.executor.submit(search.search_files, search_text)
            result_files = future_files.result() or {}

            future_dirs = self.executor.submit(search.search_dirs, search_text)
            result_dirs = future_dirs.result() or {}

            future_apps = self.executor.submit(search.search_application, search_text)
            result_apps = future_apps.result() or {}

            GLib.idle_add(self.update_list, result_apps, result_files, result_dirs)
            self.first_app_command = result_apps.get(next(iter(result_apps)), '')  # Get the first app command


        self.debounce_timer = threading.Timer(0.5, debounce_search)  # Wrap event in a tuple
        self.debounce_timer.start()

        
        return False



    def update_list(self, results_apps, results_files, results_dirs):
        # Clear existing widgets
        self.file_list_box.foreach(lambda w: w.destroy())
        self.dir_list_box.foreach(lambda w: w.destroy()) 
        self.app_list_box.foreach(lambda w: w.destroy())
        
        self.search_results_files = results_files  
        self.search_results_apps = results_apps
        self.search_results_dirs = results_dirs

        # Check if we have any results
        if not (results_apps or results_files or results_dirs):
            self.hide_box()
            self.resize(900, 50)
            self.move(self.x, Y_CENTER)
            return False

        # Update window position
        self.redefine_position(results_apps, results_files, results_dirs)
        
        # Create and add app widgets
        for appname, appcommand in results_apps.items():
            widget = self.create_app_widget(appname, appcommand)
            self.app_list_box.pack_start(widget, False, False, 0)

        # Create and add file widgets
        for filename, filepath in results_files.items():
            widget = self.create_file_widget(filename, filepath)
            self.file_list_box.pack_start(widget, False, False, 0)

        # Create and add directory widgets
        for dir_name, dir_path in results_dirs.items():
            widget = self.create_dir_widget(dir_name, dir_path)
            self.dir_list_box.pack_start(widget, False, False, 0)

        self.show_box()
        self.resize(900, 300)
        self.show_all()
        return False

    def open_file(self, widget, event, filepath):
        # Opens the selected file.
        search.open_file(filepath)
        self.executor.shutdown(wait=False)
        Gtk.main_quit()

    def open_dir(self, widget, event, dir_path):
        # Opens the selected directory.
        search.open_directory(dir_path)
        self.executor.shutdown(wait=False)
        Gtk.main_quit()

    def run_apps(self, widget, event, app_name):
        # Opens the selected application.
        search.run_applications(app_name)
        self.executor.shutdown(wait=False)
        Gtk.main_quit()

    def close_window(self, widget, event=None):
        # Closes the window and opens the first search result (if any).
        if self.debounce_timer:
            self.debounce_timer.cancel()

        if self.search_results:
            first_key = next(iter(self.search_results))
            first_value = self.search_results[first_key]
            print(f"Opening file: {first_value}")
            search.open_file(first_value)
        else:
            print("No search results to open.")

        if not self.executor._shutdown:  # Ensure the executor is not already shut down
            self.executor.shutdown(wait=False)

        Gtk.main_quit()

    def show_box(self):
        # Show the file and application result boxes.
        self.vbox_list_container.show()

    def hide_box(self):
        # Hide the file and application result boxes.
        self.vbox_list_container.hide()

    def get_type_of_file(self, filename):
        # Check cache first
        if filename in self.file_icon_cache:
            return self.file_icon_cache[filename]
            
        icon_path = 'assets/file_icons/txt.png' # Default
        
        # Determine icon path based on extension
        for ext, icon in {
            '.py': 'python.png',
            '.txt': 'txt.png',
            '.cpp': 'cpp.png',
            '.c': 'cpp.png',
            '.png': 'image.png',
            '.jpg': 'image.png',
            '.jpeg': 'image.png',
            '.pdf': 'pdf.png',
            '.json': 'json.png',
            '.html': 'html.png',
            '.js': 'js.png',
            '.vue': 'vue.png'
        }.items():
            if filename.endswith(ext):
                icon_path = f'assets/file_icons/{icon}'
                break
                
        self.file_icon_cache[filename] = icon_path
        return icon_path
    
    def get_app_icon(self, app_name):
        # Returns the icon path for the given application name.
        if(app_name == 'firefox'):
            return 'assets/app_icons/firefox.png'
        elif(app_name == 'visual studio code'):
            return 'assets/app_icons/visual-studio-code.png'
        elif(app_name == 'whatsapp'):
            return 'assets/app_icons/whatsapp.png'
        elif(app_name == 'emacs'):
            return 'assets/app_icons/emacs.png'
        elif(app_name == 'appunti'):
            return 'assets/app_icons/appunti.png'
        elif(app_name == 'spotify'):
            return 'assets/app_icons/spotify.png'
        elif(app_name == 'overleaf'):
            return 'assets/app_icons/overleaf.png'
        elif(app_name == 'zoom'):  
            return 'assets/app_icons/zoom.png'
        elif(app_name == 'gaia-app'):
            return 'assets/app_icons/gaia.png'
        elif(app_name == 'gaia-web'):
            return 'assets/app_icons/gaia.png'
        elif(app_name == 'moodle'):
            return 'assets/app_icons/moodle.png'
        elif(app_name == 'telegram'):
            return 'assets/app_icons/telegram.png'
        elif(app_name == 'postman'):
            return 'assets/app_icons/postman.png'
        elif(app_name == 'gmail'):
            return 'assets/app_icons/gmail.png'
        elif (app_name == 'studio'):
            return 'assets/app_icons/appunti.png'
        elif (app_name == 'notetom'):
            return 'assets/app_icons/notetom.png'

        
        return 'assets/app_icons/app.png'

    def redefine_position(self, results_apps, results_files, results_dirs):
        # Dynamically adjust self.y without modifying the constant center value
        if (len(results_apps) > 5 or len(results_files) > 5 or len(results_dirs) > 5):
            self.move(self.x, self.y - 500)
        else:
            self.move(self.x, Y_CENTER)

    def create_app_widget(self, appname, appcommand):
        event_box_app = Gtk.EventBox()
        box_app = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        box_app.get_style_context().add_class("file-list-box")

        appname_label = Gtk.Label(label=appname)
        appname_label.set_halign(Gtk.Align.CENTER)
        appname_label.get_style_context().add_class("filename-text")
        appname_label.set_valign(Gtk.Align.CENTER)

        img_path = self.get_app_icon(appname)
        
        # Cache pixbufs
        if img_path not in self.app_icon_cache:
            self.app_icon_cache[img_path] = GdkPixbuf.Pixbuf.new_from_file_at_size(
                os.path.join(os.path.dirname(__file__), img_path), 23, 23
            )
        
        image = Gtk.Image.new_from_pixbuf(self.app_icon_cache[img_path])
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)

        box_app.pack_start(image, False, False, 0)
        box_app.pack_start(appname_label, False, False, 0)
        event_box_app.add(box_app)
        event_box_app.connect("button-press-event", self.run_apps, appcommand)

        return event_box_app

    def create_file_widget(self, filename, filepath):
        event_box = Gtk.EventBox()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        box.get_style_context().add_class("file-list-box")

        filename_label = Gtk.Label(label=filename)
        filename_label.set_halign(Gtk.Align.CENTER)
        filename_label.get_style_context().add_class("filename-text")
        filename_label.set_valign(Gtk.Align.CENTER)

        path_txt = filepath.replace("/home/simone", "")
        if len(filepath) > 60:
            path_txt = '...' + filepath[30:]
        filepath_label = Gtk.Label(label=path_txt)
        filepath_label.get_style_context().add_class("filepath-text")
        filepath_label.set_halign(Gtk.Align.END)

        img_path = self.get_type_of_file(filename)
        if img_path not in self.pixbuf_cache:
            self.pixbuf_cache[img_path] = GdkPixbuf.Pixbuf.new_from_file_at_size(
                os.path.join(os.path.dirname(__file__), img_path), 23, 23
            )
        
        image = Gtk.Image.new_from_pixbuf(self.pixbuf_cache[img_path])
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)

        box.pack_start(image, False, False, 0)
        box.pack_start(filename_label, False, False, 0)
        box.pack_start(filepath_label, False, False, 0)
        event_box.add(box)
        event_box.connect("button-press-event", self.open_file, filepath)

        return event_box

    def create_dir_widget(self, dir_name, dir_path):
        event_box = Gtk.EventBox()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        box.get_style_context().add_class("file-list-box")

        dir_name_label = Gtk.Label(label=dir_name)
        dir_name_label.set_halign(Gtk.Align.CENTER)
        dir_name_label.get_style_context().add_class("filename-text")
        dir_name_label.set_valign(Gtk.Align.CENTER)

        path_txt = dir_path.replace("/home/simone", "")
        if len(dir_path) > 60:
            path_txt = '...' + dir_path[30:]
        dirpath_label = Gtk.Label(label=path_txt)
        dirpath_label.get_style_context().add_class("filepath-text")
        dirpath_label.set_halign(Gtk.Align.END)

        img_path = 'assets/folder.png'
        if img_path not in self.pixbuf_cache:
            self.pixbuf_cache[img_path] = GdkPixbuf.Pixbuf.new_from_file_at_size(
                os.path.join(os.path.dirname(__file__), img_path), 23, 23
            )
        
        image = Gtk.Image.new_from_pixbuf(self.pixbuf_cache[img_path])
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)

        box.pack_start(image, False, False, 0)
        box.pack_start(dir_name_label, False, False, 0)
        box.pack_start(dirpath_label, False, False, 0)
        event_box.add(box)
        event_box.connect("button-press-event", self.open_dir, dir_path)

        return event_box

    def __del__(self):
        self.icon_executor.shutdown(wait=False)
        self.executor.shutdown(wait=False)




# Run the application
win = SpotlightClone()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
