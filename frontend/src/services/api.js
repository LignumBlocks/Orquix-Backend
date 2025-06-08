import axios from 'axios'
import { config } from '../config'

// Configuración base de Axios
const api = axios.create({
  baseURL: config.API_BASE_URL,
  timeout: 60000, // 60 segundos para consultas largas de orquestación
  headers: {
    'Content-Type': 'application/json',
  }
})

// Interceptor para agregar token de autenticación
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Interceptor para manejar respuestas y errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // En desarrollo, algunos errores 401 pueden ser normales
    if (error.response?.status === 401 && !import.meta.env.PROD) {
      console.warn('Auth error in development - this is expected for some endpoints')
      // No redirigir en desarrollo para permitir testing
      return Promise.reject(error)
    }
    
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 🔐 Servicios de Autenticación
export const authService = {
  async getSession() {
    try {
      const response = await api.get('/api/v1/auth/session')
      return response.data
    } catch (error) {
      // Fallback mock para desarrollo
      if (import.meta.env.DEV) {
        return {
          user: {
            id: 'mock-user-1',
            email: 'dev@orquix.com',
            name: 'Developer User'
          }
        }
      }
      throw error
    }
  },

  async validateToken() {
    try {
      const response = await api.post('/api/v1/auth/validate-token')
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        return { valid: true }
      }
      throw error
    }
  },

  async getUserInfo() {
    try {
      const response = await api.get('/api/v1/auth/me')
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        return {
          id: 'mock-user-1',
          email: 'dev@orquix.com',
          name: 'Developer User'
        }
      }
      throw error
    }
  },

  async signOut() {
    try {
      const response = await api.post('/api/v1/auth/signout')
      localStorage.removeItem('auth_token')
      return response.data
    } catch (error) {
      localStorage.removeItem('auth_token')
      throw error
    }
  }
}

// 📁 Servicios de Proyectos
export const projectService = {
  async getProjects(skip = 0, limit = 50) {
    try {
      const response = await api.get('/api/v1/projects', {
        params: { skip, limit }
      })
      return response.data
    } catch (error) {
      // Fallback con proyectos mock para desarrollo
      if (import.meta.env.DEV && error.response?.status === 401) {
        console.warn('Using mock projects for development')
        return [
          {
            id: 'mock-project-1',
            name: 'Demo Project - Fintech Analysis',
            description: 'Proyecto de demostración para análisis fintech',
            created_at: new Date().toISOString(),
            moderator_personality: 'Analytical'
          }
        ]
      }
      throw error
    }
  },

  async getProject(projectId) {
    try {
      const response = await api.get(`/api/v1/projects/${projectId}`)
      return response.data
    } catch (error) {
      if (import.meta.env.DEV && error.response?.status === 401) {
        return {
          id: projectId,
          name: 'Demo Project - Fintech Analysis',
          description: 'Proyecto de demostración para análisis fintech',
          created_at: new Date().toISOString(),
          moderator_personality: 'Analytical'
        }
      }
      throw error
    }
  },

  async createProject(projectData) {
    try {
      const response = await api.post('/api/v1/projects', projectData)
      return response.data
    } catch (error) {
      console.error('Error creating project:', error)
      
      // Solo usar fallback si no hay token o si es realmente un error de auth
      if (import.meta.env.DEV && error.response?.status === 401 && !localStorage.getItem('auth_token')) {
        console.warn('Using mock project creation for development (no auth token)')
        return {
          id: `mock-project-${Date.now()}`,
          ...projectData,
          created_at: new Date().toISOString()
        }
      }
      throw error
    }
  },

  async updateProject(projectId, projectData) {
    try {
      const response = await api.put(`/api/v1/projects/${projectId}`, projectData)
      return response.data
    } catch (error) {
      if (import.meta.env.DEV && error.response?.status === 401) {
        return {
          id: projectId,
          ...projectData,
          updated_at: new Date().toISOString()
        }
      }
      throw error
    }
  },

  async deleteProject(projectId) {
    try {
      const response = await api.delete(`/api/v1/projects/${projectId}`)
      return response.data
    } catch (error) {
      if (import.meta.env.DEV && error.response?.status === 401) {
        return { success: true }
      }
      throw error
    }
  },

  // 🌟 ENDPOINT PRINCIPAL - CONSULTA/CHAT
  async query(projectId, queryData) {
    try {
      const response = await api.post(`/api/v1/projects/${projectId}/query`, queryData)
      return response.data
    } catch (error) {
      // Para testing en desarrollo, crear respuesta mock
      if (import.meta.env.DEV && error.response?.status === 401) {
        console.warn('Using mock query response for development')
        await new Promise(resolve => setTimeout(resolve, 2000)) // Simular delay
        
        return {
          interaction_event_id: `mock-interaction-${Date.now()}`,
          synthesis_text: `**Análisis basado en tu consulta: "${queryData.user_prompt_text}"**\n\nEsta es una respuesta de demostración del sistema Orquix. En un entorno de producción, esta respuesta sería generada por:\n\n1. **Múltiples IAs especializadas** trabajando en paralelo\n2. **Moderador IA v2.0** sintetizando las respuestas\n3. **Context Manager** proporcionando información relevante\n\nLas características clave incluyen:\n- Orquestación inteligente de múltiples proveedores de IA\n- Síntesis de alta calidad con meta-análisis\n- Tiempo de respuesta optimizado\n- Fallback automático en caso de errores`,
          moderator_quality: 'high',
          key_themes: ['demo', 'orquestación', 'IA múltiple', 'síntesis'],
          contradictions: [],
          consensus_areas: ['funcionalidad básica', 'interfaz responsive'],
          recommendations: [
            'Conectar con backend real para funcionalidad completa',
            'Configurar autenticación apropiada',
            'Revisar logs del sistema para troubleshooting'
          ],
          suggested_questions: [
            '¿Cómo funciona la orquestación de IAs?',
            '¿Qué hace el moderador v2.0?',
            '¿Cuáles son las ventajas del sistema?'
          ],
          research_areas: ['arquitectura distribuida', 'síntesis de IA', 'moderación inteligente'],
          individual_responses: [
            {
              agent_name: 'Agent1',
              response: 'Respuesta desde perspectiva técnica...',
              processing_time_ms: 1200
            },
            {
              agent_name: 'Agent2', 
              response: 'Respuesta desde perspectiva analítica...',
              processing_time_ms: 980
            }
          ],
          processing_time_ms: 1850,
          fallback_used: false,
          created_at: new Date().toISOString()
        }
      }
      throw error
    }
  }
}

// 📜 Servicios de Historial
export const historyService = {
  async getInteractions(projectId, page = 1, perPage = 20) {
    try {
      const response = await api.get(`/api/v1/projects/${projectId}/interaction_events`, {
        params: { page, per_page: perPage }
      })
      return response.data
    } catch (error) {
      if (import.meta.env.DEV && error.response?.status === 401) {
        return { interactions: [] }
      }
      throw error
    }
  },

  async getInteractionDetail(projectId, interactionId) {
    try {
      const response = await api.get(`/api/v1/projects/${projectId}/interaction_events/${interactionId}`)
      return response.data
    } catch (error) {
      if (import.meta.env.DEV && error.response?.status === 401) {
        return { interaction: null }
      }
      throw error
    }
  },

  async deleteInteraction(projectId, interactionId) {
    try {
      const response = await api.delete(`/api/v1/projects/${projectId}/interaction_events/${interactionId}`)
      return response.data
    } catch (error) {
      if (import.meta.env.DEV && error.response?.status === 401) {
        return { success: true }
      }
      throw error
    }
  }
}

// 💬 Servicios de Feedback
export const feedbackService = {
  async createFeedback(feedbackData) {
    const response = await api.post('/api/v1/feedback', feedbackData)
    return response.data
  },

  async getFeedback(page = 1, perPage = 20, filters = {}) {
    const response = await api.get('/api/v1/feedback', {
      params: { page, per_page: perPage, ...filters }
    })
    return response.data
  },

  async getFeedbackStats(referenceType = null, days = 30) {
    const response = await api.get('/api/v1/feedback/stats', {
      params: { reference_type: referenceType, days }
    })
    return response.data
  },

  async deleteFeedback(feedbackId) {
    const response = await api.delete(`/api/v1/feedback/${feedbackId}`)
    return response.data
  }
}

// 🏥 Servicios de Health/Estado
export const healthService = {
  async getHealth() {
    const response = await api.get('/api/v1/health')
    return response.data
  },

  async getDetailedHealth() {
    const response = await api.get('/api/v1/health/detailed')
    return response.data
  },

  async getDatabaseHealth() {
    const response = await api.get('/api/v1/health/database')
    return response.data
  },

  async getAiProvidersHealth() {
    const response = await api.get('/api/v1/health/ai-providers')
    return response.data
  },

  async getSystemHealth() {
    const response = await api.get('/api/v1/health/system')
    return response.data
  },

  // Métricas de orquestación
  async getOrchestrationMetrics(days = 1) {
    try {
      const response = await api.get('/api/v1/health/orchestration/metrics', {
        params: { days }
      })
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        return { metrics: {} }
      }
      throw error
    }
  },

  async getActiveOrchestrations() {
    try {
      const response = await api.get('/api/v1/health/orchestration/active')
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        return { active: [] }
      }
      throw error
    }
  },

  async getPerformanceMetrics() {
    try {
      const response = await api.get('/api/v1/health/orchestration/performance')
      return response.data
    } catch (error) {
      if (import.meta.env.DEV) {
        return {
          avg_response_time_ms: 1500,
          total_queries_today: 0,
          success_rate: 100,
          active_sessions: 1
        }
      }
      throw error
    }
  }
}

// 🎯 Utilidades
export const utilsService = {
  async getApiInfo() {
    const response = await api.get('/api')
    return response.data
  },

  async getApiStatus() {
    const response = await api.get('/api/status')
    return response.data
  }
}

export default api 