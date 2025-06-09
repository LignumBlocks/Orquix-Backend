# Orquix - Sistema de IA con Moderador Inteligente

**Monorepo Fullstack**: Backend FastAPI + Frontend React con Vite

## 🏗️ Arquitectura

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React + Vite + Tailwind CSS
- **IA**: Orquestación de múltiples proveedores (OpenAI, Anthropic)
- **Moderador**: IA v2.0 con meta-análisis profesional
- **Deployment**: Render (Backend Web Service + Frontend Static Site)

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
│   ├── public/
│   │   └── _redirects         # Redirects para SPA en Render
│   └── package.json           # Dependencias Node.js
├── shared/                     # Tipos compartidos
│   └── types/                 # Interfaces TypeScript
├── docs/                       # Documentación
├── render.yaml                # Configuración de deployment
├── DEPLOYMENT.md              # Guía completa de deployment
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

- **Dashboard**: Interface principal con layout de 3 columnas
- **Projects**: Gestión de proyectos de investigación
- **Chat**: Interfaz de consulta con Moderador IA v2.0
- **AI Status**: Monitoreo en tiempo real de proveedores

## 🌐 Deployment en Producción

### Opción B Implementada: Static Site + Web Service

```
┌─────────────────────────────────────────────────────────────┐
│                     RENDER DEPLOYMENT                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🌐 Frontend (Static Site)     🔗 Backend (Web Service)   │
│  ┌─────────────────────────┐   ┌─────────────────────────┐  │
│  │ orquix-frontend         │   │ orquix-backend          │  │
│  │ React + Vite            │──▶│ FastAPI + Poetry        │  │
│  │ Tailwind CSS            │   │ PostgreSQL + pgvector   │  │
│  │ Static Files            │   │ AI Orchestration        │  │
│  │ _redirects for SPA      │   │ Moderator v2.0          │  │
│  └─────────────────────────┘   └─────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### URLs de Producción

- **Frontend**: `https://orquix-frontend.onrender.com`
- **Backend API**: `https://orquix-backend.onrender.com`
- **API Docs**: `https://orquix-backend.onrender.com/docs`

### Deployment Rápido

```bash
# 1. Configurar variables de entorno en Render Dashboard
# 2. Push al repositorio
git push origin main

# 3. Render deployará automáticamente ambos servicios
# Backend: Web Service con PostgreSQL
# Frontend: Static Site con CDN global
```

**Ver [DEPLOYMENT.md](./DEPLOYMENT.md) para guía completa** 📚

## ✨ Características

### Backend
- ✅ **FastAPI**: API REST moderna y rápida
- ✅ **Moderador IA v2.0**: Meta-análisis profesional
- ✅ **Multi-Provider**: OpenAI + Anthropic
- ✅ **PostgreSQL**: Con extensión pgvector
- ✅ **Autenticación**: JWT compatible con NextAuth.js
- ✅ **Rate Limiting**: Protección contra abuso
- ✅ **Health Checks**: Monitoreo completo

### Frontend
- ✅ **React 19**: Última versión con Vite 6.3
- ✅ **Tailwind CSS v4**: Styling moderno
- ✅ **Responsive**: Layout adaptativo de 3 columnas
- ✅ **Real-time**: Estado de IAs en vivo
- ✅ **SPA Routing**: Navegación fluida
- ✅ **API Integration**: Comunicación optimizada

### Deployment
- ✅ **Render Ready**: Configuración completa
- ✅ **Static Site**: Frontend con CDN global
- ✅ **Auto-scaling**: Backend escalable
- ✅ **SSL/HTTPS**: Certificados automáticos
- ✅ **Preview URLs**: Deploy preview para PRs

## 🧪 Testing

### Desarrollo Local
```bash
# Verificar estado de ambos servicios
./dev-status.sh

# Tests del backend
yarn test:backend

# Tests del frontend  
yarn test:frontend
```

### Producción
```bash
# Health check del backend
curl https://orquix-backend.onrender.com/api/v1/health

# Verificar frontend
curl https://orquix-frontend.onrender.com
```

## 🎯 Estado del Proyecto

### ✅ Completado
- Arquitectura completa del sistema
- Moderador IA v2.0 con meta-análisis
- Interface de usuario responsive
- Orquestación de múltiples IAs
- Deployment en Render listo
- Documentación completa

### 🔄 En Desarrollo
- Autenticación con Google OAuth
- Sistema de usuarios avanzado
- Métricas y analytics
- Tests de integración

### 📋 Roadmap
- Integración con más proveedores de IA
- Sistema de plugins
- API pública
- Aplicación móvil

## 📚 Documentación

- [**DEPLOYMENT.md**](./DEPLOYMENT.md) - Guía completa de deployment
- [**docs/**](./docs/) - Documentación técnica completa
- [**frontend/README.md**](./frontend/README.md) - Documentación del frontend
- **API Docs**: Disponible en `/docs` del backend

## 🤝 Contribuir

1. Fork el repositorio
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 🙋‍♂️ Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/orquix-backend/issues)
- **Documentación**: [docs/](./docs/)
- **Email**: tu-email@ejemplo.com

---

**🚀 ¡Orquix está listo para producción!** Deployment completo en Render con Backend + Frontend optimizado.
