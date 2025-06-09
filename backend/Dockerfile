FROM python:3.12-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Instalar Poetry
RUN pip install poetry==2.1.3

# Configurar Poetry para no crear entorno virtual
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copiar archivos de Poetry
COPY pyproject.toml poetry.lock ./

# Instalar dependencias
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Copiar código de la aplicación
COPY . .

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app_user && chown -R app_user:app_user /app
USER app_user

# Exponer puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 