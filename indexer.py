import sqlite3
import os
import argparse

DB_PATH = "spotlight_index.db"

def build_index(root_dir):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()
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
