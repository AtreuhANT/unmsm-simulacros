# Imagen base ligera de Python 3.11
FROM python:3.11-slim

# Evitar generación de archivos .pyc y forzar salida inmediata a consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación
COPY . .

# Puerto expuesto por Flask / Gunicorn
EXPOSE 5000

# Comando de inicio del servidor
CMD ["python", "app.py"]
