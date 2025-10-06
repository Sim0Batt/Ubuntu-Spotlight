import os
import subprocess
from pathlib import Path
import fnmatch
import sqlite3
import os

MAX_CHAR = 50 # Maximum characters for file name display
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
}

class SearchInFiles():
    def __init__(self):
        pass

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
            return {}

    @staticmethod
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


