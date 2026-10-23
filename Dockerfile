FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY application/ ./application/

ENV PYTHONPATH=/app

RUN useradd -m -u 1001 ctfuser && chown -R ctfuser:ctfuser /app
USER ctfuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn application.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
