# Multi-stage build for QSL Auto V2
FROM python:3.11-slim AS base
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi8 libjpeg62-turbo \
    fonts-dejavu-core libxml2 libxslt1.1 libssl3 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install -r requirements.txt

FROM base AS runtime
COPY . .
VOLUME ["/app/output", "/app/secrets", "/app/data"]
CMD ["python", "-m", "app.cli", "run", "--limit", "5"]
