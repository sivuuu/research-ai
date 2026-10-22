FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application code
COPY backend/ /app/backend/
COPY sample_documents/ /app/sample_documents/
COPY sample_evaluation/ /app/sample_evaluation/

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python seed_data.py && python manage.py runserver 0.0.0.0:8000"]
