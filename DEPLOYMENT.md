# 🚀 **DEPLOYMENT GUIDE - ORQUIX BACKEND EN RENDER**

## 📋 **RESUMEN EJECUTIVO**

Esta guía te ayudará a deployar **Orquix Backend** (sistema de IA con Moderador Inteligente v2.0) en **Render** usando PostgreSQL 15 con pgvector.

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
├── render.yaml                 # ✅ Configuración completa de servicios
├── backend/
│   ├── Dockerfile             # ✅ Imagen Docker optimizada
│   ├── start.sh               # ✅ Script de inicio con migraciones
│   ├── requirements.txt       # ✅ Dependencias Python
│   └── app/core/config.py     # ✅ Configuración actualizada
└── .gitignore                 # ✅ Archivos excluidos
```

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

**⚠️ IMPORTANTE**: Sin las API keys, el deployment fallará.

### **PASO 3: Deployment Automático**

1. **Render detectará** el archivo `render.yaml`
2. **Creará automáticamente**:
   - 🗄️ Base de datos PostgreSQL 15
   - 🌐 Servicio web Python
   - 🔧 Variables de entorno
3. **Ejecutará** las migraciones automáticamente
4. **Iniciará** el servidor FastAPI

---

## 🏥 **VERIFICACIÓN DEL DEPLOYMENT**

### **1. Health Check**
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

### **2. Documentación API**
- 📚 **Swagger**: `https://tu-app.onrender.com/docs`
- 📖 **ReDoc**: `https://tu-app.onrender.com/redoc`

### **3. Endpoints Clave**
```bash
# Información general
GET /api/v1/health

# Crear proyecto (requiere auth)
POST /api/v1/projects

# Consulta con Moderador IA v2.0
POST /api/v1/projects/{project_id}/query
```

---

## 🛠️ **CONFIGURACIÓN AVANZADA**

### **1. Dominio Personalizado**
En Render Dashboard:
1. Ve a tu servicio → **"Settings"**
2. **"Custom Domains"** → **"Add Custom Domain"**
3. Agrega: `api.tudominio.com`
4. Configura DNS CNAME: `api.tudominio.com → tu-app.onrender.com`

### **2. Scaling**
```yaml
# En render.yaml (ya configurado)
plan: starter  # Cambiar a: standard, pro, etc.
```

### **3. Variables de Entorno Adicionales**
```bash
# Optimización AI
DEFAULT_AI_TIMEOUT=45
DEFAULT_AI_MAX_RETRIES=5
DEFAULT_AI_TEMPERATURE=0.8

# Context Manager
MAX_CONTEXT_TOKENS=8000
CHUNK_SIZE=1500
```

---

## 🔍 **TROUBLESHOOTING**

### **❌ Error: Build Failed**
```bash
# Verificar en logs de Render:
"Poetry not found" → El Dockerfile se encarga de instalarlo
"Requirements not satisfied" → Verificar requirements.txt
```

### **❌ Error: Database Connection**
```bash
# Verificar que pgvector esté habilitado:
CREATE EXTENSION IF NOT EXISTS vector;
```

### **❌ Error: API Keys**
```bash
# En logs verás:
"OPENAI_API_KEY not configured"
```
**Solución**: Configurar variables de entorno en Render.

### **❌ Error: Migrations Failed**
```bash
# El script start.sh maneja automáticamente:
alembic upgrade head
```

---

## 📊 **MONITOREO Y LOGS**

### **1. Logs en Tiempo Real**
En Render Dashboard:
- **"Logs"** → Ver logs del servicio
- **"Metrics"** → CPU, memoria, requests

### **2. Health Monitoring**
```bash
# Render hace health checks automáticos cada 30s a:
GET /api/v1/health
```

### **3. Database Monitoring**
```bash
# Verificar conexiones:
SELECT count(*) FROM pg_stat_activity;

# Verificar extensiones:
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## 🎉 **DEPLOYMENT EXITOSO**

Si todo está correcto, verás:

```bash
✅ Database migrations applied successfully
✅ Orquix Backend v1.0.0 started
✅ Environment: production
✅ AI Providers: OpenAI, Anthropic
✅ Rate Limiting: Enabled
✅ Health Check: /api/v1/health
```

---

## 🔗 **RECURSOS ADICIONALES**

- 📖 **Documentación Render**: [render.com/docs](https://render.com/docs)
- 🤖 **OpenAI API**: [platform.openai.com](https://platform.openai.com)
- 🧠 **Anthropic API**: [console.anthropic.com](https://console.anthropic.com)
- 🗄️ **PostgreSQL + pgvector**: [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)

---

## 🆘 **SOPORTE**

Si encuentras problemas:

1. **Revisa los logs** en Render Dashboard
2. **Verifica variables de entorno** (especialmente API keys)
3. **Confirma que pgvector** esté instalado en la DB
4. **Verifica el health check**: `/api/v1/health`

---

**🚀 ¡Listo para producción con Orquix Backend + Moderador IA v2.0!** 