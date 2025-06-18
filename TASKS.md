# Orquix - Moderador de IA v2.0 Implementation

Plataforma completa de orquestación de múltiples IAs con interfaz responsive y deployment en producción.

## Completed Tasks

- [x] Configuración inicial del proyecto
- [x] Estructura backend FastAPI con endpoints principales
- [x] Implementación del sistema de autenticación mock
- [x] Base de datos PostgreSQL con esquemas principales
- [x] Integración con múltiples proveedores de IA (OpenAI, Anthropic, Groq, Together)
- [x] Sistema de Context Manager acumulativo
- [x] Moderador v2.0 con síntesis inteligente
- [x] Frontend React con Zustand store
- [x] Componentes UI principales (sidebars, chat, modales)
- [x] Sistema de notificaciones toast
- [x] Métricas y monitoreo de IA providers
- [x] Deployment backend en Render (Web Service)
- [x] Configuración CORS para producción
- [x] **Interfaz responsive completa**
- [x] **Navegación móvil con tabs**
- [x] **Layout adaptativo (móvil/tablet/desktop)**
- [x] **Deployment frontend en Render (Static Site)**
- [x] **Corrección de problemas de layout móvil**
- [x] **PreAnalyst completamente implementado e integrado**

## In Progress Tasks

- [ ] Testing de integración completa del FollowUpInterpreter
- [ ] Optimización de rendimiento en móviles
- [ ] Testing en diferentes navegadores y dispositivos
- [ ] Documentación de usuario final

## Future Tasks

### High Priority
- [ ] **Tarea 1.3: Continuidad Conversacional Post-Síntesis** - Sistema de follow-up conversacional para mantener el hilo de la investigación
  - [x] **Análisis de Tipo de Consulta**
    - [x] Crear servicio `FollowUpInterpreter` para detectar si una consulta es nueva o continuación
    - [x] Implementar detección de referencias anafóricas ("Y si vamos con niños", "mejora eso", "dame más detalles")
    - [x] Integrar análisis con PreAnalyst para determinar contexto necesario
    - [x] Desarrollar criterios para identificar cambio de tema vs. ampliación
  - [x] **Recuperación de Memoria Activa**
    - [x] Implementar función `get_recent_interaction_context()` en `context_manager.py`
    - [x] Configurar recuperación automática de última síntesis del moderador
    - [x] Extraer prompts refinados y respuestas de IAs relevantes de la interacción previa
    - [x] Implementar límites de tokens/caracteres para contexto histórico
  - [x] **Enriquecimiento Contextual Inteligente**
    - [x] Desarrollar función `enrich_prompt_with_history()` para combinar nueva consulta con historial
    - [x] Implementar template de prompt que preserva información previa relevante
    - [x] Evitar repetición de información ya proporcionada en síntesis anterior
    - [x] Mantener coherencia semántica entre consultas relacionadas
  - [x] **Integración con Flujo Principal**
    - [x] Modificar endpoint `/projects/{project_id}/query` para incluir análisis de continuidad
    - [x] Actualizar `AI Orchestrator` para usar contexto enriquecido automáticamente
    - [x] Asegurar que el `AI Moderator` considere el hilo conversacional en nuevas síntesis
    - [x] Implementar logging específico para tracking de continuidad conversacional
  - [ ] **Frontend - Indicadores de Continuidad**
    - [x] Crear componente visual para mostrar cuando se usa contexto previo
    - [x] Implementar "breadcrumb" conversacional en la interfaz de chat
    - [x] Agregar opción para usuario de "empezar nueva consulta" vs "continuar conversación"
    - [x] Mostrar preview del contexto que se está utilizando de conversaciones anteriores
    - [x] **Dashboard conversacional detallado con métricas y estado en tiempo real**
- [ ] **Tarea 1.4: Historial Conversacional Corto** - Incorporación de memoria conversacional para referencias implícitas
- [x] **Tarea 1.5: PreAnalystService - Interpretación previa de consultas** - Análisis e interpretación de la intención del usuario antes de orquestar IAs
  - [x] Implementar clase `PreAnalysisResult` con campos requeridos
  - [x] Crear servicio `PreAnalystService` en `app/services/pre_analyst.py`
  - [x] Integrar GPT-3.5-Turbo para análisis de intenciones
  - [x] Desarrollar endpoint `/analyze-prompt` para testing
  - [x] Integrar PreAnalyst con flujo principal de orquestación
  - [x] Implementar flujo iterativo de clarificación de preguntas
  - [x] **Integrar interfaz frontend con flujo de clarificación**
    - [x] Crear servicio clarificationService.js
    - [x] Desarrollar componente ClarificationDialog.jsx
    - [x] Integrar estado de clarificación en useAppStore.js
    - [x] Modificar CenterColumn.jsx para mostrar flujo de clarificación
    - [x] Añadir indicadores visuales para PreAnalyst
- [ ] Implementación de speech-to-text en móvil
- [ ] Optimización de Context Manager con historial reciente

### Medium Priority  
- [ ] Gestos táctiles avanzados (swipe, pinch)
- [ ] Modo offline/PWA
- [ ] Push notifications
- [ ] Compartir conversaciones
- [ ] Exportar a PDF
- [ ] Themes/modo oscuro

### Low Priority
- [ ] Analíticas de uso
- [ ] Integración con más proveedores de IA
- [ ] Sistema de plugins/extensiones

## Implementation Plan

### Arquitectura Responsive

La aplicación utiliza un diseño **mobile-first** con breakpoints específicos:

- **Mobile (< 768px)**: Navegación por tabs, layout de columna única
- **Tablet (768px - 1024px)**: Layout híbrido con sidebars colapsables  
- **Desktop (> 1024px)**: Layout de 3 columnas completo

### Tecnologías Utilizadas

**Backend:**
- FastAPI + PostgreSQL
- Múltiples proveedores de IA
- Sistema de Context Manager
- Deployment: Render Web Service

**Frontend:**
- React + Vite + Tailwind CSS
- Zustand para state management
- Lucide React iconos
- Deployment: Render Static Site

### URLs de Producción

- **Backend**: `https://orquix-backend.onrender.com`
- **Frontend**: `https://orquix-frontend.onrender.com`

## Próxima Funcionalidad Prioritaria

### 🧠 Tarea 1.5: PreAnalystService - Interpretación previa de consultas

**Problema**: Los usuarios envían preguntas vagas, incompletas o ambiguas (ej: "necesito ayuda con el presupuesto de mi viaje"). Estas consultas requieren clarificación antes de ser enviadas a las IAs orquestadas, generando respuestas genéricas o irrelevantes.

**Solución**: Implementar un servicio previo que analice la intención del usuario, identifique información faltante y genere preguntas de clarificación iterativas.

#### Flujo de Conversación Ejemplo

1. **Usuario**: "necesito ayuda con el presupuesto de mi viaje"
2. **PreAnalyst**: Interpreta intención + genera preguntas clarificadoras
3. **Usuario**: Responde "Es para Medellín, 4 días, tengo $800 dólares"  
4. **PreAnalyst**: Genera `refined_prompt_candidate` refinado
5. **Sistema**: Envía prompt refinado al flujo normal de orquestación

#### Implementación Técnica

1. **Modelo de Datos**:
   ```python
   class PreAnalysisResult(BaseModel):
       interpreted_intent: str
       clarification_questions: List[str]
       refined_prompt_candidate: Optional[str]
   ```

2. **Servicio Principal**:
   ```python
   # app/services/pre_analyst.py
   async def analyze_prompt(user_prompt_text: str) -> PreAnalysisResult
   ```

3. **Integración con OpenAI**:
   - Modelo: `gpt-3.5-turbo-1106` (económico)
   - Temperature: 0.3 (consistencia)
   - Sistema prompt específico para análisis de intenciones

4. **Endpoint de Testing**:
   ```python
   # app/routers/pre_analyst.py
   @router.post("/analyze-prompt")
   async def analyze_user_prompt(...)
   ```

#### Archivos a Crear/Modificar

- `backend/app/services/pre_analyst.py` - ✅ Servicio principal
- `backend/app/api/v1/endpoints/pre_analyst.py` - ✅ Endpoint REST
- `backend/app/models/pre_analysis.py` - ✅ Modelos Pydantic
- `backend/app/main.py` - ✅ Integración del router
- `backend/app/api/v1/endpoints/projects.py` - ✅ Integración con flujo principal
- `backend/app/services/clarification_manager.py` - ✅ **Gestión de sesiones iterativas**
- `backend/app/api/v1/endpoints/pre_analyst.py` - ✅ **Endpoints de clarificación**

#### Beneficios

- ✅ Mejora calidad de respuestas mediante clarificación previa
- ✅ Reduce tokens consumidos en orquestación principal
- ✅ Habilita manejo de referencias implícitas futuras
- ✅ Compatible con arquitectura actual
- ✅ Costo-efectivo (modelo económico GPT-3.5)

### 🧠 Tarea 1.4: Historial Conversacional Corto

**Problema**: Los usuarios utilizan referencias implícitas en conversaciones multi-turno como "Dame los últimos 4", "Mejora eso", "Lo que me diste antes", etc. Estas frases carecen de contenido semántico suficiente para la búsqueda vectorial.

**Solución**: Incorporar historial conversacional reciente para enriquecer el contexto antes de procesar nuevas consultas.

#### Implementación Técnica

1. **Recuperación de Historial**:
   ```sql
   SELECT user_prompt_text, moderated_synthesis
   FROM interaction_events
   WHERE project_id = ? AND user_id = ?
   ORDER BY created_at DESC
   LIMIT 3
   ```

2. **Enriquecimiento de Prompt**:
   ```python
   enriched_prompt = f"""
   Historial reciente:
   {historial_formateado}
   ---
   Nueva pregunta: {user_prompt}
   """
   ```

3. **Integración con Context Manager**:
   - Usar `enriched_prompt` para búsqueda vectorial en `pgvector`
   - Pasar contexto enriquecido a las IAs orquestadas
   - Mantener coherencia en la síntesis del Moderador

#### Archivos a Modificar

- `backend/app/services/context_manager.py` - Lógica de enriquecimiento
- `backend/app/services/query_service.py` - Integración con orquestación
- `backend/app/routers/ai_orchestrator.py` - Endpoint actualizado

#### Beneficios

- ✅ Mejora comprensión de preguntas anafóricas
- ✅ Compatible con arquitectura actual (usa `interaction_events`)
- ✅ Escalable (configurable por cantidad de eventos o tokens)
- ✅ No requiere cambios de esquema de BD

### 🔄 Tarea 1.3: Continuidad Conversacional Post-Síntesis

**Problema**: Orquix actualmente funciona como un sistema de "pregunta-respuesta única", pero debe comportarse como un asistente inteligente que acompaña al usuario durante una investigación iterativa. Los usuarios esperan poder hacer seguimiento como "¿Y si vamos con niños?" después de una consulta sobre viajes.

**Solución**: Implementar un sistema de continuidad conversacional que detecte automáticamente cuando una nueva consulta es una ampliación de la anterior y use la síntesis previa como memoria activa.

#### Flujo de Conversación Ejemplo

1. **Usuario inicial**: "Necesito ayuda para planear un viaje de 5 días a Cuba con mi esposa"
2. **Sistema**: [PreAnalyst + Orquestación + Síntesis] → "Aquí están las mejores opciones para un viaje de 5 días en Cuba..."
3. **Usuario follow-up**: "¿Y si fuéramos con niños?"
4. **Sistema**: [Detecta continuidad + Enriquece contexto] → Nuevo prompt: "Considerando el viaje a Cuba de 5 días que ya planificamos, cómo adaptarlo para ir con niños"
5. **Sistema**: [Orquestación enriquecida + Síntesis contextual]

#### Implementación Técnica

1. **Servicio FollowUpInterpreter**:
   ```python
   class FollowUpInterpreter:
       async def analyze_query_continuity(
           user_prompt: str, 
           project_id: UUID, 
           user_id: UUID
       ) -> ContinuityAnalysis
   ```

2. **Modelo de Datos**:
   ```python
   class ContinuityAnalysis(BaseModel):
       is_continuation: bool
       reference_type: str  # "anaphoric", "topic_expansion", "clarification", "new_topic"
       confidence_score: float
       previous_interaction_id: Optional[UUID]
       contextual_keywords: List[str]
   ```

3. **Recuperación de Memoria Activa**:
   ```python
   async def get_recent_interaction_context(
       project_id: UUID, 
       user_id: UUID, 
       max_interactions: int = 1
   ) -> InteractionContext
   ```

4. **Enriquecimiento Contextual**:
   ```python
   def enrich_prompt_with_history(
       current_prompt: str,
       previous_synthesis: str,
       previous_refined_prompt: str
   ) -> str:
       return f"""
       CONTEXTO PREVIO (para referencia):
       Consulta anterior: {previous_refined_prompt}
       Síntesis proporcionada: {previous_synthesis[:500]}...
       
       NUEVA CONSULTA (amplía o modifica lo anterior):
       {current_prompt}
       
       INSTRUCCIÓN: Responde considerando el contexto previo pero enfócate en la nueva consulta.
       """
   ```

#### Archivos a Crear/Modificar

**Backend - Nuevos Servicios**:
- `backend/app/services/followup_interpreter.py` - Detecta tipo de continuidad
- `backend/app/models/continuity.py` - Modelos de datos para continuidad
- `backend/app/services/conversation_memory.py` - Gestión de memoria conversacional

**Backend - Modificaciones**:
- `backend/app/services/context_manager.py` - Agregar funciones de recuperación de historial
- `backend/app/api/v1/endpoints/projects.py` - Integrar análisis de continuidad en `/query`
- `backend/app/services/ai_orchestrator.py` - Usar contexto enriquecido
- `backend/app/services/ai_moderator.py` - Síntesis consciente del hilo conversacional

**Frontend - Nuevos Componentes**:
- `frontend/src/components/chat/ContinuityIndicator.jsx` - Muestra cuando se usa contexto previo
- `frontend/src/components/chat/ConversationBreadcrumb.jsx` - Rastro visual de la conversación
- `frontend/src/components/chat/ContextPreview.jsx` - Preview del contexto utilizado

**Frontend - Modificaciones**:
- `frontend/src/store/useAppStore.js` - Estado para tracking de continuidad
- `frontend/src/components/layout/CenterColumn.jsx` - Integrar indicadores visuales
- `frontend/src/services/api.js` - Endpoints para gestión de continuidad

#### Criterios de Detección de Continuidad

**Referencias Anafóricas** (is_continuation = true):
- Pronombres: "eso", "esto", "lo anterior", "lo que dijiste"
- Temporal: "después de eso", "luego", "también"
- Condicional: "¿y si...?", "pero qué tal si..."
- Expansión: "además", "también considera", "otra opción"

**Cambio de Tema** (is_continuation = false):
- Palabras clave completamente diferentes
- Cambio radical de dominio (ej: viajes → programación)
- Indicadores explícitos: "ahora quiero", "nueva consulta", "cambiando de tema"

#### Beneficios Esperados

- ✅ Experiencia conversacional natural e intuitiva
- ✅ Reduce fricción para el usuario en consultas iterativas
- ✅ Maximiza reutilización del conocimiento ya generado
- ✅ Convierte Orquix en un verdadero asistente de investigación
- ✅ Compatible con la arquitectura actual de `interaction_events`
- ✅ Escalable y configurable (límites de memoria, tokens, etc.)

## Relevant Files

### Backend Core ✅
- `backend/app/main.py` - FastAPI app principal con CORS
- `backend/app/routers/ai_orchestrator.py` - Endpoints de orquestación  
- `backend/app/routers/projects.py` - Gestión de proyectos
- `backend/app/routers/moderator.py` - Moderador v2.0
- `backend/app/services/pre_analyst.py` - ✅ **PreAnalystService**
- `backend/app/api/v1/endpoints/pre_analyst.py` - ✅ **Endpoints PreAnalyst**
- `backend/app/models/pre_analysis.py` - ✅ **Modelos PreAnalysis**
- `backend/app/services/followup_interpreter.py` - ✅ **Detección de continuidad conversacional**
- `backend/app/services/context_manager.py` - ✅ **Función get_recent_interaction_context() añadida**
- `backend/app/api/v1/endpoints/projects.py` - ✅ **Integrado con análisis de continuidad**
- `backend/tests/test_followup_interpreter.py` - ✅ **Pruebas completas del FollowUpInterpreter**
- `backend/app/database/database.py` - Configuración PostgreSQL
- `backend/app/database/models.py` - Modelos SQLAlchemy

### Frontend Responsive ✅
- `frontend/src/App.jsx` - Layout responsive principal
- `frontend/src/components/layout/MobileNavigation.jsx` - Navegación móvil
- `frontend/src/components/layout/LeftSidebar.jsx` - Sidebar proyectos (responsive)
- `frontend/src/components/layout/CenterColumn.jsx` - Chat principal (responsive)
- `frontend/src/components/layout/RightSidebar.jsx` - Agentes IA (responsive)
- `frontend/src/components/chat/ContinuityIndicator.jsx` - ⏳ **Indicador de contexto previo**
- `frontend/src/components/chat/ConversationBreadcrumb.jsx` - ⏳ **Rastro conversacional**
- `frontend/src/components/chat/ContextPreview.jsx` - ⏳ **Preview de contexto utilizado**
- `frontend/src/index.css` - Estilos responsive y móviles

### Configuration ✅
- `render.yaml` - Configuración fullstack deployment
- `frontend/vite.config.js` - Build optimizado para producción
- `frontend/src/config.js` - URLs dinámicas dev/prod
- `frontend/public/_redirects` - SPA routing para Render
- `frontend/index.html` - Meta tags optimizados para móvil

### Documentation ✅
- `DEPLOYMENT.md` - Guía completa de deployment
- `README.md` - Arquitectura y URLs de producción
- `docs/frontend_deployment_render.md` - Opción B implementada

## Testing Checklist

### Mobile Testing (< 768px)
- [ ] iPhone SE (375x667) - Navegación tabs
- [ ] iPhone 12 Pro (390x844) - Layout responsive  
- [ ] Galaxy Fold (280x653) - Pantallas muy pequeñas
- [ ] Orientación portrait/landscape
- [ ] Touch gestures y scrolling

### Tablet Testing (768px - 1024px)  
- [ ] iPad (768x1024) - Layout híbrido
- [ ] Surface Pro (912x1368) - Windows tablet

### Desktop Testing (> 1024px)
- [ ] 1920x1080 - Layout 3 columnas
- [ ] 4K displays - Escalado
- [ ] Diferentes browsers (Chrome, Firefox, Safari, Edge)

## Performance Metrics

- [ ] Lighthouse mobile score > 90
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Bundle size analysis
- [ ] Core Web Vitals optimization

## Deployment Status

- ✅ **Backend**: Deployado y funcional en Render
- ✅ **Frontend**: Deployado con Static Site en Render  
- ✅ **Database**: PostgreSQL en Render
- ✅ **CORS**: Configurado para producción
- ✅ **SSL**: Certificados automáticos
- ✅ **CDN**: Global con Render Static Site
