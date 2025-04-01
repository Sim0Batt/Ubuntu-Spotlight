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
window_width, window_height = 600, 50
Y_CENTER = (geometry.height - window_height) // 2 


class SpotlightClone(Gtk.Window):
    def __init__(self):
        # Initialize the SpotlightClone window with UI setup and configurations.
        super().__init__(title="Spotlight Clone")
        self.set_default_size(900, 50)
        self.set_size_request(900, 50)
        screen = Gdk.Screen.get_default()
        monitor = screen.get_primary_monitor()
        geometry = screen.get_monitor_geometry(monitor)
        window_width, window_height = self.get_size()
        self.x = (geometry.width - window_width) // 2
        self.y = (geometry.height - window_height) // 2 
        self.move(self.x, self.y)
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
        self.vbox_list_container.pack_start(self.file_title, False, False, 0)
        self.vbox_list_container.pack_start(self.file_list_box, True, True, 1)
        self.vbox_list_container.pack_start(self.dir_title, False, False, 0)
        self.vbox_list_container.pack_start(self.dir_list_box, True, True, 1)
        self.vbox_list_container.pack_start(self.app_title, False, False, 0)
        self.vbox_list_container.pack_start(self.app_list_box, True, True, 1)

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

        self.debounce_timer = threading.Timer(0.3, debounce_search)
        self.debounce_timer.start()
        return False



    def update_list(self, results_apps, results_files, results_dirs):
        # Updates the file and application lists safely from the main thread.
        for child in self.file_list_box.get_children():
            self.file_list_box.remove(child)
        
        for child in self.dir_list_box.get_children():
            self.dir_list_box.remove(child)

        for child in self.app_list_box.get_children():
            self.app_list_box.remove(child)

        self.search_results_files = results_files  
        self.search_results_apps = results_apps
        self.search_results_dirs = results_dirs

        self.redefine_position(self.search_results_apps, self.search_results_files, self.search_results_dirs)

        if not self.search_results_files and not self.search_results_apps and not self.search_results_dirs:
            self.hide_box()
            self.resize(600, 50)
            self.move(self.x, Y_CENTER)
            return

        self.show_box()

        

        img_path = 'assets/file_icons/txt.png'

        # Create box for files results
        for filename, filepath in self.search_results_files.items():

            event_box_files = Gtk.EventBox()
            box_files = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            box_files.get_style_context().add_class("file-list-box")

            filename_label = Gtk.Label(label=filename)  # Use keyword argument for label
            filename_label.set_halign(Gtk.Align.CENTER)  
            filename_label.get_style_context().add_class("filename-text")
            filename_label.set_halign(Gtk.Align.CENTER)
            filename_label.set_valign(Gtk.Align.CENTER) 
            filepath_label = Gtk.Label(label=filepath.replace("/home/user_name", ""))  # Use keyword argument for label
            filepath_label.get_style_context().add_class("filepath-text")
            filepath_label.set_halign(Gtk.Align.END)  # Align to the left

            
            img_path = self.get_type_of_file(filename)
            
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                os.path.join(os.path.dirname(__file__), img_path), 23, 23
            )
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            image.set_halign(Gtk.Align.CENTER)
            image.set_valign(Gtk.Align.CENTER) 

                    
            box_files.pack_start(image, False, False, 0)
            box_files.pack_start(filename_label, False, False, 0)
            box_files.pack_start(filepath_label, False, False, 0)  # Add some space
            event_box_files.add(box_files)
            event_box_files.connect("button-press-event", self.open_file, filepath)

            self.file_list_box.pack_start(event_box_files, False, False, 0)


        # Create box for dirs results
        img_path = 'assets/folder.png'
        
        for dir_name, dir_path in self.search_results_dirs.items():

            event_box_dirs = Gtk.EventBox()
            box_dirs = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            box_dirs.get_style_context().add_class("file-list-box")

            dir_name_label = Gtk.Label(label=dir_name)  # Use keyword argument for label
            dir_name_label.set_halign(Gtk.Align.CENTER)  
            dir_name_label.get_style_context().add_class("filename-text")
            dirpath_label = Gtk.Label(label=dir_path.replace("/home/user_name", ""))  # Use keyword argument for label
            dirpath_label.get_style_context().add_class("filepath-text")
            dirpath_label.set_halign(Gtk.Align.END)
            dir_name_label.set_halign(Gtk.Align.CENTER)
            dir_name_label.set_valign(Gtk.Align.CENTER) 


            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                os.path.join(os.path.dirname(__file__), img_path), 23, 23
            )
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            image.set_halign(Gtk.Align.CENTER)
            image.set_valign(Gtk.Align.CENTER) 

                    
            box_dirs.pack_start(image, False, False, 0)
            box_dirs.pack_start(dir_name_label, False, False, 0)
            box_dirs.pack_start(dirpath_label, False, False, 0) 
            event_box_dirs.add(box_dirs)
            event_box_dirs.connect("button-press-event", self.open_file, dir_path)

            self.dir_list_box.pack_start(event_box_dirs, False, False, 0)


        # Create box for apps results
        img_path = 'assets/app_icons/app.png'
        
        for appname, appcommand in self.search_results_apps.items():
            event_box_app = Gtk.EventBox()
            box_app = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            box_app.get_style_context().add_class("file-list-box")


            appname_label = Gtk.Label(label=appname)  # Use keyword argument for label
            appname_label.set_halign(Gtk.Align.CENTER)  
            appname_label.get_style_context().add_class("filename-text")
            appname_label.set_halign(Gtk.Align.CENTER)
            appname_label.set_valign(Gtk.Align.CENTER) 


            img_path = self.get_app_icon(appname)
                    
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                os.path.join(os.path.dirname(__file__), img_path), 23, 23
            )
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            image.set_halign(Gtk.Align.CENTER)
            image.set_valign(Gtk.Align.CENTER) 

            box_app.pack_start(image, False, False, 0)
            box_app.pack_start(appname_label, False, False, 0)
            event_box_app.add(box_app)
            event_box_app.connect("button-press-event", self.run_apps, appcommand)

            self.app_list_box.pack_start(event_box_app, False, False, 0)


        self.resize(600, 300)
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
        # Returns the icon path for the given file type.
        if('.py' in filename):
            return 'assets/file_icons/python.png'
        elif('.txt' in filename):
            return 'assets/file_icons/txt.png'
        elif('.cpp' in filename):
            return 'assets/file_icons/cpp.png'
        elif('.c' in filename):
            return 'assets/file_icons/cpp.png'
        elif('.png' in filename or '.jpg' in filename or '.jpeg' in filename):
            return 'assets/file_icons/image.png'
        elif('.pdf' in filename):
            return 'assets/file_icons/pdf.png'
        elif('.json' in filename):
            return 'assets/file_icons/json.png'
        elif('.html' in filename):
            return 'assets/file_icons/html.png'
        elif('.js' in filename):
            return 'assets/file_icons/js.png'
        elif('.vue' in filename):
            return 'assets/file_icons/vue.png'
        return 'assets/file_icons/txt.png'
    
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
        return 'assets/app_icons/app.png'

    def redefine_position(self, results_apps, results_files, results_dirs):
        # Dynamically adjust self.y without modifying the constant center value
        if (len(results_apps) > 5 or len(results_files) > 5 or len(results_dirs) > 5):
            self.move(self.x, self.y - 500)
        else:
            self.move(self.x, Y_CENTER)

        




# Run the application
win = SpotlightClone()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
