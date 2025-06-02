/**
 * @fileoverview Tipos compartidos para la API de Orquix
 */

/**
 * @typedef {Object} User
 * @property {string} id - ID único del usuario
 * @property {string} email - Email del usuario
 * @property {string} name - Nombre del usuario
 * @property {string} [image] - URL de la imagen de perfil
 */

/**
 * @typedef {Object} Project
 * @property {string} id - ID único del proyecto
 * @property {string} name - Nombre del proyecto
 * @property {string} [description] - Descripción del proyecto
 * @property {string} user_id - ID del usuario propietario
 * @property {Object} moderator_config - Configuración del moderador
 * @property {string} moderator_config.personality - Personalidad del moderador
 * @property {number} moderator_config.temperature - Temperatura (0.0-2.0)
 * @property {string} moderator_config.response_length - Longitud de respuesta
 * @property {string} created_at - Fecha de creación
 * @property {string} updated_at - Fecha de actualización
 */

/**
 * @typedef {Object} QueryRequest
 * @property {string} user_prompt_text - Texto de la consulta (1-10000 chars)
 * @property {boolean} [include_context=true] - Si incluir contexto del proyecto
 * @property {number} [temperature] - Temperatura para generación (0.0-2.0)
 * @property {number} [max_tokens] - Máximo número de tokens (100-4000)
 */

/**
 * @typedef {Object} StandardAIResponse
 * @property {string} ia_provider_name - Nombre del proveedor (openai, anthropic)
 * @property {string} [response_text] - Texto de respuesta
 * @property {string} status - Estado (success, error, timeout, etc.)
 * @property {string} [error_message] - Mensaje de error
 * @property {number} latency_ms - Latencia en milisegundos
 * @property {string} timestamp - Timestamp de la respuesta
 */

/**
 * @typedef {Object} QueryResponse
 * @property {string} interaction_event_id - ID único del evento
 * @property {string} synthesis_text - Texto sintetizado por el moderador
 * @property {string} moderator_quality - Calidad de síntesis (high, medium, low, failed)
 * @property {string[]} key_themes - Temas clave identificados
 * @property {string[]} contradictions - Contradicciones detectadas
 * @property {string[]} consensus_areas - Áreas de consenso
 * @property {string[]} recommendations - Recomendaciones del moderador
 * @property {string[]} suggested_questions - Preguntas sugeridas
 * @property {string[]} research_areas - Áreas de investigación
 * @property {StandardAIResponse[]} individual_responses - Respuestas individuales
 * @property {number} processing_time_ms - Tiempo total de procesamiento
 * @property {string} created_at - Timestamp de creación
 * @property {boolean} fallback_used - Si se usó fallback del moderador
 */

/**
 * @typedef {Object} InteractionEvent
 * @property {string} id - ID único de la interacción
 * @property {string} project_id - ID del proyecto
 * @property {string} user_prompt - Prompt del usuario
 * @property {StandardAIResponse[]} ai_responses - Respuestas de las IAs
 * @property {Object} [moderator_synthesis] - Síntesis del moderador
 * @property {string} created_at - Fecha de creación
 * @property {number} processing_time_ms - Tiempo de procesamiento
 */

/**
 * @typedef {Object} FeedbackCreate
 * @property {string} reference_id - ID de referencia
 * @property {string} reference_type - Tipo de referencia
 * @property {number} score - Puntuación 1-5
 * @property {string} [comment] - Comentario opcional
 * @property {string} [category] - Categoría del feedback
 */

/**
 * @typedef {Object} HealthResponse
 * @property {string} status - Estado general (healthy, unhealthy, degraded)
 * @property {string} timestamp - Timestamp del check
 * @property {string} version - Versión del sistema
 * @property {number} uptime_seconds - Tiempo de actividad
 */

// Exportar para uso en módulos ES6
export const ApiTypes = {
  // Solo para referencia, los tipos están en JSDoc
}; 