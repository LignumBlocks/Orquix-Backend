# 🚀 **DEPLOYMENT GUIDE - ORQUIX FULLSTACK EN RENDER**

## 📋 **RESUMEN EJECUTIVO**

Esta guía te ayudará a deployar **Orquix Fullstack** (Backend FastAPI + Frontend React) en **Render** usando PostgreSQL 15 con pgvector.

---

## 🎯 **PRE-REQUISITOS**

### **1. Cuentas Necesarias**
- ✅ **Cuenta en Render**: [render.com](https://render.com)
- ✅ **Repositorio GitHub**: Con código de Orquix Backend
- ✅ **OpenAI API Key**: Para GPT-4o-mini y GPT-3.5-Turbo
- ✅ **Anthropic API Key**: Para Claude-3 Sonnet/Haiku

### **2. Archivos Generados** ✅
Los siguientes archivos ya están listos en tu proyecto:

```
Orquix-Backend/
├── render.yaml                     # ✅ Configuración completa de servicios (Backend + Frontend)
├── backend/
│   ├── Dockerfile                 # ✅ Imagen Docker optimizada
│   ├── start.sh                   # ✅ Script de inicio con migraciones
│   ├── requirements.txt           # ✅ Dependencias Python
│   └── app/core/config.py         # ✅ Configuración actualizada
├── frontend/
│   ├── public/_redirects          # ✅ Redirects para SPA
│   ├── vite.config.js             # ✅ Configuración optimizada de Vite
│   └── src/config.js              # ✅ Configuración dinámica de API URLs
└── .gitignore                     # ✅ Archivos excluidos
```

---

## 🏗️ **ARQUITECTURA DE DEPLOYMENT**

### **Opción B Implementada: Frontend Static Site**

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

### **Ventajas de la Opción B:**
- ✅ **Más económico**: Static Site es gratuito hasta cierto límite
- ✅ **Más rápido**: CDN global automático
- ✅ **Más escalable**: Infinitas requests simultáneas
- ✅ **SSL automático**: HTTPS habilitado por defecto
- ✅ **Deploy Preview**: URLs de preview para cada PR

---

## 🔧 **PASOS DE DEPLOYMENT**

### **PASO 1: Preparar el Repositorio GitHub**

```bash
# 1. Agregar todos los archivos nuevos
git add .

# 2. Commit con mensaje descriptivo
git commit -m "🚀 feat: Add Render deployment configuration

- Add render.yaml with web service and PostgreSQL config
- Add Dockerfile optimized for Python 3.12 + Poetry
- Add start.sh script with database migrations
- Add requirements.txt generated from Poetry
- Update config.py to support DATABASE_URL from Render
- Add frontend static site configuration
- Add _redirects for SPA routing
- Update CORS for frontend domain
- Add comprehensive .gitignore
- Add deployment documentation"

# 3. Push al repositorio
git push origin main
```

### **PASO 2: Configurar Render**

#### **2.1. Crear Nueva Aplicación**
1. Ve a [render.com](https://render.com) y haz login
2. Click **"New +"** → **"Blueprint"**
3. Conecta tu repositorio GitHub
4. Selecciona el repositorio **Orquix-Backend**

#### **2.2. Configurar Variables de Entorno** 🔑
En el dashboard de Render, configura estas variables **ANTES** del deployment:

**BACKEND (orquix-backend):**
```bash
# === AI API KEYS (REQUERIDO) ===
OPENAI_API_KEY=sk-tu-clave-openai-aqui
ANTHROPIC_API_KEY=sk-ant-tu-clave-anthropic-aqui

# === AUTH OPCIONAL (Para futuro) ===
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret
JWT_PUBLIC_KEY=tu_nextauth_public_key

# === Las demás variables se auto-configuran ===
```

**FRONTEND (orquix-frontend):**
```bash
# Las variables del frontend se auto-configuran desde render.yaml
# Solo cambiar si necesitas URLs diferentes:
VITE_API_BASE_URL=https://orquix-backend.onrender.com
```

**⚠️ IMPORTANTE**: Sin las API keys del backend, el deployment fallará.

### **PASO 3: Deployment Automático**

1. **Render detectará** el archivo `render.yaml`
2. **Creará automáticamente**:
   - 🗄️ Base de datos PostgreSQL 15
   - 🌐 Servicio web Python (Backend)
   - 📱 Static Site (Frontend)
   - 🔧 Variables de entorno
3. **Ejecutará** las migraciones automáticamente
4. **Iniciará** ambos servicios

---

## 🏥 **VERIFICACIÓN DEL DEPLOYMENT**

### **1. Backend Health Check**
```bash
curl https://orquix-backend.onrender.com/api/v1/health
```

**Respuesta esperada**:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0",
    "environment": "production"
}
```

### **2. Frontend Verificación**
- 🌐 **URL Principal**: `https://orquix-frontend.onrender.com`
- 📱 **Interfaz Responsive**: Verificar las 3 columnas
- 🔄 **Routing SPA**: Navegar entre rutas
- 🔗 **Conexión API**: Verificar comunicación con backend

### **3. Documentación API**
- 📚 **Swagger**: `https://orquix-backend.onrender.com/docs`
- 📖 **ReDoc**: `https://orquix-backend.onrender.com/redoc`

### **4. Endpoints Clave**
```bash
# Backend
GET https://orquix-backend.onrender.com/api/v1/health
POST https://orquix-backend.onrender.com/api/v1/projects
POST https://orquix-backend.onrender.com/api/v1/projects/{id}/query

# Frontend
GET https://orquix-frontend.onrender.com
GET https://orquix-frontend.onrender.com/projects
```

---

## 🛠️ **CONFIGURACIÓN AVANZADA**

### **1. Dominio Personalizado**

**Para el Backend:**
En Render Dashboard → orquix-backend:
1. Ve a **"Settings"** → **"Custom Domains"**
2. Agrega: `api.tudominio.com`
3. Configura DNS CNAME: `api.tudominio.com → orquix-backend.onrender.com`

**Para el Frontend:**
En Render Dashboard → orquix-frontend:
1. Ve a **"Settings"** → **"Custom Domains"**
2. Agrega: `app.tudominio.com`
3. Configura DNS CNAME: `app.tudominio.com → orquix-frontend.onrender.com`

### **2. Actualizar URL del Backend**
Si cambias el dominio del backend, actualizar:

```bash
# En render.yaml o variables de entorno
VITE_API_BASE_URL=https://api.tudominio.com
```

### **3. Scaling del Backend**
```yaml
# En render.yaml (solo backend - frontend es automático)
plan: starter  # Cambiar a: standard, pro, etc.
```

---

## 🔍 **TROUBLESHOOTING**

### **❌ Frontend: Build Failed**
```bash
# Verificar en logs de Render:
"yarn not found" → Render instala automáticamente
"Build failed" → Verificar package.json y dependencies
```

### **❌ Frontend: SPA Routing No Funciona**
```bash
# Verificar que existe:
frontend/public/_redirects

# Con contenido:
/* /index.html 200
```

### **❌ Frontend: No Conecta con Backend**
```bash
# Verificar CORS en backend/app/main.py:
allowed_origins = [
    "https://orquix-frontend.onrender.com",
    # ... otros dominios
]

# Verificar URL en frontend:
VITE_API_BASE_URL=https://orquix-backend.onrender.com
```

### **❌ Backend: Database Connection**
```bash
# Verificar que pgvector esté habilitado:
CREATE EXTENSION IF NOT EXISTS vector;
```

### **❌ Backend: API Keys**
```bash
# En logs verás:
"OPENAI_API_KEY not configured"
```
**Solución**: Configurar variables de entorno en Render.

---

## 📊 **MONITOREO Y LOGS**

### **1. Logs en Tiempo Real**
En Render Dashboard:
- **Backend**: orquix-backend → "Logs"
- **Frontend**: orquix-frontend → "Logs" (build logs)

### **2. Health Monitoring**
```bash
# Backend health checks automáticos cada 30s:
GET https://orquix-backend.onrender.com/api/v1/health

# Frontend está siempre disponible (Static Site)
```

### **3. Performance**
```bash
# Backend: CPU, memoria, requests en dashboard
# Frontend: Automáticamente escalado, CDN global
```

---

## 🎉 **DEPLOYMENT EXITOSO**

Si todo está correcto, verás:

**Backend:**
```bash
✅ Database migrations applied successfully
✅ Orquix Backend v1.0.0 started
✅ Environment: production
✅ AI Providers: OpenAI, Anthropic
✅ Rate Limiting: Enabled
✅ Health Check: /api/v1/health
```

**Frontend:**
```bash
✅ Frontend build completed successfully
✅ Static files deployed to CDN
✅ SPA routing configured
✅ Connected to backend API
```

---

## 🔗 **RECURSOS ADICIONALES**

- 📖 **Documentación Render**: [render.com/docs](https://render.com/docs)
- 🎨 **Render Static Sites**: [render.com/docs/static-sites](https://render.com/docs/static-sites)
- 🤖 **OpenAI API**: [platform.openai.com](https://platform.openai.com)
- 🧠 **Anthropic API**: [console.anthropic.com](https://console.anthropic.com)
- 🗄️ **PostgreSQL + pgvector**: [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)

---

## 🆘 **SOPORTE**

Si encuentras problemas:

1. **Revisa los logs** en Render Dashboard (ambos servicios)
2. **Verifica las variables de entorno** en cada servicio
3. **Confirma CORS** en el backend para el dominio del frontend
4. **Revisa la documentación** de Render para Static Sites

---

## 📝 **CHECKLIST DE DEPLOYMENT**

### **Pre-deployment:**
- [ ] Repositorio GitHub actualizado
- [ ] API Keys de OpenAI y Anthropic disponibles
- [ ] Cuenta en Render configurada

### **Backend:**
- [ ] Variables de entorno configuradas
- [ ] Health check respondiendo
- [ ] CORS configurado para frontend
- [ ] Migraciones aplicadas

### **Frontend:**
- [ ] Build exitoso
- [ ] _redirects configurado
- [ ] URL del backend correcta
- [ ] Routing SPA funcionando

### **Testing:**
- [ ] Frontend carga correctamente
- [ ] Backend responde a health check
- [ ] Comunicación frontend-backend funciona
- [ ] Todas las rutas del frontend accesibles

¡Deployment completado! 🎉 