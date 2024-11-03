from typing import Dict, Any
import time

class MappingService:
    def __init__(self, tmdb_service):
        self.tmdb_service = tmdb_service
        self.mapped_entries: Dict[str, Any] = {}
        self.unmapped_entries: Dict[str, Any] = {}

    def process_dataframe(self, tv_time_data, progress_callback=None):
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

                time.sleep(0.3)  # Rate limiting

            if progress_callback:
                progress = (index + 1) / total_rows * 100
                progress_callback(progress, index + 1, total_rows)

        return {
            'mapped': len(self.mapped_entries),
            'unmapped': len(self.unmapped_entries)
        }