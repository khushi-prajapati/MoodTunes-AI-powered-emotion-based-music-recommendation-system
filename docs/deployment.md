# MoodTunes Deployment

## Architecture

The Docker stack runs five production-style services:

- `frontend`: Vite build served by Nginx. It proxies `/api/` and `/admin/` to Django and serves uploaded media from the shared media volume.
- `backend`: Django REST Framework served by Gunicorn. The entrypoint can run migrations and collect static files.
- `db`: PostgreSQL 16 with a persistent `postgres_data` volume.
- `redis`: Redis 7 for Celery broker/results and Django cache.
- `celery` and `celery-beat`: background workers for recommendations, analytics snapshots, and maintenance.

## Local Docker

1. Copy backend environment values into `backend/.env`.
2. Set `SECRET_KEY`, `YOUTUBE_API_KEY`, and optional `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET`.
3. Run:

```bash
docker compose up --build
```

Frontend is served at `http://localhost:5173` and the API is proxied at `/api`.

Useful commands:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec celery celery -A config inspect ping
docker compose logs -f backend celery celery-beat
```

## Local Development Without Docker

Run Redis and PostgreSQL locally, then:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

In another terminal:

```bash
cd backend
source .venv/bin/activate
celery -A config worker -l INFO
celery -A config beat -l INFO
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev -- --host 127.0.0.1 --port 5173
```

## Analytics

`GET /api/analytics/dashboard/` returns a scoped analytics payload. Staff users receive platform-wide metrics; regular users receive their own usage metrics.

Celery Beat generates hourly `AnalyticsSnapshot` records and runs nightly cleanup. The Django admin dashboard uses Chart.js for operational cards and charts, while the React analytics page uses Recharts for user-facing insights.

## Spotify

Spotify uses the Client Credentials flow. Configure:

```env
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
```

Supported backend endpoints:

- `GET /api/music/spotify/search/?q=...`
- `GET /api/music/spotify/playlist/?playlist=<public playlist url or id>`
- `GET /api/music/spotify/artists/<artist_id>/`

The frontend Spotify page supports track search, public playlist import/preview, previews when Spotify provides them, and artist/album metadata lookup. YouTube recommendation playback remains unchanged.

## Production Notes

- Set `DEBUG=False`.
- Use strong `SECRET_KEY`.
- Set `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`.
- Store PostgreSQL and Redis data on managed or persistent volumes.
- Run backend behind HTTPS and pass `X-Forwarded-Proto`.
- Keep `RUN_MIGRATIONS=1` for one release task or run migrations separately.
- Run Celery worker and beat as separate processes.
- Use `config.settings_production` when HTTPS is correctly configured:

```env
DJANGO_SETTINGS_MODULE=config.settings_production
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
```

Recommended production release flow:

```bash
docker compose pull
docker compose build
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py collectstatic --noinput
docker compose up -d
docker compose ps
```
