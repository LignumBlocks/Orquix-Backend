# Orquix - Sistema de IA con Moderador Inteligente

**Monorepo Fullstack**: Backend FastAPI + Frontend React con Vite

## 🏗️ Arquitectura

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React + Vite + Tailwind CSS
- **IA**: Orquestación de múltiples proveedores (OpenAI, Anthropic)
- **Moderador**: IA v2.0 con meta-análisis profesional

## 📁 Estructura del Proyecto

```
orquix-backend/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # Endpoints del API
│   │   ├── core/              # Configuración central
│   │   ├── crud/              # Operaciones CRUD
│   │   ├── models/            # Modelos SQLModel
│   │   ├── schemas/           # Esquemas Pydantic
│   │   └── services/          # Servicios de negocio
│   ├── alembic/               # Migraciones de BD
│   ├── tests/                 # Tests del backend
│   └── pyproject.toml         # Dependencias Python
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/             # Páginas/Vistas
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API calls
│   │   └── stores/            # Estado global (Zustand)
│   └── package.json           # Dependencias Node.js
├── shared/                     # Tipos compartidos
│   └── types/                 # Interfaces TypeScript
├── docs/                       # Documentación
└── package.json               # Scripts del monorepo
```

## 🚀 Inicio Rápido

### Prerrequisitos

- **Python 3.12+** con Poetry
- **Node.js 18+** con Yarn
- **PostgreSQL 15** con pgvector

### 1. Configuración Inicial

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/orquix-backend.git
cd orquix-backend

# Instalar dependencias de ambos proyectos
yarn setup
```

### 2. Configuración del Backend

```bash
# Copiar variables de entorno
cp backend/.env.example backend/.env
# Editar backend/.env con tus configuraciones

# Aplicar migraciones
cd backend && poetry run alembic upgrade head
```

### 3. Desarrollo

```bash
# Ejecutar backend y frontend simultáneamente
yarn dev

# O ejecutar por separado:
yarn dev:backend    # FastAPI en http://localhost:8000
yarn dev:frontend   # React en http://localhost:5173
```

## 📚 Scripts Disponibles

```bash
# Desarrollo
yarn dev              # Backend + Frontend simultáneamente
yarn dev:backend      # Solo backend (FastAPI)
yarn dev:frontend     # Solo frontend (React)

# Construcción
yarn build            # Build del frontend
yarn build:frontend   # Build específico del frontend

# Testing
yarn test             # Tests de backend + frontend
yarn test:backend     # Tests del backend (pytest)
yarn test:frontend    # Tests del frontend

# Utilidades
yarn lint             # Linting del frontend
yarn preview          # Preview del build del frontend
```

## 🔗 Endpoints Principales

### Backend API (http://localhost:8000)

- **Documentación**: `/docs` (Swagger UI)
- **Autenticación**: `/api/v1/auth/*`
- **Proyectos**: `/api/v1/projects/*`
- **Consulta Principal**: `POST /api/v1/projects/{id}/query` ⭐
- **Historial**: `/api/v1/projects/{id}/interaction_events/*`
- **Feedback**: `/api/v1/feedback/*`
- **Salud**: `/api/v1/health/*`

### Frontend (http://localhost:5173)

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
