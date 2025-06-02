# Orquix Backend

Backend FastAPI para el sistema de IA con Moderador Inteligente.

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.12+
- PostgreSQL 15 con pgvector
- Poetry para gestión de dependencias

### Instalación

1. Instalar dependencias:
```bash
poetry install
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

3. Aplicar migraciones:
```bash
poetry run alembic upgrade head
```

### Desarrollo

```bash
# Iniciar servidor de desarrollo
poetry run uvicorn app.main:app --reload

# Documentación del API
http://localhost:8000/docs
```

## 📁 Estructura

```
app/
├── api/v1/
│   └── endpoints/          # Endpoints del API
├── core/                   # Configuración central
├── crud/                   # Operaciones CRUD
├── models/                 # Modelos SQLModel
├── schemas/                # Esquemas Pydantic
├── services/               # Servicios de negocio
│   ├── ai_adapters/       # Adaptadores de IA
│   ├── ai_moderator.py    # Moderador v2.0
│   ├── ai_orchestrator.py # Orquestador
│   └── context_manager.py # Gestión de contexto
└── middleware/             # Middleware personalizado
```

## 🔗 Endpoints Principales

- `POST /api/v1/projects/{id}/query` - Consulta principal
- `GET /api/v1/projects` - Listar proyectos
- `POST /api/v1/projects` - Crear proyecto
- `GET /api/v1/health` - Estado del sistema

## 🧪 Testing

```bash
# Ejecutar todos los tests
poetry run pytest

# Tests con cobertura
poetry run pytest --cov=app

# Tests específicos
poetry run pytest tests/test_api/
```

## 🛠️ Tecnologías

- **FastAPI**: Framework web
- **SQLAlchemy**: ORM async
- **PostgreSQL**: Base de datos
- **Alembic**: Migraciones
- **Pydantic**: Validación
- **Poetry**: Dependencias 