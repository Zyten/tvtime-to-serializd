import json
import sqlite3
import os
from datetime import datetime

DB_PATH = 'tmdb_data.db'
TMDB_FOLDER = 'tmdb'

def get_latest_tv_show_file():
    # Filter for tv show files and sort by date in filename
    tv_show_files = sorted([f for f in os.listdir(TMDB_FOLDER) if f.startswith("tv_series_ids_")], reverse=True)
    return tv_show_files[0] if tv_show_files else None

def create_tables(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS tv_shows (
                        id INTEGER PRIMARY KEY,
                        original_name TEXT,
                        popularity REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT)''')

def load_tv_show_data(cursor, tv_show_file):
    cursor.execute("DELETE FROM tv_shows")
    with open(os.path.join(TMDB_FOLDER, tv_show_file), "r") as f_tv:
        for line in f_tv:
            data = json.loads(line)
            cursor.execute('''INSERT OR IGNORE INTO tv_shows (id, original_name, popularity)
                              VALUES (?, ?, ?)''', (data['id'], data['original_name'], data['popularity']))

def update_metadata(cursor, last_updated, tv_show_file):
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_updated', ?)", (last_updated,))
    cursor.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('tv_show_file', ?)", (tv_show_file,))

def create_tmdb_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    create_tables(cursor)

    latest_tv_show_file = get_latest_tv_show_file()
    if not latest_tv_show_file:
        print("Error: TV show files not found in the folder.")
        conn.close()
        return

    last_updated = cursor.execute("SELECT value FROM metadata WHERE key='last_updated'").fetchone()
    last_updated = last_updated[0] if last_updated else None
    current_date = datetime.now().strftime('%Y-%m-%d')
    if last_updated != current_date or \
       cursor.execute("SELECT value FROM metadata WHERE key='tv_show_file'").fetchone()[0] != latest_tv_show_file:
        print("Updating TMDb database...")
        load_tv_show_data(cursor, latest_tv_show_file)
        update_metadata(cursor, current_date, latest_tv_show_file)
        conn.commit()
        print("Database updated successfully.")
    else:
        print("TMDb database is already up-to-date.")

    conn.close()

if __name__ == "__main__":
    create_tmdb_database()
