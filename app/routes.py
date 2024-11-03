from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import threading
from . import socketio, mapping_service

bp = Blueprint('main', __name__)

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
 
        def progress_callback(progress, index, total):
            socketio.emit('progress', {
                'progress': progress,
                'index': index,
                'total': total
            })

        def mapping_thread():
            try:
                result = mapping_service.process_dataframe(tv_time_data, progress_callback)
                socketio.emit('complete', result)
            except Exception as e:
                print("Failed to load tvtime csv into dataframe")
                socketio.emit('error', {'message': str(e)})

        threading.Thread(target=mapping_thread).start()
        return jsonify({"status": "Mapping started"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/result')
def result():
    mapped_shows = [entry['tmdb_name'] for entry in mapping_service.mapped_entries.values()]
    unmapped_shows = [entry['title'] for entry in mapping_service.unmapped_entries.values()]
    
    return render_template(
        'result.html',
        mapped_shows=mapped_shows,
        unmapped_shows=unmapped_shows,
        mapped_count=len(mapped_shows),
        unmapped_count=len(unmapped_shows)
    )