# Railway deployment notes (DupeFinder)

This repo is a **monorepo** (`backend/`, `ml-engine/`, `frontend-app/`, `mobile/`, …). Railway builds work best when the Docker build context includes everything the backend imports at runtime.

## Service A — API (FastAPI)

### Recommended Railway settings

- **Root Directory**: `.` (repo root)
- **Dockerfile path**: `Dockerfile.railway-api`
- **Start command**: leave empty (Dockerfile `CMD` runs uvicorn on `$PORT`)

### Why repo-root context?

The admin scraping → reindex flow imports `ml-engine` (see `backend/app/api/routes/admin_new.py`). If Railway builds only `backend/` as the context, `ml-engine/` is not present in the image.

### Dependency install note (image size)

The production API image installs Python dependencies from **`backend/requirements-railway-api.txt`** (this intentionally omits Playwright/Chromium; those live in the scraper worker image).

The `ml-engine/` directory is still copied into the image for imports/scripts.

### Service C — Scraper worker (Playwright/Chromium)

Railway has a hard **Docker image size** cap; splitting scraping into a second service keeps the API/ML image smaller.

#### Recommended Railway settings

- **Root Directory**: `.` (repo root)
- **Dockerfile path**: `Dockerfile.railway-scraper`
- **Start command**: leave empty (Dockerfile `CMD` runs uvicorn on `$PORT`)

#### Required env vars (both services)

Set the same shared secret on **both** services:

- **`SCRAPER_SERVICE_TOKEN`**: shared secret (sent as `X-Scraper-Token`)

On the **API** service, also set:

- **`SCRAPER_SERVICE_URL`**: public URL of the scraper worker (**no trailing slash**), e.g. `https://<scraper>.up.railway.app`

On the **scraper** service, you only need `SCRAPER_SERVICE_TOKEN` for auth (Mongo is **not** required for the worker unless you call Excel-based helpers that write to Mongo).

#### How communication works

Admin scraping (`backend/app/api/routes/admin_new.py`) will:

- If `SCRAPER_SERVICE_URL` is set **and** `SCRAPER_SERVICE_TOKEN` is set: call `POST {SCRAPER_SERVICE_URL}/scrape/url` for each listing/home URL.
- Otherwise: fall back to in-process `ProductScraper` (local dev parity).

The API service still handles **Mongo writes** + **post-job reindex** exactly like local.

### Persistent volume (indices/maps/images; not Mongo)

Mount a Railway volume and point the backend to it with env vars:

- **`DATA_DIR`**: directory served at `/data` (product images)
- **`FAISS_INDEX_DIR`**: directory containing `*.index` files
- **`FAISS_ID_MAP_DIR`**: directory containing `*.pkl` id maps
- Optional override:
  - **`BACKEND_APP_ML_DIR`**: if you want a single parent directory for both indices + maps

The API also uses:

- **`SEARCH_UPLOAD_DIR`**: temp uploads for image search (defaults to `<repo>/data/uploads`)

### Mongo settings

The backend reads Mongo settings from `backend/app/core/config.py` / environment variables (Pydantic settings).

The incremental reindex script (`ml-engine/scripts/reindex_new_products.py`) prefers these env vars when present:

- `MONGO_URI` (or `MONGODB_URI` / `MONGODB_URL`)
- `MONGO_DB_NAME` (or `MONGODB_DATABASE` / `DATABASE_NAME`)
- `MONGO_COLLECTION` (optional; falls back to `ml-engine/config.yaml`)

## Service B — Web (Vite)

### Recommended Railway settings

- **Root Directory**: `frontend-app`
- **Dockerfile path**: `Dockerfile`

### Build-time API URL

Vite embeds `import.meta.env.VITE_*` at **build time**.

Set **`VITE_API_BASE`** in Railway for the frontend service (same value you want compiled into the bundle), e.g. your public API `https://...` (**no trailing slash**).

### Admin dashboard note

There is **no separate** `admin-dashboard/` app in this repository snapshot.

The admin UI is part of **`frontend-app/`** (see `frontend-app/src/pages/AdminDashboard*.jsx` and `frontend-app/src/lib/adminApiUrl.js`), so **one** deployed web service covers user + admin routes.

## Mobile (Flutter)

Docker does not package Flutter. For “dev build points to Railway”, set the mobile client’s API base URL to the public Railway API domain.
