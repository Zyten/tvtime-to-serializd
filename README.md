# TVTime to Serializd

A tool to help users migrate their TV show lists from TVTime to Serializd.

## Features

- Processes TVTime's CSV export
- Maps shows to TMDB entries (which Serializd uses)
- Provides clean list of show titles ready for Serializd import
- Identifies unmapped shows for reference

## Setup

### Prerequisites

- Python 3.8+
- Supabase account
- TMDB API key
- TVTime CSV export (`tracking-prod-records-v2.csv`)

### Environment Variables

Create a `.env` file in the root directory:

```env
TMDB_API_KEY=your_tmdb_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
```

### Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/tvtime-to-serializd.git
cd tvtime-to-serializd
```

2. Create and activate virtual environment

```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

### Database Setup

1. Create a new project in Supabase
2. Go to SQL Editor in your Supabase dashboard
3. Run the schema from database/schema.sql
4. Download daily TMDB TV shows data and place in tmdb/ directory
5. Populate database with show data:

```bash
python database/seed.py
```

### Development

Run the development server:
```bash
python run.py
```
The app will be available at http://localhost:5000

### Usage

1. Email TV Time support at `support@tvtime.com` with subject `GDPR Data Request`, requesting a copy of your data.
2. After passing the verification steps, you'd receive `tv-time-personal-data.zip`, which when extracted, contains `tracking-prod-records-v2.csv` among other things.
3. Upload `tracking-prod-records-v2.csv` into the app
4. Copy the mapped shows list
5. Goto Serializd Settings > Import Data
6. Paste and Submit (Mark as Watched)
Note: There's no progress bar or success message.
7. Open your Serializd profile in new tab to see if Watched list count matches what you pasted

### Deployment

This app is designed to be deployed on Vercel:
1. Connect your GitHub repository to Vercel
2. Add environment variables in Vercel dashboard
3. Deploy

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

### License
[GNU AGPLv3](LICENSE)