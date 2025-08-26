# Multi-stage build for QSL Auto V2
FROM python:3.11-slim AS base
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfribidi0 \
    libgdk-pixbuf-2.0-0 libffi8 libjpeg62-turbo \
    fonts-dejavu-core fonts-dejavu-extra fonts-liberation libxml2 libxslt1.1 libssl3 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --prefer-binary --timeout 120 -r requirements.txt

FROM base AS runtime
COPY . .
RUN chmod +x /app/start.sh
VOLUME ["/app/output", "/app/secrets", "/app/data"]
CMD ["/app/start.sh"]
