# syntax=docker/dockerfile:1

FROM python:3.11-slim

RUN useradd -m botuser

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Use --chown to set ownership during copy
COPY --chown=botuser:botuser . .

# Create logs directory with proper permissions (future-proofing)
RUN mkdir -p /app/logs && chown botuser:botuser /app/logs

USER botuser

CMD ["python", "bot.py"]
