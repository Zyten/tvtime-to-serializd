from flask import Blueprint, render_template, request, jsonify, Response, stream_with_context
import pandas as pd
import threading
from . import tmdb_service
from .services.mapping import MappingService
import uuid

bp = Blueprint('main', __name__)

mapping_services = {}

@bp.route('/healthz')
def health_check():
    return 'OK', 200

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/upload', methods=['POST'])
def upload_files():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files.get('file')
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files are allowed"}), 400

    try:
        # Load TV Time CSV data as String columns, directly from memory
        tv_time_data = pd.read_csv(file.stream, dtype=str)

        # Generate a unique task_id
        task_id = str(uuid.uuid4())
        # Create a new MappingService instance
        mapping_service = MappingService(tmdb_service)
        # Store the instance in the global mapping_services dictionary
        mapping_services[task_id] = mapping_service

        # Start processing in a separate thread to allow asynchronous streaming
        threading.Thread(target=mapping_service.process_dataframe, args=(tv_time_data,)).start()

        return jsonify({"status": "Mapping started", "task_id": task_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Separate GET endpoint for SSE progress updates
@bp.route('/progress', methods=['GET'])
def progress():
    task_id = request.args.get('task_id')
    mapping_service = mapping_services.get(task_id)
    if not mapping_service:
        return 'No mapping service found for this task ID.', 404

    def generate():
        for update in mapping_service.get_progress_stream():
            yield f"data: {update}\n\n"
    response = Response(stream_with_context(generate()), content_type='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # For nginx, if applicable
    return response

@bp.route('/result')
def result():
    task_id = request.args.get('task_id')
    mapping_service = mapping_services.get(task_id)
    if not mapping_service:
        print(f'No mapping service found for this task ID: {task_id}')
        return 'No mapping service found for this task ID.', 404

    mapped_shows = [entry['tmdb_name'] for entry in mapping_service.mapped_entries.values()]
    unmapped_shows = [entry['title'] for entry in mapping_service.unmapped_entries.values()]

    # TODO: This is not too reliable - what if user never reaches the results page?
    mapping_services.pop(task_id, None)

    return render_template(
        'result.html',
        mapped_shows=mapped_shows,
        unmapped_shows=unmapped_shows,
        mapped_count=len(mapped_shows),
        unmapped_count=len(unmapped_shows)
    )