# 🚀 Instrucciones de Despliegue - Render.com

## 📋 Checklist Antes del Despliegue

### 1. **Variables de Entorno del Backend en Render**
Asegúrate de configurar estas variables en el dashboard de Render:

```bash
# ✅ OBLIGATORIAS - APIs de IA
OPENAI_API_KEY=sk-tu_clave_real_aqui
ANTHROPIC_API_KEY=sk-ant-tu_clave_real_aqui

# ✅ OBLIGATORIAS - Seguridad
SECRET_KEY=clave_super_segura_generada_automaticamente_por_render

# ✅ AUTO-CONFIGURADAS por Render
DATABASE_URL=postgresql://... (desde la base de datos)
ENVIRONMENT=production
```

### 2. **Verificar URLs del Frontend**
El frontend debe apuntar al backend en producción:
- ✅ `VITE_API_BASE_URL=https://orquix-backend.onrender.com`
- ✅ `VITE_ENABLE_MOCK_AUTH=false`
- ✅ `VITE_ENVIRONMENT=production`

### 3. **Base de Datos**
- ✅ La base de datos PostgreSQL se crea automáticamente
- ✅ `DATABASE_URL` se configura automáticamente
- ✅ Las migraciones se ejecutan en el `start.sh`

## 🔧 Configuración Local vs Producción

### Desarrollo Local
```bash
# Backend usa variables individuales
POSTGRES_SERVER=localhost
POSTGRES_USER=roiky
POSTGRES_PASSWORD=roiky
POSTGRES_DB=orquix_db
POSTGRES_PORT=5432

# Frontend apunta a localhost
VITE_API_BASE_URL=http://localhost:8000
```

### Producción (Render)
```bash
# Backend usa DATABASE_URL completa
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# Frontend apunta a Render
VITE_API_BASE_URL=https://orquix-backend.onrender.com
```

## 🚨 Problemas Comunes

### 1. **Frontend apunta a localhost**
**Síntoma**: Errores de CORS o conexión en producción
**Solución**: Verificar que `VITE_API_BASE_URL` esté configurado correctamente

### 2. **Backend usa BD local**
**Síntoma**: Datos no persisten entre deploys
**Solución**: Verificar que `DATABASE_URL` esté configurado en Render

### 3. **APIs de IA no configuradas**
**Síntoma**: Errores 500 en endpoints de IA
**Solución**: Configurar `OPENAI_API_KEY` y `ANTHROPIC_API_KEY` reales

## 📝 Pasos de Despliegue

### 1. **Preparar el Código**
```bash
# Hacer commit de los cambios
git add .
git commit -m "Fix: Configuración para producción"
git push origin main
```

### 2. **Configurar Variables en Render**
1. Ir al dashboard del backend en Render
2. Configurar las variables obligatorias
3. Reiniciar el servicio

### 3. **Verificar el Despliegue**
```bash
# Verificar que el backend esté funcionando
curl https://orquix-backend.onrender.com/api/v1/health

# Verificar que el frontend cargue
curl https://orquix-frontend.onrender.com
```

## 🔍 Debug en Producción

### Logs del Backend
```bash
# En el dashboard de Render, revisar los logs para:
- Errores de conexión a BD
- Errores de APIs de IA
- Errores de configuración
```

### Verificar Variables
```bash
# Desde el shell de Render (si está disponible)
echo $DATABASE_URL
echo $OPENAI_API_KEY
echo $ENVIRONMENT
```

## ✅ Checklist Post-Despliegue

- [ ] Backend responde en `/api/v1/health`
- [ ] Frontend carga correctamente
- [ ] Crear proyecto funciona
- [ ] Context builder funciona
- [ ] Datos se guardan en BD de producción
- [ ] No hay errores de CORS
- [ ] APIs de IA responden correctamente 