# TVTime to Serializd

A tool to migrate your TV show list from TV Time to Serializd.

## Features

- Processes TVTime's CSV export
- Maps shows to TMDB entries (used by Serializd)
- Generates a list ready for Serializd import
- Identifies unmapped shows

_Note: Watch Status is not supported_

## Usage

1. Obtain your TV Time data:

   - Email TV Time support at support@tvtime.com requesting a copy of your data.
   - After verification, you'll receive tv-time-personal-data.zip, which contains `tracking-prod-records-v2.csv`.

2. Use the Online Tool:

   - Visit [tvtime-to-serializd.sruban.me](https://tvtime-to-serializd.sruban.me).
   - Upload tracking-prod-records-v2.csv.
   - The app will process your data and generate a list of mapped shows.
   - Copy the generated list.

3. Import to Serializd:

   - Go to Serializd settings > Import Data.
   - Paste the list and submit.

## Running Locally

If you prefer to run the app locally, follow these steps.

### Prerequisites

- Python 3.8+
- Supabase account
- TMDB API key
- TVTime CSV export (`tracking-prod-records-v2.csv`)

### Installation

1. Clone the repo and install dependencies

```bash
git clone https://github.com/Zyten/tvtime-to-serializd.git
cd tvtime-to-serializd

python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

pip install -r requirements.txt
```

2. Set up environment variables:

Create a `.env` file in the root directory:

```env
TMDB_API_KEY=your_tmdb_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
```

3. Set up the database:

   - Create a new project in Supabase.
   - In the Supabase SQL Editor, run the schema from `database/schema.sql`.
   - Download latest TMDB Daily IDs json and place it in the `tmdb/` directory.
   - Seed the database:

   ```bash
   python database/seed.py
   ```

### Run the application

```bash
gunicorn api.main:app
```

Access the app at http://localhost:8000.

## Deployment

- Create a new web service on Render.com
- Set environment variables in the Render dashboard
- Deploy the app

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
[GNU AGPLv3](LICENSE)
