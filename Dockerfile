FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SAMSUNG_HOST=0.0.0.0 \
    SAMSUNG_PORT=8000 \
    SAMSUNG_DATA_DIR=/app/data \
    SAMSUNG_CACHE_PATH=/tmp/samsung-cache/plans.sqlite3

WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
COPY data/ ./data/
RUN pip install --no-cache-dir .

USER 65532:65532
EXPOSE 8000
CMD ["python", "-m", "samsung_engine.api"]
