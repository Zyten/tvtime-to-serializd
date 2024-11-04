from typing import Dict, Any
import time
import threading

class MappingService:
    def __init__(self, tmdb_service):
        self.tmdb_service = tmdb_service
        self.mapped_entries: Dict[str, Any] = {}
        self.unmapped_entries: Dict[str, Any] = {}
        self.progress_updates = []  # Stores progress updates for SSE streaming
        self.update_event = threading.Event()
        self.processing_complete = False

    def get_progress_stream(self):
        last_index = 0
        while not self.processing_complete or last_index < len(self.progress_updates):
            # Wait until a new update is available or processing is complete
            self.update_event.wait()
            while last_index < len(self.progress_updates):
                progress, index, total = self.progress_updates[last_index]
                last_index += 1
                yield f"{progress},{index},{total}"
            self.update_event.clear()
        # Send the completion message
        yield f"complete,{len(self.mapped_entries)},{len(self.unmapped_entries)}"

    def process_dataframe(self, tv_time_data):
        self.progress_updates = []
        self.processing_complete = False

        # Replace NaN in 'series_name' with empty strings
        tv_time_data['series_name'] = tv_time_data['series_name'].fillna('')
        # Drop rows with missing s_id
        tv_time_data = tv_time_data.dropna(subset=['s_id'])
        # Drop duplicates, and reset index
        unique_shows = tv_time_data[['s_id', 'series_name']].drop_duplicates().reset_index(drop=True)

        total_rows = len(unique_shows)
        self.mapped_entries = {}
        self.unmapped_entries = {}

        for index, row in unique_shows.iterrows():
            tvdb_id = row['s_id']
            title = row['series_name'].strip()

            # Try exact match first using local DB
            exact_match = self.tmdb_service.find_by_original_name(title)
            if exact_match:
                self.mapped_entries[tvdb_id] = {
                    'tmdb_id': exact_match['id'],
                    'title': title,
                    'tmdb_name': exact_match['name'],
                }
                print(f"{index + 1}/{total_rows}: {title} mapped with LOCAL DB")
            else:
                # Try TMDB API
                tmdb_data = self.tmdb_service.find_by_tvdb_id(tvdb_id)
                if tmdb_data:
                    self.mapped_entries[tvdb_id] = {
                        'tmdb_id': tmdb_data["tmdb_id"],
                        'title': title,
                        'tmdb_name': tmdb_data["tmdb_original_name"]
                    }
                    print(f"{index + 1}/{total_rows}: {title} mapped with ONLINE DB")
                else:
                    self.unmapped_entries[tvdb_id] = {'title': title}
                    print(f"{index + 1}/{total_rows}: {title} is UNMAPPED")

                time.sleep(0.03)  # Rate limiting - max 30 per second

            progress = (index + 1) / total_rows * 100
            self.progress_updates.append((progress, index + 1, total_rows))
            self.update_event.set()  # Signal that a new update is available

        self.processing_complete = True
        self.update_event.set()

        return {
            'mapped': len(self.mapped_entries),
            'unmapped': len(self.unmapped_entries)
        }