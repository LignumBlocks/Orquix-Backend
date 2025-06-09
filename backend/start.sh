#!/bin/bash

echo "🚀 Iniciando deployment de Orquix Backend..."

# Configurar Poetry
export POETRY_NO_INTERACTION=1
export POETRY_VENV_IN_PROJECT=1

# Verificar que Poetry esté instalado
if ! command -v poetry &> /dev/null; then
    echo "📦 Instalando Poetry..."
    pip install poetry==2.1.3
fi

# Instalar dependencias si no están instaladas
echo "📚 Verificando dependencias..."
poetry install --only=main

# Aplicar migraciones de base de datos
echo "🗄️ Aplicando migraciones de base de datos..."
poetry run alembic upgrade head

# Verificar que las migraciones fueron exitosas
if [ $? -eq 0 ]; then
    echo "✅ Migraciones aplicadas exitosamente"
else
    echo "❌ Error aplicando migraciones"
    exit 1
fi

# Iniciar la aplicación
echo "🌐 Iniciando servidor FastAPI..."
echo "🔧 Puerto: ${PORT:-8000}"
echo "🌍 Host: 0.0.0.0"

poetry run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 