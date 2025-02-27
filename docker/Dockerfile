FROM python:3.11-slim

# Instalar dependencias para PostGIS/GDAL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requeriments.txt .
RUN pip install --no-cache-dir -r requeriments.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.app:app"]
