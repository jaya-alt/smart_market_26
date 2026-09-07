FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python init_db.py && python -m app.database.seed

# Default process: the Telegram bot (long-polling).
# Override the command to run the FastAPI app instead, e.g.:
#   docker run ... uvicorn app.main:app --host 0.0.0.0 --port 8000
CMD ["python", "-m", "app.telegram.bot"]
