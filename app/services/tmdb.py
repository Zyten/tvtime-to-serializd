from datetime import datetime, timedelta
import requests
from typing import Optional, Dict, Any
from supabase import Client

class TMDBService:
    def __init__(self, supabase: Client, api_key: str, base_url: str):
        self.supabase = supabase
        self.api_key = api_key
        self.base_url = base_url

    def find_by_tvdb_id(self, tvdb_id: str) -> Optional[Dict[str, Any]]:
        # Check cache first
        try:
            cache_response = self.supabase.table('tmdb_cache') \
                .select('tmdb_data') \
                .eq('tvdb_id', tvdb_id) \
                .gte('expires_at', datetime.utcnow().isoformat()) \
                .execute()
            
            if cache_response.data:
                return cache_response.data[0]['tmdb_data']
        except Exception as e:
            print(f"Cache check failed for TVDB ID {tvdb_id}: {e}")

        # If not in cache or expired, call API
        try:
            url = f"{self.base_url}/{tvdb_id}"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            params = {"external_source": "tvdb_id"}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("tv_results"):
                tv_show = data["tv_results"][0]
                result = {
                    "tmdb_id": tv_show["id"],
                    "tmdb_name": tv_show["name"],
                    "tmdb_original_name": tv_show["original_name"],
                }
                
                # Cache the result
                try:
                    self.supabase.table('tmdb_cache').upsert({
                        'tvdb_id': tvdb_id,
                        'tmdb_data': result,
                        'expires_at': (datetime.utcnow() + timedelta(hours=48)).isoformat()
                    }).execute()
                except Exception as e:
                    print(f"Failed to cache TVDB ID {tvdb_id}: {e}")

                return result

        except requests.exceptions.RequestException as e:
            print(f"API request failed for TVDB ID {tvdb_id}: {e}")
        
        return None

    def find_by_original_name(self, title: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.supabase.table('tv_shows') \
                .select('id, original_name') \
                .ilike('original_name', title.strip().lower()) \
                .execute()
            
            if response.data:
                row = response.data[0]
                return {
                    'id': row['id'],
                    'name': row['original_name']
                }
            return None
        except Exception as e:
            print(f"Database lookup failed for title '{title}': {e}")
            return None