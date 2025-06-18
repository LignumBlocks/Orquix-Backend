import config from '../config'

const handleResponse = async (response) => {
  if (!response.ok) {
    throw new Error(response.statusText || 'Not Found')
  }
  const data = await response.json()
  return data
}

// Función para obtener headers con autenticación
const getAuthHeaders = () => {
  const token = localStorage.getItem('auth_token')
  const headers = {
    'Content-Type': 'application/json'
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return headers
}

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
      const response = await fetch(`${config.apiUrl}/pre-analyst/clarification`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          project_id: projectId,
          user_response: userResponse
        })
      })
      return handleResponse(response)
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
      const response = await fetch(`${config.apiUrl}/pre-analyst/clarification`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          session_id: sessionId,
          project_id: projectId,
          user_response: userResponse
        })
      })
      return handleResponse(response)
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
      const response = await fetch(`${config.apiUrl}/pre-analyst/clarification/${sessionId}`, {
        headers: getAuthHeaders()
      })
      return handleResponse(response)
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
      const response = await fetch(`${config.apiUrl}/pre-analyst/analyze-prompt`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          user_prompt_text: userPromptText
        })
      })
      return handleResponse(response)
    } catch (error) {
      console.error('Error analyzing prompt:', error)
      throw error
    }
  },

  submitClarification: async (projectId, originalQuery, clarificationResponse) => {
    const response = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/clarify`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        original_query: originalQuery,
        clarification_response: clarificationResponse
      })
    })
    return handleResponse(response)
  },

  getClarificationQuestions: async (projectId, query) => {
    const response = await fetch(`${config.apiUrl}/api/v1/pre-analyst/analyze-prompt`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        project_id: projectId,
        prompt: query
      })
    })
    return handleResponse(response)
  }
}

export default clarificationService 