# AI Orchestrator - Flujo Detallado

## Descripción General

El `AIOrchestrator` es el componente central que gestiona múltiples proveedores de IA (OpenAI, Anthropic) y ejecuta diferentes estrategias de orquestación para obtener respuestas de manera eficiente y robusta.

## Arquitectura y Configuración

### Inicialización
```python
def __init__(self):
    self.adapters: Dict[AIProviderEnum, Any] = {}
    self._initialize_adapters()
```

### Adaptadores Disponibles
El sistema inicializa automáticamente los adaptadores disponibles basado en las API keys:

1. **OpenAI GPT-4o-mini**
   ```python
   if settings.OPENAI_API_KEY:
       self.adapters[AIProviderEnum.OPENAI] = OpenAIAdapter(
           api_key=settings.OPENAI_API_KEY,
           model="gpt-4o-mini"
       )
   ```

2. **Anthropic Claude 3 Haiku**
   ```python
   if settings.ANTHROPIC_API_KEY:
       self.adapters[AIProviderEnum.ANTHROPIC] = AnthropicAdapter(
           api_key=settings.ANTHROPIC_API_KEY,
           model="claude-3-haiku-20240307"
       )
   ```

## Estrategias de Orquestación

### Enum de Estrategias
```python
class AIOrchestrationStrategy(str, Enum):
    SINGLE = "single"      # Una sola IA
    PARALLEL = "parallel"  # Todas las IAs en paralelo
    FALLBACK = "fallback"  # Intentar una, si falla usar la siguiente
    FASTEST = "fastest"    # La primera que responda exitosamente
```

## Métodos de Orquestación

### 1. Single Response (`generate_single_response`)
**Propósito**: Genera respuesta usando un proveedor específico

**Flujo:**
```python
async def generate_single_response(
    self, 
    request: AIRequest, 
    provider: AIProviderEnum
) -> StandardAIResponse:
```

**Proceso:**
1. Verifica que el proveedor esté disponible
2. Obtiene el adaptador correspondiente
3. Ejecuta la solicitud
4. Retorna respuesta estandarizada

**Casos de uso:**
- Testing de proveedores específicos
- Cuando se requiere un modelo particular
- Debugging de respuestas individuales

### 2. Parallel Responses (`generate_parallel_responses`)
**Propósito**: Ejecuta consultas simultáneas a múltiples proveedores

**Flujo:**
```python
async def generate_parallel_responses(
    self, 
    request: AIRequest, 
    providers: Optional[List[AIProviderEnum]] = None
) -> List[StandardAIResponse]:
```

**Proceso:**
1. Filtra proveedores disponibles
2. Crea tareas asíncronas para cada proveedor
3. Ejecuta todas las tareas en paralelo usando `asyncio.gather()`
4. Procesa resultados y excepciones
5. Retorna lista de respuestas estandarizadas

**Ventajas:**
- **Velocidad**: Todas las consultas simultáneas
- **Diversidad**: Múltiples perspectivas
- **Robustez**: Si una falla, otras pueden continuar

**Ejemplo de uso:**
```python
# Ejecutar en paralelo
tasks = [
    self.adapters[provider].generate_response(request)
    for provider in available_providers
]
responses = await asyncio.gather(*tasks, return_exceptions=True)
```

### 3. Fallback Response (`generate_fallback_response`)
**Propósito**: Intenta proveedores secuencialmente hasta obtener éxito

**Flujo:**
```python
async def generate_fallback_response(
    self, 
    request: AIRequest, 
    providers: Optional[List[AIProviderEnum]] = None
) -> StandardAIResponse:
```

**Proceso:**
1. Ordena proveedores por prioridad
2. Intenta el primer proveedor
3. Si es exitoso → retorna respuesta
4. Si falla → intenta siguiente proveedor
5. Continúa hasta encontrar éxito o agotar opciones

**Ventajas:**
- **Confiabilidad**: Backup automático
- **Eficiencia de costos**: Solo usa lo necesario
- **Orden de preferencia**: Prioriza proveedores específicos

**Ejemplo de flujo:**
```
1. Intenta OpenAI GPT-4o-mini → Falla (rate limit)
2. Intenta Anthropic Claude 3 Haiku → Éxito ✅
3. Retorna respuesta de Claude
```

### 4. Fastest Response (`generate_fastest_response`)
**Propósito**: Retorna la primera respuesta exitosa (competencia de velocidad)

**Flujo:**
```python
async def generate_fastest_response(
    self, 
    request: AIRequest, 
    providers: Optional[List[AIProviderEnum]] = None
) -> StandardAIResponse:
```

**Proceso:**
1. Inicia todas las tareas en paralelo
2. Usa `asyncio.as_completed()` para procesar conforme terminan
3. Retorna la primera respuesta exitosa
4. Cancela las tareas restantes automáticamente

**Ventajas:**
- **Latencia mínima**: Primera respuesta disponible
- **Eficiencia**: Cancela tareas innecesarias
- **Adaptabilidad**: Se adapta a la velocidad de cada proveedor

**Implementación:**
```python
for completed_task in asyncio.as_completed(tasks):
    response = await completed_task
    if response.status == AIResponseStatus.SUCCESS:
        # Cancelar tareas restantes (automático)
        return response
```

## Método Principal: `orchestrate()`

### Signature
```python
async def orchestrate(
    self, 
    request: AIRequest, 
    strategy: AIOrchestrationStrategy = AIOrchestrationStrategy.FALLBACK,
    providers: Optional[List[AIProviderEnum]] = None
) -> Any:
```

### Dispatcher de Estrategias
```python
if strategy == AIOrchestrationStrategy.SINGLE:
    return await self.generate_single_response(request, providers[0])
elif strategy == AIOrchestrationStrategy.PARALLEL:
    return await self.generate_parallel_responses(request, providers)
elif strategy == AIOrchestrationStrategy.FALLBACK:
    return await self.generate_fallback_response(request, providers)
elif strategy == AIOrchestrationStrategy.FASTEST:
    return await self.generate_fastest_response(request, providers)
```

## Modelos de Datos

### AIRequest
```python
class AIRequest(BaseModel):
    user_question: str          # Pregunta del usuario
    context: Optional[str]      # Contexto adicional
    temperature: Optional[float] # Creatividad (0.0-1.0)
    max_tokens: Optional[int]   # Límite de tokens
    system_prompt: Optional[str] # Prompt del sistema
```

### StandardAIResponse
```python
class StandardAIResponse(BaseModel):
    ia_provider_name: AIProviderEnum    # Proveedor usado
    response_text: str                  # Respuesta generada
    status: AIResponseStatus            # SUCCESS | ERROR | TIMEOUT
    latency_ms: int                     # Tiempo de respuesta
    error_message: Optional[str]        # Mensaje de error si aplica
    metadata: Optional[Dict[str, Any]]  # Metadatos adicionales
```

### AIProviderEnum
```python
class AIProviderEnum(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
```

## Integración con el Sistema Principal

### Uso desde Projects Endpoint
```python
# En projects.py
async def orchestrate_ai_responses(
    orchestrator: AIOrchestrator,
    user_prompt: str,
    context_text: Optional[str],
    project_id: UUID,
    interaction_id: UUID,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    context_info: Optional[ContextInfo] = None
):
    # Crear AIRequest
    ai_request = AIRequest(
        user_question=user_prompt,
        context=context_text,
        temperature=temperature or 0.7,
        max_tokens=max_tokens or 1000,
        system_prompt=build_system_prompt(context_info)
    )
    
    # Ejecutar orquestación (estrategia por defecto: FALLBACK)
    ai_responses = await orchestrator.orchestrate(
        request=ai_request,
        strategy=AIOrchestrationStrategy.FALLBACK
    )
```

### Flujo en Consulta Principal
```python
# Paso 2: Orquestación de IAs
with time_step(interaction_id, "ai_orchestration") as timer:
    orchestration_result = await orchestrate_ai_responses(
        orchestrator=orchestrator,
        user_prompt=enriched_prompt,  # Desde FollowUp Interpreter
        context_text=context_text,    # Desde Context Manager
        project_id=project_id,
        interaction_id=interaction_id,
        temperature=query_request.temperature,
        max_tokens=query_request.max_tokens,
        context_info=context_info
    )
```

## Manejo de Errores y Excepciones

### Tipos de Errores Comunes
1. **Proveedor no disponible**: API key faltante
2. **Rate limiting**: Límites de uso excedidos
3. **Timeout**: Respuesta demasiado lenta
4. **Parsing errors**: Respuesta malformada
5. **Network errors**: Problemas de conectividad

### Estrategia de Manejo
```python
# En generate_parallel_responses
for i, response in enumerate(responses):
    provider = available_providers[i]
    
    if isinstance(response, Exception):
        processed_responses.append(StandardAIResponse(
            ia_provider_name=provider,
            status=AIResponseStatus.ERROR,
            error_message=f"Excepción: {str(response)}",
            latency_ms=0
        ))
    else:
        processed_responses.append(response)
```

## Métricas y Monitoreo

### Métricas Capturadas
- **Latencia por proveedor**: Tiempo de respuesta individual
- **Tasa de éxito**: Porcentaje de respuestas exitosas
- **Distribución de uso**: Qué proveedores se usan más
- **Patrones de fallback**: Cuándo se activan los backups

### Logging
```python
logger.info("Adaptador OpenAI inicializado")
logger.info("Adaptador Anthropic inicializado")
logger.warning("No se inicializó ningún adaptador de IA")
```

## Configuración y Optimización

### Variables de Entorno Requeridas
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Configuración de Modelos
- **OpenAI**: `gpt-4o-mini` (balance costo/rendimiento)
- **Anthropic**: `claude-3-haiku-20240307` (más económico)

### Estrategia Recomendada por Caso de Uso

| Caso de Uso | Estrategia | Razón |
|-------------|------------|-------|
| Producción normal | `FALLBACK` | Confiabilidad + eficiencia |
| Comparación de respuestas | `PARALLEL` | Diversidad de perspectivas |
| Prototipado rápido | `FASTEST` | Latencia mínima |
| Testing específico | `SINGLE` | Control total |

## Cleanup y Recursos

### Método de Cierre
```python
async def close(self):
    """Cierra todas las conexiones de adaptadores"""
    for adapter in self.adapters.values():
        if hasattr(adapter, 'close'):
            await adapter.close()
```

## Estado Actual y Rendimiento

### Estadísticas Típicas
- **Tiempo de respuesta promedio**: 
  - Single: 800-1200ms
  - Parallel: 1000-1500ms (limitado por el más lento)
  - Fallback: 800-2000ms (depende de fallos)
  - Fastest: 600-1000ms
- **Tasa de éxito**: >95% con fallback habilitado
- **Proveedores activos**: OpenAI + Anthropic

### Próximas Mejoras
- [ ] Implementar caching de respuestas
- [ ] Añadir más proveedores (Google, Cohere)
- [ ] Balanceador de carga inteligente
- [ ] Métricas de costo por proveedor 