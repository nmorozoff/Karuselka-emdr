FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV KARUSELKA_RUNTIME=cloud
ENV WORKER_STATE_BACKEND=dropbox
ENV ACCOUNTS_PAIRS_PATH=/app/config/accounts-pairs.json

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/lib ./lib
COPY app/main.py ./main.py
COPY app/config ./config

ENV PYTHONPATH=/app:/app/lib

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
