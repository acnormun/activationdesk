# Activation Desk API - FastAPI on Python 3.12 (same minor as the local .venv).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Unprivileged user owning /srv so the SQLite fallback (DATABASE_URL unset)
# can still write its file next to the app.
RUN useradd --create-home --home-dir /srv appuser \
    && chown -R appuser:appuser /srv
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + str(os.environ.get('PORT', 8000)) + '/health', timeout=2)"]

# Railway injects PORT: listen on it when set, 8000 elsewhere. Shell form so
# the variable expands when the container starts.
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
