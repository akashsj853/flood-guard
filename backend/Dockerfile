# FloodGuard AI — backend image
# FastAPI + uvicorn. Weather comes from Open-Meteo (no API key).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System libs: libgomp is required by XGBoost / scikit-learn native code.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# The trained model + metadata live under app/ml (persisted by ml/train.py).
# SQLite is the default dev DB; override DATABASE_URL for PostgreSQL in prod.
ENV DATABASE_URL=sqlite:///./floodguard.db
ENV HOST=0.0.0.0
ENV PORT=8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
