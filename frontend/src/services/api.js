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
  // Usar token mock para desarrollo
  const token = localStorage.getItem('auth_token') || 'dev-mock-token-12345'
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
    const response = await fetch(`${config.apiUrl}/api/v1/projects/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  createProject: async (projectData) => {
    const response = await fetch(`${config.apiUrl}/api/v1/projects/`, {
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
  // NUEVO: Arquitectura Chat + Session
  // ==========================================
  
  // Crear o obtener chat por defecto para un proyecto
  getOrCreateDefaultChat: async (projectId) => {
    // Primero intentar obtener chats existentes
    const chatsResponse = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/chats`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    
    if (chatsResponse.ok) {
      const chatsData = await chatsResponse.json()
      if (chatsData.chats && chatsData.chats.length > 0) {
        return chatsData.chats[0] // Retornar primer chat existente
      }
    }
    
    // Si no hay chats, crear uno nuevo
    const createResponse = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/chats`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        title: "Construcción de Contexto"
      })
    })
    return handleResponse(createResponse)
  },

  // Enviar mensaje en construcción de contexto
  sendContextMessage: async (projectId, userMessage, sessionId = null) => {
    // Si no hay sessionId, necesitamos crear chat y sesión
    if (!sessionId) {
      // Obtener o crear chat inline para evitar referencia circular
      let chat
      try {
        const chatsResponse = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/chats`, {
          method: 'GET',
          headers: getAuthHeaders()
        })
        
        if (chatsResponse.ok) {
          const chatsData = await chatsResponse.json()
          if (chatsData.chats && chatsData.chats.length > 0) {
            chat = chatsData.chats[0]
          }
        }
        
        if (!chat) {
          const createResponse = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/chats`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
              title: "Construcción de Contexto"
            })
          })
          chat = await handleResponse(createResponse)
        }
      } catch (error) {
        throw new Error(`Error obteniendo/creando chat: ${error.message}`)
      }
      
      // Crear nueva sesión
      const sessionResponse = await fetch(`${config.apiUrl}/api/v1/chats/${chat.id}/sessions`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          accumulated_context: "",
          status: "active"
        })
      })
      const session = await handleResponse(sessionResponse)
      sessionId = session.id
    }

         // Enviar mensaje usando endpoint de context-chat (mantener compatibilidad)
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

  // Obtener sesión específica
  getContextSession: async (sessionId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/sessions/${sessionId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  // Obtener sesión activa para un proyecto
  getActiveContextSession: async (projectId) => {
    try {
      // Usar endpoint de compatibilidad
      const response = await fetch(`${config.apiUrl}/api/v1/context-chat/projects/${projectId}/active-context-session`, {
        method: 'GET',
        headers: getAuthHeaders()
      })
      return handleResponse(response)
    } catch (error) {
      // Si no hay sesión activa, retornar null
      return null
    }
  },

  // ✅ NUEVO: Obtener sesiones detalladas de un chat específico
  getChatSessionsDetailed: async (chatId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/chats/${chatId}/sessions/detailed`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  // ✅ NUEVO: Obtener resumen de sesiones de contexto por proyecto
  getProjectContextSessionsSummary: async (projectId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/context-chat/projects/${projectId}/context-sessions-summary`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  // Finalizar construcción de contexto
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
  // FUNCIONES ESPECÍFICAS PARA CHATS
  // ==========================================
  
  // Obtener todos los chats de un proyecto
  getProjectChats: async (projectId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/chats`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  // Crear un nuevo chat
  createChat: async (projectId, title) => {
    const response = await fetch(`${config.apiUrl}/api/v1/projects/${projectId}/chats`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ title })
    })
    return handleResponse(response)
  },

  // Eliminar un chat
  deleteChat: async (chatId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/chats/${chatId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    return handleResponse(response)
  },

  // Obtener sesiones de un chat
  getChatSessions: async (chatId) => {
    const response = await fetch(`${config.apiUrl}/api/v1/chats/${chatId}/sessions`, {
      method: 'GET',
      headers: getAuthHeaders()
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