import sqlite3
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import threading
import requests
import time
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3/find"

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mapped_entries, unmapped_entries = {}, {}

@app.route('/')
def index():
	return render_template('index.html')

def find_by_tvdb_id(tvdb_id):
	try:
		url = f"{TMDB_BASE_URL}/{tvdb_id}"
		headers = {
			"accept": "application/json",
			"Authorization": f"Bearer {TMDB_API_KEY}"
		}

		params = {
			"external_source": "tvdb_id",
		}
		response = requests.get(url, headers=headers, params=params)

		response.raise_for_status()
		data = response.json()

		if data.get("tv_results"):
			tv_show = data["tv_results"][0]
			return {
                "tmdb_id": tv_show["id"],
                "tmdb_name": tv_show["name"],
                "tmdb_original_name": tv_show["original_name"],
            }
	except requests.exceptions.RequestException as e:
		print(f"API request failed for TVDB ID {tvdb_id}: {e}")
	return None


@app.route('/upload', methods=['POST'])
def upload_files():
	file = request.files.get('file')
	
	if file:
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
		threading.Thread(target=generate_mapping, args=(file.filename,)).start()
		return jsonify({"status": "Mapping started"}), 200
	return "Please upload the tracking-prod-records-v2.csv file."

def generate_mapping(file):
	print("Starting TV show mapping")

	# Load TV Time CSV data as String columns
	tv_time_data = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], file), dtype=str)
	# Replace NaN in 'series_name' with empty strings
	tv_time_data['series_name'] = tv_time_data['series_name'].fillna('')
	# Drop rows with missing s_id
	tv_time_data = tv_time_data.dropna(subset=['s_id'])
	# Drop duplicates, and reset index
	unique_shows = tv_time_data[['s_id', 'series_name']].drop_duplicates().reset_index(drop=True)

	total_rows = len(unique_shows)
	print(f"Found {total_rows} rows in TV Time list")

	global mapped_entries, unmapped_entries
	mapped_entries, unmapped_entries = {}, {}

	conn = sqlite3.connect('tmdb/tv_series.db')
	cursor = conn.cursor()

	for index, row in unique_shows.iterrows():
		tvdb_id = row['s_id']
		title = row['series_name']

		# Perform exact match in SQLite
		cursor.execute("SELECT id, original_name FROM tv_shows WHERE LOWER(original_name) = ?", (title.strip().lower(),))
		result = cursor.fetchone()

		if result:
			tmdb_id, tmdb_name = result
			mapped_entries[tvdb_id] = {
				'tmdb_id': tmdb_id,
				'title': title,
				'tmdb_name': tmdb_name,
			}
			print(f"{index + 1}/{total_rows}: {title} mapped with LOCAL DB")
		else:
			tmdb_data = find_by_tvdb_id(tvdb_id)
			if tmdb_data:
				mapped_entries[tvdb_id] = {
					'tmdb_id': tmdb_data["tmdb_id"],
					'title': title,
					'tmdb_name': tmdb_data["tmdb_original_name"]
				}
				print(f"{index + 1}/{total_rows}: {title} mapped with ONLINE DB")
			else:
				unmapped_entries[tvdb_id] = {'title': title}
				print(f"{index + 1}/{total_rows}: {title} is UNMAPPED")

			time.sleep(0.3)

		progress = (index + 1) / total_rows * 100
		socketio.emit('progress', {'progress': progress, 'index': index + 1, 'total': total_rows})

	conn.close()
	socketio.emit('complete', {'mapped': len(mapped_entries), 'unmapped': len(unmapped_entries)})

@app.route('/unmapped')
def unmapped():
	return render_template('mapping.html', mapped_count=len(mapped_entries), unmapped_count=len(unmapped_entries), unmapped_entries=unmapped_entries)

# Local search endpoint for manual mapping
@app.route('/search_local_tmdb', methods=['POST'])
def search_local_tmdb():
	data = request.json
	query = data.get('query', '').strip().lower()

	if not query:
		return jsonify({"results": []})

	conn = sqlite3.connect('tmdb_data.db')
	cursor = conn.cursor()

	cursor.execute("SELECT id, original_name FROM tv_shows WHERE lower(original_name) LIKE ? LIMIT 15", ('%' + query + '%',))
	results = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
	conn.close()

	return jsonify(results=results)

@app.route('/manual_map', methods=['POST'])
def manual_map():
	data = request.json
	tvdb_id = data.get('tvdb_id')
	tmdb_id = data.get('tmdb_id')

	if tvdb_id in unmapped_entries:
		title = unmapped_entries[tvdb_id]['title']
		mapped_entries[tvdb_id] = {
			'tmdb_id': tmdb_id,
			'title': title,
			'tmdb_name': title
		}
		del unmapped_entries[tvdb_id]

	return jsonify(mapped_count=len(mapped_entries), unmapped_count=len(unmapped_entries))

if __name__ == '__main__':
	socketio.run(app, debug=True)
