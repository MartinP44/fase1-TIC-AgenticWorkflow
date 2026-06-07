FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app/ ./app/

# Inicializar la base de datos SQLite con datos de prueba
RUN python app/init_db.py

# Exponer el puerto de la aplicación
EXPOSE 8090

# Usuario no privilegiado para mayor seguridad
RUN useradd -m ctfuser && chown -R ctfuser:ctfuser /app
USER ctfuser

CMD ["python", "app/server.py"]
