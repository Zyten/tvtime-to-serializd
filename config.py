import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    TMDB_BASE_URL = "https://api.themoviedb.org/3/find"
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size