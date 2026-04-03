FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python en modo desarrollo
# Sin caché para que reconozca cambios en requirements.txt
RUN pip install -r requirements.txt

# Copiar código de la aplicación (opcional, se monta con volumen en desarrollo)
COPY . .

# Exponer puerto
EXPOSE 8080

# Comando por defecto
# En desarrollo se ejecutará con --reload desde docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
