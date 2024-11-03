import json
import os
from datetime import datetime
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

TMDB_FOLDER = 'tmdb'
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_latest_tv_show_file():
    tv_show_files = sorted([f for f in os.listdir(TMDB_FOLDER) if f.startswith("tv_series_ids_")], reverse=True)
    return tv_show_files[0] if tv_show_files else None

async def populate_database():
    latest_file = get_latest_tv_show_file()
    if not latest_file:
        print("Error: TV show files not found in the folder.")
        return

    print("Starting database population...")
    
    # First, clear existing data
    try:
        data = supabase.table('tv_shows').delete().neq('id', 0).execute()
        print("Cleared existing data")
    except Exception as e:
        print(f"Error clearing existing data: {e}")
        return

    batch_size = 10000
    current_batch = []
    total_records = 0

    with open(os.path.join(TMDB_FOLDER, latest_file), "r") as f_tv:
        for line in f_tv:
            data = json.loads(line)
            show_data = {
                'id': data['id'],
                'original_name': data['original_name'],
                'popularity': data['popularity']
            }
            current_batch.append(show_data)

            if len(current_batch) >= batch_size:
                try:
                    data = supabase.table('tv_shows').upsert(current_batch).execute()
                    total_records += len(current_batch)
                    print(f"Inserted {len(current_batch)} records. Total: {total_records}")
                    current_batch = []
                except Exception as e:
                    print(f"Error inserting batch: {e}")
                    return

    # Insert remaining records
    if current_batch:
        try:
            data = supabase.table('tv_shows').upsert(current_batch).execute()
            total_records += len(current_batch)
            print(f"Inserted final {len(current_batch)} records. Total: {total_records}")
        except Exception as e:
            print(f"Error inserting final batch: {e}")
            return

    print(f"Database population completed! Total records: {total_records}")

if __name__ == "__main__":
    asyncio.run(populate_database())