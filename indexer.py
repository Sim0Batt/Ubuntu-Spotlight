import sqlite3
import os
import argparse

DB_PATH = "spotlight_index.db"
APPLICATION_DB_PATH = "applications.db"

application_list = {'firefox':'firefox',
    'VS Code':'code',
    'WhatsApp': 'whatsapp-linux-app',
    'Spotify': 'spotify',
    'Zoom':'zoom',
    'Appunti':'emacs /home/$USER/università/appuntiLatex/',
    'OverLeaf':'firefox -new-window https://www.overleaf.com/project',
    'Moodle': 'firefox -new-window https://webapps.unitn.it/gestionecorsi/',
    'Telegram':'telegram-desktop',
    'Postman':'postman',
    'Gmail': 'firefox -new-window https://mail.google.com/mail/u/0/#inbox',
    'Studio': 'firefox -new-window https://webapps.unitn.it/gestionecorsi/ https://www.overleaf.com/project',
    'NoteTom': 'firefox --new-window https://notetom.onrender.com/',
    'Intellij': 'intellij-idea-ultimate',
    'Android Studio': 'android-studio'
}

def build_index(root_dir):
    conn_files = sqlite3.connect(DB_PATH)
    cursor = conn_files.cursor()

    # Recreate table to include a type column
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

    conn_application = sqlite3.connect(APPLICATION_DB_PATH)
    cursor_application = conn_application.cursor()

    cursor_application.execute("DROP TABLE IF EXISTS applications")
    cursor_application.execute("CREATE VIRTUAL TABLE applications USING fts5(name, command)")
    for app, command in application_list.items():
        cursor_application.execute("INSERT INTO applications (name, command) VALUES (?, ?)", (app.lower(), command))

    conn_files.commit()
    conn_files.close()
    conn_application.commit()
    conn_application.close()
    print(f"Index built for: {root_dir}")

def search(term, kind=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = f"{term}*"
    if kind:
        cursor.execute("SELECT path, type FROM entries WHERE name MATCH ? AND type = ?", (query, kind))
    else:
        cursor.execute("SELECT path, type FROM entries WHERE name MATCH ?", (query,))

    results = cursor.fetchall()
    conn.close()

    print(f"\nSearch results for '{term}' ({kind if kind else 'all'}):")
    for path, entry_type in results:
        print(f"[{entry_type}] {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spotlight Clone Indexer")
    parser.add_argument("--index", type=str, help="Path to index")
    parser.add_argument("--search", type=str, help="Search term")
    parser.add_argument("--type", type=str, choices=["file", "directory"], help="Type to search for")

    args = parser.parse_args()

    if args.index:
        build_index(args.index)
    elif args.search:
        search(args.search, args.type)
    else:
        print("Usage:")
        print("  python indexer.py --index /path/to/folder")
        print("  python indexer.py --search name [--type file|directory]")
