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

const api = {
  // Proyectos
  getProjects: async () => {
    const response = await fetch(`${config.apiUrl}/api/v1/projects`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  createProject: async (projectData) => {
    const response = await fetch(`${config.apiUrl}/api/v1/projects`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(projectData)
    })
    return handleResponse(response)
  },

  // Conversaciones
  getConversations: async (projectId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/interaction_events`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  // ==========================================
  // NUEVO: Construcción de Contexto Conversacional
  // ==========================================
  
  // Enviar mensaje en construcción de contexto
  sendContextMessage: async (projectId, userMessage, sessionId = null) => {
    const response = await fetch(`${config.apiUrl}/api/v1/context-chat/projects/${projectId}/context-chat`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        user_message: userMessage,
        session_id: sessionId
      })
    })
    return handleResponse(response)
  },

  // Obtener sesión de contexto actual
  getContextSession: async (sessionId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/context-chat/context-sessions/${sessionId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  // Finalizar construcción de contexto y enviar a IAs principales
  finalizeContextSession: async (sessionId, finalQuestion) => {
    const response = await fetch(`${config.apiUrl}/api/v1/context-chat/context-sessions/${sessionId}/finalize`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: sessionId,
        final_question: finalQuestion
      })
    })
    return handleResponse(response)
  },

  // ==========================================
  // ENDPOINTS ORIGINALES (mantener compatibilidad)
  // ==========================================

  // Pre-análisis y consultas
  analyzePrompt: async (prompt, projectId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/pre-analyst/analyze-prompt`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        user_prompt_text: prompt
      })
    })
    return handleResponse(response)
  },

  sendQuery: async (query, projectId, clarificationResponse = null) => {
    const endpoint = clarificationResponse 
      ? `${config.apiUrl}/api/v1/projects/${projectId}/clarify`
      : `${config.apiUrl}/api/v1/projects/${projectId}/query`

    const body = clarificationResponse
      ? { 
          original_query: query,
          clarification_response: clarificationResponse 
        }
      : { 
          user_prompt_text: query,
          include_context: true,
          conversation_mode: "auto"
        }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body)
    })
    return handleResponse(response)
  },

  // Clarificaciones
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
  }
}

export default api 