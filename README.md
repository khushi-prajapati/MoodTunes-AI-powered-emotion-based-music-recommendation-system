# eMusic

eMusic is a full-stack, mood-aware music discovery application presented in the UI as **MoodTunes**. It combines account-based recommendations, Spotify and YouTube metadata, playlist management, listening insights, and optional webcam emotion detection in a responsive React interface.

## Highlights

- JWT registration, sign-in, profile, and protected routes
- Mood-based and emotion-assisted song recommendations
- Spotify search, artist, and playlist discovery
- Favourites, custom playlists, and recommendation history
- Personal analytics dashboard and scheduled analytics snapshots
- Custom Django administration experience
- Production-oriented Docker services for PostgreSQL, Redis, Celery, Django, and Nginx

## Technology stack

| Area | Technology |
| --- | --- |
| Frontend | React 19, Vite 8, Tailwind CSS 4, React Router, Axios, Recharts, Framer Motion |
| Backend | Python 3.11, Django 5.2, Django REST Framework, Simple JWT |
| AI / vision | FER, TensorFlow, MTCNN, OpenCV |
| Data | SQLite for local development; PostgreSQL-ready configuration |
| Background work | Celery and Redis |
| Deployment | Docker Compose, Gunicorn, Nginx, WhiteNoise |

## Project layout

```text
emousic/
├── frontend/             # React application
├── backend/
│   ├── authentication/   # Registration, login, JWT, and profiles
│   ├── users/            # Custom user model
│   ├── music/            # Recommendations, providers, playlists, and favourites
│   ├── ai_emotion/       # Webcam-image emotion detection and mood mapping
│   ├── analytics/        # User insights and aggregate snapshots
│   ├── tasks/            # Celery analytics and cleanup jobs
│   └── config/           # Django settings, URLs, ASGI/WSGI, and Celery setup
├── ai-services/          # Notes for independently deployable AI services
├── docs/                 # Deployment and architecture documentation
└── docker-compose.yml
```

## Local development

### Prerequisites

- Python 3.11
- Node.js and npm compatible with the versions in `frontend/package-lock.json`
- Redis only when running Celery or Redis-backed caching
- PostgreSQL only when not using the default local SQLite setup

### Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Edit `backend/.env` before running the server. Generate a unique Django secret key, and add provider credentials only when testing the matching integration. The checked-in example contains placeholders only.

SQLite is configured in `.env.example` for local development. To use PostgreSQL, set `DB_ENGINE=django.db.backends.postgresql` and provide `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.

Create admin and test accounts locally with `python manage.py createsuperuser` or through the registration API. No shared or production login credentials are included in this repository.

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev -- --host 127.0.0.1 --port 5173
```

The frontend defaults to `http://127.0.0.1:8000/api`. Configure these public build-time variables when needed:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_DJANGO_ADMIN_URL=http://127.0.0.1:8000/admin/
```

## API overview

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health/` | Service health check |
| `POST /api/auth/register/` | Create a local account |
| `POST /api/auth/login/` | Obtain JWT credentials |
| `POST /api/auth/token/refresh/` | Refresh a JWT |
| `GET /api/auth/profile/` | Read the authenticated profile |
| `GET /api/music/moods/` | List supported moods |
| `POST /api/music/recommend/` | Request mood-based recommendations |
| `/api/music/playlists/` | Manage authenticated-user playlists |
| `/api/music/favorites/` | Manage favourites |
| `/api/music/spotify/` | Search Spotify metadata and public catalogue data |
| `POST /api/ai/detect-emotion/` | Map an uploaded image to an emotion and mood |
| `GET /api/analytics/dashboard/` | Retrieve personal analytics |

Except for registration, login, and health checks, API routes generally require an `Authorization: Bearer <token>` header.

## Background services

With Redis running and the backend environment configured:

```bash
cd backend
celery -A config worker -l INFO
celery -A config beat -l INFO
```

Celery handles analytics snapshots, cleanup jobs, and recommendation-related background work.

## Docker deployment

```bash
cp .env.example .env
cp backend/.env.example backend/.env
# Replace every placeholder and enable the HTTPS security settings for production.
docker compose up --build
```

The Compose stack starts PostgreSQL, Redis, Django/Gunicorn, Celery worker and beat services, and the React/Nginx frontend. Review [`docs/deployment.md`](docs/deployment.md) before deployment. Use a managed secret store in production, restrict `ALLOWED_HOSTS`, CORS, and CSRF origins, terminate TLS, back up the database securely, and do not deploy with `DEBUG=True`.

## Validation

Run the checks appropriate to the area you changed:

```bash
cd backend
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test

cd ../frontend
npm run lint
npm run build
```

## Music and media policy

eMusic stores recommendation metadata, provider identifiers, thumbnails, and user-created organisation data; it does not require a local song library. Playback and catalogue information are provided through external services subject to their own terms.

Real songs, copyrighted recordings, user-uploaded audio, private playlists, generated audio, database files, and downloaded streaming content are intentionally excluded from Git. If a legally redistributable test fixture is ever required, place it in `sample_media/`, keep it small, and document its source and licence before committing it.

## Screenshots

Project screenshots can be added under `docs/screenshots/` after confirming that they contain no personal information, tokens, private playlists, or copyrighted artwork that cannot be redistributed.

## Privacy and copyright

Local databases may contain email addresses, password hashes, mood and listening history, favourites, playlists, analytics, and admin activity. They must never be committed or shared. Keep API credentials in ignored `.env` files, rotate any credential that has been exposed, and obtain permission for every media asset distributed with the project.

This source repository does **not** include real credentials, private user data, or real/copyrighted music files.
