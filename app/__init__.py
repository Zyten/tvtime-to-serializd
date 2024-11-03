from flask import Flask
from flask_socketio import SocketIO
from supabase import create_client, Client
from config import Config

socketio = SocketIO(cors_allowed_origins="*")
tmdb_service = None
mapping_service = None

def create_app(config_object=Config):
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.config.from_object(config_object)
    socketio.init_app(app)
    
    supabase: Client = create_client(
        app.config['SUPABASE_URL'],
        app.config['SUPABASE_KEY']
    )
    
    global tmdb_service, mapping_service
    from .services.tmdb import TMDBService
    from .services.mapping import MappingService
    
    tmdb_service = TMDBService(
        supabase=supabase,
        api_key=app.config['TMDB_API_KEY'],
        base_url=app.config['TMDB_BASE_URL']
    )
    mapping_service = MappingService(tmdb_service)
    
    from . import routes
    app.register_blueprint(routes.bp)
    
    return app