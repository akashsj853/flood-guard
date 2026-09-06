# FloodGuard AI

**Real-Time AI Urban Flood Prediction, Early Warning & Decision Support Platform**

FloodGuard AI turns live weather and forecast data into localized flood-risk
assessments for city zones, with explainability (SHAP), population-exposure
estimates, actionable recommendations, an interactive risk map, and an
early-warning alert layer.

> ⚠️ **Decision support, not disaster management.** All predictions are
> *decision-support outputs*. They do **not** replace official
> disaster-management or meteorological warnings. Always follow instructions
> from local authorities.

---

## What this is

The platform is **weather-driven and fully software-only**. The original IoT /
sensor / ESP32 scope was deliberately removed and replaced with real-time
weather observations and forecasts:

- Real-time weather observations (Open-Meteo, no API key required)
- Hourly weather **forecast**
- Precipitation **forecast** (24h + multi-hour horizon)
- GIS / terrain attributes per zone (elevation, slope, drainage, impervious
  surface, population) loaded from data, not sensors

No hardware, no ESP32, no physical sensors are used or required. No weather API
keys are exposed to the frontend.

### Demo / offline mode

If the weather provider is unreachable (or you pass `demo=true`), the platform
falls back to clearly-labelled **demo data**. Demo values are never presented as
real-time data. This makes the whole stack runnable from a clean install with
zero external dependencies.

---

## Architecture

```
┌──────────────────┐      /api/*       ┌──────────────────────────┐
│  React + Vite    │  ───────────────▶ │  FastAPI (Python)        │
│  (Leaflet,       │   (proxied)       │  - WeatherService        │
│   Recharts,      │ ◀───────────────  │  - Risk engine           │
│   Tailwind)      │   JSON             │  - ML prediction         │
│  Nginx in prod   │                   │  - Recommendation engine │
└──────────────────┘                   │  - Alerts / Simulation   │
                                       └────────────┬─────────────┘
                                                    │
                                       ┌────────────┴─────────────┐
                                       │  Weather provider        │
                                       │  (Open-Meteo, no key)    │
                                       └──────────────────────────┘
```

- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2 (SQLite dev / PostgreSQL prod).
- **ML**: features → RandomForest (selected over XGBoost on recall) with a
  tuned probability threshold; SHAP for explainability; metrics persisted to
  `backend/app/ml/model_metadata.json`.
- **Frontend**: React 18 + Vite 5 + Tailwind 3 + React Leaflet 4 + Recharts 2.
- **Deploy**: Docker Compose (backend uvicorn, frontend Nginx serving the
  static build and proxying `/api`).

---

## Risk levels

| Score | Level       |
|-------|-------------|
| 0–20  | LOW         |
| 20–40 | MODERATE    |
| 40–60 | HIGH        |
| 60–80 | VERY HIGH   |
| 80–100| CRITICAL    |

Model selection prioritizes **recall** to minimize false negatives (missed
flood events).

---

## Quick start (local, no Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env               # optional; defaults work out of the box
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health:    http://localhost:8000/api/health

> The first run auto-creates the SQLite DB and seeds zone data if empty.

### Frontend

```bash
cd frontend
npm install
# If your npm enforces an allow-scripts gate, approve the build tool first:
#   npm approve-scripts esbuild
npm run dev                       # http://localhost:5173  (proxies /api -> :8000)
# production build:
npm run build && npm run preview
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`.

---

## Running with Docker

```bash
# From the repo root:
docker compose up --build
#   frontend:  http://localhost:5173
#   backend:   http://localhost:8000/docs
```

Run the Vite dev server instead of the static build:

```bash
docker compose --profile dev up --build   # frontend dev on :5174
```

Override the database (PostgreSQL example) and weather provider via env:

```bash
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/floodguard \
WEATHER_PROVIDER=openmeteo \
docker compose up --build
```

---

## API endpoints

| Method | Path                              | Purpose                                  |
|--------|-----------------------------------|------------------------------------------|
| GET    | `/api/health`                     | Liveness / readiness                     |
| GET    | `/api/weather/current`            | Current observations (`?lat&lon`)        |
| GET    | `/api/weather/forecast`           | Hourly forecast (`?lat&lon`)             |
| GET    | `/api/weather/rainfall`           | Precipitation obs + forecast (`?lat&lon`)|
| POST   | `/api/predict`                    | Zone flood-risk prediction               |
| GET    | `/api/zones`                      | All zones (`?demo=true`)                 |
| GET    | `/api/zones/{id}`                 | Single zone                              |
| GET    | `/api/alerts`                     | Active alerts (`?demo=true`)             |
| POST   | `/api/alerts/{id}/acknowledge`    | Acknowledge an alert                     |
| POST   | `/api/simulation`                 | What-If scenario simulation              |
| GET    | `/api/analytics`                  | Model + zone analytics                   |

Append `?demo=true` to any supported endpoint to use offline demo data.

---

## ML training pipeline

The model is reproducible from a clean install:

```bash
cd ml
pip install -r ../backend/requirements.txt   # or install pandas/sklearn/xgboost/shap
python train.py
```

`ml/train.py` loads `ml/data/*`, runs feature engineering
(`ml/feature_engineering.py`), trains and compares candidate models
(RandomForest vs XGBoost), selects on recall, tunes the decision threshold,
computes SHAP-based explanations, and persists the model + metadata to
`backend/app/ml/`.

---

## Tests

Required test suites (backend, `pytest`):

```bash
cd backend
pytest
```

Covers: weather service, feature engineering, prediction, risk engine,
recommendation engine, simulation, zones, and alerts.

---

## Configuration

Copy `backend/env.example` to `backend/.env` and adjust. Important variables:

- `DATABASE_URL` — SQLite (default) or PostgreSQL.
- `WEATHER_PROVIDER` — `openmeteo` (default, no key). Other providers wire in
  behind `WeatherService`.
- `REDIS_URL` — optional Redis connection URL. When set, weather and prediction
  cache entries are shared across backend workers; without it, an in-process
  TTL cache is used.
- `JWT_SECRET_KEY` — secret used to sign access and refresh cookies. Set a long,
  random value outside development; the built-in default is development-only.
- `HOST` / `PORT` — uvicorn bind.

Performance endpoints:

- `POST /api/predictions/bulk` accepts `{ "zone_ids": ["Z001", "Z002"] }` and
  returns predictions for multiple zones in one request.
- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/admin-login`, `POST /api/auth/refresh`,
  `GET /api/auth/me`, and `POST /api/auth/logout` provide cookie-based JWT auth.
  Access and refresh tokens are `HttpOnly`; public registration always creates a
  citizen account. Operators/admins must be provisioned separately.
- `POST /api/auth/admin-register` is available from the Admin access page and
  creates an admin session immediately.
- `GET/POST /api/profile/locations` and `GET/POST /api/profile/subscriptions`
  support saved zones and in-app risk thresholds for authenticated users.
- `GET /api/zones/{zone_id}/history?limit=30` returns persisted risk snapshots
  for public trend charts. Simulation, analytics, and alert acknowledgement
  require an operator or admin session.
- GET responses include short-lived `Cache-Control` and `ETag` headers. Requests
  over 120 per minute per client receive `429` to protect public deployments.

**Never commit `.env` or any secret.** The frontend never receives weather API
keys; all provider calls happen server-side.

---

## Project layout

```
floodguard-ai/
├── backend/            FastAPI app, ML, services, tests
│   ├── app/
│   │   ├── api/        route routers (weather, zones, predictions, alerts, simulation, analytics)
│   │   ├── ml/         model + metadata
│   │   ├── services/   weather, risk, prediction, recommendation, impact, zone
│   │   └── models/     db models, schemas
│   └── tests/          required test suites
├── frontend/           React + Vite + Tailwind + Leaflet
├── ml/                 training pipeline + data
├── data/               shared data (geojson, samples)
├── docs/               documentation assets
├── docker-compose.yml
└── README.md
```

---

## Disclaimer

FloodGuard AI is a **decision-support tool**. Predictions are statistical
estimates derived from weather and zone attributes and may be wrong. They must
not be used as the sole basis for life-safety decisions. Official warnings from
meteorological and disaster-management agencies take precedence.
# flood-guard
