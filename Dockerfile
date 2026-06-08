FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create all required directories including static
RUN mkdir -p /app/logs /app/media /app/staticfiles /app/static

RUN python manage.py collectstatic --noinput --settings=medcenter.settings 2>/dev/null || true

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_data && gunicorn medcenter.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120"]
