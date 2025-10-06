import os
import subprocess
from pathlib import Path
import fnmatch
import sqlite3
import os

MAX_CHAR = 50 # Maximum characters for file name display
<<<<<<< HEAD
DB_PATH = os.path.expanduser("/home/$USER/spotlight/spotlight_index.db")
APPLICATION_DB_PATH = os.path.expanduser("/home/$USER/spotlight/applications.db")

application_list = {
    'firefox':'firefox', 
    'visual studio code':'code',  
    'whatsapp': 'whatsapp-linux-app', 
    'spotify': 'spotify', 
    'zoom':'zoom', 
    'appunti':'emacs /home/$USER/università/appuntiLatex/', 
    'gaia-app':'python /home/$USER/gaia/app.py',
    'gaia-web':'firefox -new-window https://gaiaassistant.netlify.app/',
    'overleaf':'firefox -new-window https://www.overleaf.com/project',
    'moodle': 'firefox -new-window https://webapps.unitn.it/gestionecorsi/',
    'telegram':'telegram-desktop',
    'postman':'postman',
    'gmail': 'firefox -new-window https://mail.google.com/mail/u/0/#inbox',
    'studio': 'firefox -new-window https://webapps.unitn.it/gestionecorsi/ https://www.overleaf.com/project',
    'notetom': 'firefox --new-window https://notetom.onrender.com/',
    'intellij': 'intellij-idea-ultimate',
    'Android Studio': 'android-studio'
=======
DB_PATH = os.path.expanduser("/home/simone/spotlight/spotlight_index.db")  # You can change path


application_list = {'firefox':'firefox', 
                    'visual studio code':'code',  
                    'whatsapp': 'whatsapp-linux-app', 
                    'spotify': 'spotify', 
                    'zoom':'zoom', 
                    'overleaf':'firefox -new-window https://www.overleaf.com/project',
                    'telegram':'telegram-desktop',
                    'postman':'postman',
                    'gmail': 'firefox -new-window https://mail.google.com/mail/u/0/#inbox',
>>>>>>> 3294013577bfebe85ea1622d6c75b853c9e822d2
}

class SearchInFiles():
    def __init__(self):
        pass

<<<<<<< HEAD
    @staticmethod
    def search(term, kind=None):
        """
        Search for entries in the SQLite database using FTS5
        Args:
            term: Search term
            kind: Type of item to search for ("file" or "directory")
        Returns:
            List of (path, type) tuples matching the search
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            conn_app = sqlite3.connect(APPLICATION_DB_PATH)
            cursor = conn.cursor()
            cursor_app = conn_app.cursor()

            # Escape special characters and add wildcard
            escaped_term = term.replace('"', '""')
            query = f'"{escaped_term}"*'

=======
    def build_index(root_dir):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS entries")
        cursor.execute("CREATE VIRTUAL TABLE entries USING fts5(path, name, type)")

        for root, dirs, files in os.walk(root_dir):
            for d in dirs:
                full_path = os.path.join(root, d)
                cursor.execute("INSERT INTO entries (path, name, type) VALUES (?, ?, ?)",
                            (full_path, d, "directory"))
            for f in files:
                full_path = os.path.join(root, f)
                cursor.execute("INSERT INTO entries (path, name, type) VALUES (?, ?, ?)",
                            (full_path, f, "file"))

        conn.commit()
        conn.close()
        print(f"Index built for: {root_dir}")

    @staticmethod
    def search(term, kind=None):
        """
        Search for entries in the SQLite database using FTS5
        Args:
            term: Search term
            kind: Type of item to search for ("file" or "directory")
        Returns:
            List of (path, type) tuples matching the search
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Escape special characters and add wildcard
            escaped_term = term.replace('"', '""')
            query = f'"{escaped_term}"*'

>>>>>>> 3294013577bfebe85ea1622d6c75b853c9e822d2
            if kind:
                cursor.execute("""
                    SELECT path, type 
                    FROM entries 
                    WHERE entries MATCH ? AND type = ?
                    ORDER BY rank
                    LIMIT 10
                """, (query, kind))
            else:
                cursor.execute("""
                    SELECT path, type 
                    FROM entries 
                    WHERE entries MATCH ?
                    ORDER BY rank
                    LIMIT 10
                """, (query,))

            results = cursor.fetchall()
            conn.close()
            return results
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        except Exception as e:
            print(f"Error performing search: {e}")
            return []

    @staticmethod
    def search_files(term):
        """Search for files matching the term"""
        if not term:
<<<<<<< HEAD
            return {}
        results = SearchInFiles.search(term, "file")
        return {os.path.basename(path): path for path, type in results[:10]}
    
    @staticmethod
    def search_dirs(term):
        """Search for directories matching the term"""
        if not term:
            return {}
        results = SearchInFiles.search(term, "directory")
        return {os.path.basename(path): path for path, type in results[:10]}

    @staticmethod
    def search_application(term):
        """Search for applications matching the term using the applications database"""
        if not term:
            return {}
        try:
            conn = sqlite3.connect(APPLICATION_DB_PATH)
            cursor = conn.cursor()
            # Prepare the FTS5 query (use wildcard and quote for FTS escaping)
            escaped_term = term.replace('"', '""')
            query = f'"{escaped_term}"*'
            cursor.execute(
                """
                SELECT name, command
                FROM applications
                WHERE applications MATCH ?
                LIMIT 10
                """, 
                (query,)
            )
            results = cursor.fetchall()
            conn.close()
            return {name: command for name, command in results}
        except sqlite3.Error as e:
            print(f"Database error (applications): {e}")
            return {}
        except Exception as e:
            print(f"Error performing application search: {e}")
=======
>>>>>>> 3294013577bfebe85ea1622d6c75b853c9e822d2
            return {}
        results = SearchInFiles.search(term, "file")
        return {os.path.basename(path): path for path, type in results[:10]}
    
    @staticmethod
    def search_dirs(term):
        """Search for directories matching the term"""
        if not term:
            return {}
        results = SearchInFiles.search(term, "directory")
        return {os.path.basename(path): path for path, type in results[:10]}

    @staticmethod
<<<<<<< HEAD
=======
    def search_application(term):
        """Search for applications matching the term"""
        if not term:
            return {}
        results = {}
        for app_name, command in application_list.items():
            if term.lower() in app_name.lower():
                results[app_name] = command
        return dict(list(results.items())[:10])

    @staticmethod
>>>>>>> 3294013577bfebe85ea1622d6c75b853c9e822d2
    def open_file(filepath):
        """Open a file using xdg-open"""
        try:
            subprocess.run(["xdg-open", filepath])
        except Exception as e:
            print(f"Error opening file: {e}")

    @staticmethod
    def open_directory(dirpath):
        """Open a directory in the file manager"""
        try:
            subprocess.run(["nautilus", dirpath])
        except Exception as e:
            print(f"Error opening directory: {e}")

    @staticmethod
    def run_applications(command):
        """Run an application command"""
        try:
            subprocess.Popen(command.split())
        except Exception as e:
            print(f"Error running application: {e}")


