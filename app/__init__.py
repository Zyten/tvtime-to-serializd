from flask import Flask
from supabase import create_client, Client
from config import Config

tmdb_service = None

def create_app(config_object=Config):
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(config_object)

    supabase: Client = create_client(
        app.config['SUPABASE_URL'],
        app.config['SUPABASE_KEY']
    )
    
    global tmdb_service
    from .services.tmdb import TMDBService
    
    tmdb_service = TMDBService(
        supabase=supabase,
        api_key=app.config['TMDB_API_KEY'],
        base_url=app.config['TMDB_BASE_URL']
    )

    from . import routes
    app.register_blueprint(routes.bp)
    
    return app