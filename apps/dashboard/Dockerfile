FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY apps/dashboard/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy dashboard app code
COPY apps/dashboard/ .
# Copy shared templates
COPY ../shared/templates /app/shared_templates

EXPOSE 5550

CMD ["python", "dashboard.py"]
