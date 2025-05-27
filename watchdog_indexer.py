import os
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

DB_PATH = "spotlight_index.db"
WATCH_PATH = "/home/simone"  # Change this to the directory you want to monitor


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS files USING fts5(path, name)")
    conn.commit()
    conn.close()


def add_file_to_index(filepath):
    if os.path.isfile(filepath):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (path, name) VALUES (?, ?)", (filepath, os.path.basename(filepath)))
        conn.commit()
        conn.close()


def remove_file_from_index(filepath):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE path = ?", (filepath,))
    conn.commit()
    conn.close()


class IndexEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            add_file_to_index(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            remove_file_from_index(event.src_path)
            add_file_to_index(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            remove_file_from_index(event.src_path)


def full_initial_index(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            add_file_to_index(os.path.join(root, file))


def run_daemon():
    init_db()
    full_initial_index(WATCH_PATH)
    print(f"Indexing started on: {WATCH_PATH}")

    event_handler = IndexEventHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_PATH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    run_daemon()
