FROM python:3.11-slim
WORKDIR /connector
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_DEFAULT_TIMEOUT=120
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --prefer-binary --timeout 120 -r requirements.txt
COPY . .
EXPOSE 5557
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5557"]
