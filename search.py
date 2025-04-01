import os
import subprocess


MAX_CHAR = 50 # Maximum characters for file name display

application_list = {'firefox':'firefox', 
                    'visual studio code':'code',  
                    'whatsapp': '', 
                    'spotify': 'spotify', 
                    'zoom':'zoom', 
                    'appunti':'emacs /home/user_name/università/appuntiLatex/', 
                    'gaia':'python /home/user_name/gaia/app.py'}

class SearchInFiles():
    def __init__(self):
        pass

    def search_files(search_text):
        matching_files = {}
        if search_text != "":
            count = 0  # Counter to limit results
            for root, dirs, files in os.walk("/home/user_name/"):  # Search from the root directory
                for file in files:
                    if search_text in file:
                        name_file = file[0:MAX_CHAR]
                        matching_files[name_file] = os.path.join(root, file)
                        count += 1
                        if count >= 10:  # Stop after 10 results
                            return matching_files
        return matching_files  # Always return a dictionary
    
    def search_dirs(search_text):
        matching_dirs = {}
        if search_text != "":
            count = 0  # Counter to limit results
            for root, dirs, files in os.walk("/home/user_name/"):  # Search from the root directory
                for dir in dirs:
                    if search_text in dir:
                        name_dir = dir[0:MAX_CHAR]
                        matching_dirs[name_dir] = os.path.join(root, dir)
                        count += 1
                        if count >= 10:  # Stop after 10 results
                            return matching_dirs
        return matching_dirs  # Always return a dictionary

    def open_file(file_path):
        subprocess.run(["gnome-terminal", "--", "bash", "-c", f"code {file_path}"])

    
    def search_application(search_text):
        if not search_text.strip():  # Return empty if search text is empty or whitespace
            return {}

        matching_apps = {}
        search_text = search_text.lower()
        for app in application_list:
            if search_text in app:
                matching_apps[app] = application_list[app]
        return matching_apps
    
    def run_applications(command):
        subprocess.run(["gnome-terminal", "--", "bash", "-c", str(command)])
        return
    
    def open_directory(dir_path):
        subprocess.run(["gnome-terminal", "--", "bash", "-c", f"nautilus {dir_path}"])
        return
