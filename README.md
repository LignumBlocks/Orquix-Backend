# Orquix Backend

Backend para Orquix - Orquestador de IAs

## Requisitos

- Python 3.12+
- PostgreSQL 15 con pgvector
- Poetry para gestión de dependencias

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/orquix-backend.git
cd orquix-backend
```

2. Instalar dependencias con Poetry:
```bash
poetry install
```

3. Copiar el archivo de variables de entorno y configurarlo:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. Crear la base de datos y aplicar las migraciones:
```bash
poetry run alembic upgrade head
```

## Desarrollo

1. Iniciar el servidor de desarrollo:
```bash
poetry run uvicorn app.main:app --reload
```

2. Visitar la documentación del API:
```
http://localhost:8000/docs
```

## Estructura del Proyecto

```
app/
├── api/            # Endpoints del API
├── core/           # Configuración central
├── crud/          # Operaciones CRUD
├── models/        # Modelos SQLModel
├── schemas/       # Esquemas Pydantic
└── services/      # Servicios de negocio
```

## Endpoints Principales

- `POST /api/projects`: Crear nuevo proyecto
- `GET /api/projects`: Listar proyectos
- `GET /api/projects/{id}`: Obtener proyecto por ID
- `PUT /api/projects/{id}`: Actualizar proyecto
- `DELETE /api/projects/{id}`: Eliminar proyecto

## Tests

Ejecutar los tests:
```bash
poetry run pytest
```

## Licencia

MIT
