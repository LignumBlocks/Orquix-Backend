import api from './api'

/**
 * Servicio para manejar sesiones de clarificación iterativa con el PreAnalyst
 */
export const clarificationService = {
  /**
   * Inicia una nueva sesión de clarificación
   * @param {string} projectId - ID del proyecto
   * @param {string} userResponse - Prompt inicial del usuario
   * @returns {Promise<Object>} - Respuesta de clarificación
   */
  async startClarificationSession(projectId, userResponse) {
    try {
      const response = await api.post('/api/v1/pre-analyst/clarification', {
        project_id: projectId,
        user_response: userResponse
      })
      return response.data
    } catch (error) {
      console.error('Error starting clarification session:', error)
      throw error
    }
  },

  /**
   * Continúa una sesión de clarificación existente
   * @param {string} sessionId - ID de la sesión
   * @param {string} projectId - ID del proyecto
   * @param {string} userResponse - Respuesta del usuario
   * @returns {Promise<Object>} - Respuesta de clarificación
   */
  async continueClarificationSession(sessionId, projectId, userResponse) {
    try {
      const response = await api.post('/api/v1/pre-analyst/clarification', {
        session_id: sessionId,
        project_id: projectId,
        user_response: userResponse
      })
      return response.data
    } catch (error) {
      console.error('Error continuing clarification session:', error)
      throw error
    }
  },

  /**
   * Obtiene el estado de una sesión de clarificación
   * @param {string} sessionId - ID de la sesión
   * @returns {Promise<Object>} - Estado de la sesión
   */
  async getClarificationSession(sessionId) {
    try {
      const response = await api.get(`/api/v1/pre-analyst/clarification/${sessionId}`)
      return response.data
    } catch (error) {
      console.error('Error getting clarification session:', error)
      throw error
    }
  },

  /**
   * Analiza un prompt directamente (sin sesión)
   * @param {string} userPromptText - Texto del prompt
   * @returns {Promise<Object>} - Resultado del análisis
   */
  async analyzePrompt(userPromptText) {
    try {
      const response = await api.post('/api/v1/pre-analyst/analyze-prompt', {
        user_prompt_text: userPromptText
      })
      return response.data
    } catch (error) {
      console.error('Error analyzing prompt:', error)
      throw error
    }
  }
}

export default clarificationService 