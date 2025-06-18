# 📋 TAREAS ORQUIX-BACKEND

## 🎉 HITOS IMPORTANTES ALCANZADOS - 18 DE JUNIO 2025

### ✨ **ETAPA 1 DEL FLUJO COMPLETADA EXITOSAMENTE**

**🎯 Logro Principal**: Se ha implementado exitosamente la **Etapa 1** del nuevo flujo simplificado de Orquix:

1. **✅ Context Building Funcional**: El sistema de construcción de contexto guía perfectamente al usuario
2. **✅ Generación de Prompts Elaborados**: Los prompts ahora usan los templates sofisticados de 600-800 palabras
3. **✅ Interfaz Mejorada**: Formato legible con botones colapsar/expandir para una UX excelente
4. **✅ Arquitectura Correcta**: Endpoint `/generate-ai-prompts` usando `query_service` + `prompt_templates.py`

### 🚀 **ETAPA 2 DEL FLUJO COMPLETADA EXITOSAMENTE**

**🎯 Logro Principal**: Se ha implementado exitosamente la **Etapa 2** - Consulta Individual a las IAs:

1. **✅ Endpoint Específico**: `/context-sessions/{session_id}/query-ais` para consultas individuales
2. **✅ Respuestas Separadas**: OpenAI y Anthropic con diseño diferenciado y tiempos de procesamiento
3. **✅ Botón Condicional**: "Consultar a las IAs" visible solo después de generar prompts
4. **✅ Sistema de Reintentos**: Botón "🔄 Reintentar" para IAs fallidas con endpoint `/retry-ai/{provider}`
5. **✅ UX Robusta**: Estados de carga, manejo de errores, y actualización automática de respuestas

**📊 Impacto Etapa 2**: 
- **Tiempo de desarrollo**: 90 minutos para implementar flujo completo
- **Funcionalidad robusta**: Manejo inteligente de fallos y reintentos automáticos
- **Experiencia excepcional**: Respuestas individuales con diseño diferenciado por proveedor
- **Arquitectura escalable**: Fácil agregar nuevos proveedores de IA

**🎉 Estado Actual**: **FLUJO COMPLETO FUNCIONAL** - Ambas etapas operativas y testeadas exitosamente

---

## 🚨 CRITICAL REFACTOR (Inmediato - <2h)

### 1. ✅ [Refactor] Simplificar Flujo - Etapa 1: Solo Generar Prompt
**Archivo**: `frontend/src/components/layout/CenterColumn.jsx`
**Objetivo**: Dividir flujo en 2 etapas claras
**Cambios**:
- ✅ Cambiar botón "Enviar a las IAs" → "Generar Prompt para las IAs"
- ✅ Modificar `handleSendToAIs` → `handleGeneratePrompts` (no llamar `/query`)
- ✅ Mantener context builder como está (funciona bien)
- ✅ Mostrar prompt generado y terminar etapa
- ✅ **CORREGIDO**: Usar endpoint correcto `/generate-ai-prompts` con `prompt_templates.py`
- ✅ **CORREGIDO**: Renderizar prompts elaborados en lugar de fallbacks simples
**Tiempo estimado**: 45 minutos
**Estado**: 🟢 Completada

### 1.1. ✅ [Feature] Implementar Etapa 2: Consulta Individual a IAs
**Archivos**: 
- `backend/app/api/v1/endpoints/context_chat.py` (nuevo endpoint `/query-ais`)
- `frontend/src/components/layout/CenterColumn.jsx` (botón condicional + renderizado)
**Objetivo**: Consultar IAs individualmente con sistema de reintentos
**Cambios**:
- ✅ Endpoint específico `/context-sessions/{session_id}/query-ais` 
- ✅ Endpoint de reintento `/context-sessions/{session_id}/retry-ai/{provider}`
- ✅ Botón "Consultar a las IAs" visible solo después de generar prompts
- ✅ Respuestas individuales con diseño diferenciado (OpenAI verde, Anthropic naranja)
- ✅ Botón "🔄 Reintentar" en respuestas fallidas
- ✅ Estados de carga y manejo robusto de errores
**Tiempo estimado**: 90 minutos
**Estado**: 🟢 Completada

### 2. ❌ [Bug] Missing add_info Method in MetricsCollector  
**Archivo**: `backend/app/core/metrics.py`
**Problema**: `'OrchestrationMetricsCollector' object has no attribute 'add_info'`
**Solución**: Añadir método `add_info()` a la clase
**Tiempo estimado**: 20 minutos
**Estado**: 🔴 Pendiente

### 2. ✅ [UX] Mejorar Formato de Prompts Generados
**Archivo**: `frontend/src/components/layout/CenterColumn.jsx`
**Problema**: Los prompts se muestran en una línea continua, difícil de leer
**Solución**: 
- ✅ Aplicar formato Markdown (negritas, párrafos, listas)
- ✅ Botones para colapsar/expandir secciones largas (SYSTEM/USER)
- ✅ Mejor espaciado y legibilidad con bordes y indentación
- ✅ Altura ajustable y scroll para textos largos
**Tiempo estimado**: 30 minutos
**Estado**: 🟢 Completada

### 3. ❌ [Bug] Synthesis Preview Truncation Error
**Archivo**: `backend/app/api/v1/endpoints/interactions.py`
**Problema**: Campo `synthesis_preview` excede límite de 300 caracteres en InteractionSummary
**Solución**: Truncar a 297 chars + "..." en líneas 108 y 164
**Tiempo estimado**: 15 minutos
**Estado**: 🔴 Pendiente

---

## 🏃‍♂️ SPRINT 1: Polish & UX (1-2 semanas)

### 4. 🎨 [UX] Loading States Mejorados
**Archivo**: `frontend/src/components/ui/ConversationFlow.jsx`
**Descripción**: Añadir indicadores de progreso específicos para cada fase (contexto → AI → síntesis)
**Tiempo estimado**: 30 minutos
**Estado**: ⏳ Planificado

### 5. 🛡️ [UX] Error Handling Robusto  
**Archivos**: 
- `frontend/src/components/layout/CenterColumn.jsx`
- `frontend/src/services/api.js`
**Descripción**: Mostrar errores específicos y opciones de reintento
**Tiempo estimado**: 45 minutos
**Estado**: ⏳ Planificado

### 6. 📱 [UX] Mobile Optimization
**Archivos**: 
- `frontend/src/components/ui/AIResponseCard.jsx`
- `frontend/src/App.css`
**Descripción**: Mejorar visualización en móviles del chat de resultados
**Tiempo estimado**: 40 minutos
**Estado**: ⏳ Planificado

### 7. ⚡ [Performance] AI Response Caching
**Archivo**: `backend/app/services/ai_orchestrator.py`
**Descripción**: Cache temporal para respuestas similares
**Tiempo estimado**: 45 minutos
**Estado**: ⏳ Planificado

### 8. 📊 [UX] Metrics Dashboard Simple
**Archivo**: `frontend/src/components/ui/MetricsDisplay.jsx`
**Descripción**: Mostrar tiempo de respuesta y calidad de síntesis
**Tiempo estimado**: 35 minutos
**Estado**: ⏳ Planificado

---

## 🚀 SPRINT 2: New Features (2-3 semanas)

### 9. 🔄 [Feature] Persistencia y Continuidad de Sesiones
**Archivos**: 
- `backend/app/models/context_session.py` (usar existente)
- `backend/app/models/conversation_history.py` (usar existente)  
- `backend/app/models/interaction_events.py` (usar existente)
- `backend/app/api/v1/endpoints/context_chat.py` (nuevos endpoints)
- `frontend/src/components/ui/SessionSelector.jsx` (nuevo)
**Descripción**: 
- Permitir volver a sesiones anteriores y continuar conversación
- Guardar historial completo en `conversation_history` y `interaction_events`
- UI para listar y seleccionar sesiones del proyecto
- Restaurar estado completo de sesión (contexto + historial + prompts)
**Endpoints nuevos**:
- `GET /projects/{id}/sessions` - Listar sesiones del proyecto
- `GET /context-sessions/{id}/full-state` - Estado completo de sesión
- `POST /context-sessions/{id}/continue` - Continuar sesión existente
**Tiempo estimado**: 90 minutos (feature compleja)
**Estado**: ⏳ Planificado

### 10. 🔗 [Feature] Continuity Indicators  
**Archivos**: 
- `frontend/src/components/ui/ContinuityIndicator.jsx`
- `backend/app/api/v1/endpoints/projects.py`
**Descripción**: Mostrar conexiones entre conversaciones relacionadas
**Tiempo estimado**: 45 minutos
**Estado**: ⏳ Planificado

### 11. 🧠 [Feature] PreAnalyst Frontend Integration
**Archivos**: 
- `frontend/src/components/ui/PreAnalystDisplay.jsx`
- `frontend/src/services/api.js`
**Descripción**: Mostrar resultados del pre-análisis en la UI
**Tiempo estimado**: 45 minutos
**Estado**: ⏳ Planificado

### 12. 💾 [Feature] Conversation Export
**Archivos**: 
- `frontend/src/components/ui/ConversationExport.jsx`
- `backend/app/api/v1/endpoints/interactions.py`
**Descripción**: Exportar conversaciones completas en PDF/MD
**Tiempo estimado**: 45 minutos
**Estado**: ⏳ Planificado

### 13. 🔍 [Feature] Advanced Search
**Archivos**: 
- `frontend/src/components/ui/SearchDialog.jsx`
- `backend/app/services/embeddings.py`
**Descripción**: Búsqueda semántica en conversaciones históricas
**Tiempo estimado**: 45 minutos
**Estado**: ⏳ Planificado

---

## 📋 GUIDELINES

### ⏱️ Tiempo de Tareas
- **Critical Fixes**: < 45 minutos cada una
- **Sprint Tasks**: < 45 minutos cada una
- Si una tarea toma más de 45 minutos, dividirla en subtareas

### 🧪 Testing
- Cada tarea debe incluir testing inmediato
- No pasar a la siguiente tarea sin confirmar que la anterior funciona
- Usar `test_sistema_real_completo.py` para validación end-to-end

### 📝 Commits
- Un commit por tarea completada
- Formato: `[tipo] descripción corta - #tarea`
- Ejemplo: `[fix] truncar synthesis_preview - #1`

### 🎯 Priorización
1. **Critical Fixes**: Resolver todos antes de continuar
2. **Sprint 1**: UX y polish básico
3. **Sprint 2**: Features nuevas

### 🔄 Estado de Tareas
- 🔴 **Pendiente**: No iniciada
- 🟡 **En Progreso**: Actualmente trabajando
- 🟢 **Completada**: Funciona y testeada
- ⏳ **Planificado**: Definida pero no iniciada
- ❌ **Bloqueada**: Requiere otra tarea

---

## 📈 PROGRESO ACTUAL

**Critical Refactor**: 3/4 ✅ (75% completado)  
**Sprint 1**: 0/5 ✅  
**Sprint 2**: 0/5 ✅  

**Total**: 3/15 tareas completadas (20%)

### 🎯 Archivos Relevantes Actualizados

#### ✅ Completados
- `backend/app/api/v1/endpoints/context_chat.py` - Endpoints de generación de prompts, consulta individual y reintentos
- `frontend/src/components/layout/CenterColumn.jsx` - Flujo completo de 2 etapas con sistema de reintentos
- `frontend/src/components/ui/ContextBuildingFlow.jsx` - Construcción de contexto (sin cambios, funcionando)

#### 🔄 Arquitectura Implementada
- **Etapa 1**: Context Building → Prompt Generation (usando `query_service` + `prompt_templates.py`)
- **Etapa 2**: Individual AI Queries → Retry System (usando `ai_orchestrator`)
- **UX Flow**: Botones condicionales → Estados de carga → Respuestas diferenciadas → Reintentos automáticos