FROM python:3.12-slim AS app
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .

# Test image (compose profile "test"): adds pytest; the repo is mounted at /repo when it runs.
FROM app AS test
RUN pip install --no-cache-dir ".[dev]"

FROM app AS runtime
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed.load && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
