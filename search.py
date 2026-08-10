import os
import subprocess
from pathlib import Path
import shlex
import fnmatch
import sqlite3

MAX_CHAR = 50 # Maximum characters for file name display
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "spotlight_index.db")
APPLICATION_DB_PATH = str(BASE_DIR / "applications.db")
HOME_DIR = str(Path.home())

application_list = {
    'firefox':'firefox', 
    'visual studio code':'code',  
    'whatsapp': 'whatsapp-linux-app', 
    'spotify': 'spotify', 
    'zoom':'zoom', 
    'gaia-web':'firefox -new-window https://gaiaassistant.netlify.app/',
    'overleaf':'firefox -new-window https://www.overleaf.com/project',
    'moodle': 'firefox -new-window https://webapps.unitn.it/gestionecorsi/',
    'postman':'postman',
    'gmail': 'firefox -new-window https://mail.google.com/mail/u/0/#inbox',
    'intellij': 'intellij-idea-ultimate',
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
            cursor = conn.cursor()

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
            if not command:
                return
            normalized_command = os.path.expandvars(os.path.expanduser(command))
            subprocess.Popen(shlex.split(normalized_command))
        except Exception as e:
            print(f"Error running application: {e}")


