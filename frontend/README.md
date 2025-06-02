# Orquix Frontend

Frontend React + Vite para el sistema de IA con Moderador Inteligente.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
yarn install

# Desarrollo
yarn dev  # http://localhost:5173

# Build
yarn build
yarn preview
```

## 🛠️ Stack Tecnológico

- **React 19**: Biblioteca UI
- **Vite 6.3**: Build tool y dev server
- **Tailwind CSS 3.4**: Framework de estilos
- **JavaScript**: Lenguaje principal (sin TypeScript)
- **Lucide React**: Iconografía
- **Axios**: Cliente HTTP
- **Zustand**: Gestión de estado global
- **React Router**: Navegación

## 📁 Estructura de Directorios

```
src/
├── components/           # Componentes React
│   ├── ui/              # Componentes UI básicos
│   ├── layout/          # Componentes de layout
│   └── forms/           # Componentes de formularios
├── pages/               # Páginas/Vistas principales
├── hooks/               # Custom hooks
├── services/            # Llamadas a la API
├── stores/              # Estado global (Zustand)
├── utils/               # Utilidades
├── config.js            # Configuración de la app
└── index.css            # Estilos Tailwind CSS
```

## ⚙️ Configuración

### Variables de Entorno (Vite)
- `VITE_API_BASE_URL`: URL del backend (default: http://localhost:8000)
- `VITE_APP_NAME`: Nombre de la aplicación
- `VITE_APP_VERSION`: Versión de la aplicación

### Tailwind CSS
- Configuración en `tailwind.config.js`
- Clases personalizadas definidas en `src/index.css`:
  - `.btn-primary`: Botón principal
  - `.btn-secondary`: Botón secundario
  - `.card`: Tarjeta básica

### Endpoints del Backend
Configurados en `src/config.js`:
- `/api/v1/auth` - Autenticación
- `/api/v1/projects` - Proyectos
- `/api/v1/feedback` - Feedback
- `/api/v1/health` - Estado del sistema

## 🎨 Componentes UI Personalizados

### Botones
```jsx
<button className="btn-primary">Botón Principal</button>
<button className="btn-secondary">Botón Secundario</button>
```

### Tarjetas
```jsx
<div className="card p-6">
  <h3>Título</h3>
  <p>Contenido</p>
</div>
```

## 🔗 Integración con Backend

El frontend está configurado para conectarse con el backend FastAPI:
- **Base URL**: `http://localhost:8000`
- **Autenticación**: JWT tokens
- **API Docs**: `http://localhost:8000/docs`

## 🧪 Testing

```bash
yarn test      # Ejecutar tests
yarn lint      # Linting con ESLint
```

## 📦 Build y Deploy

```bash
yarn build     # Crear build de producción
yarn preview   # Preview del build
```

## 🎯 Próximos Pasos

1. **Dashboard de Proyectos**: Interfaz principal de gestión
2. **Chat de Investigación**: Interfaz de consulta con IAs
3. **Panel de Moderador**: Configuración y resultados
4. **Autenticación**: Login con Google OAuth
5. **Historial**: Navegación de sesiones pasadas

## 💡 Estado Actual

✅ **Configurado y Funcionando:**
- React + Vite
- Tailwind CSS v3.4
- Estructura de directorios
- Configuración base
- Componente de prueba
- Conexión con backend (API_BASE_URL)

⏳ **Pendiente:**
- Componentes específicos de Orquix
- Integración con endpoints reales
- Autenticación con NextAuth.js
- Estado global con Zustand
