FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY apps/dashboard/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy dashboard app code
COPY apps/dashboard/ .

# Create shared templates directory (will be mounted at runtime)
RUN mkdir -p /app/shared_templates

EXPOSE 5550

CMD ["python", "dashboard.py"]
