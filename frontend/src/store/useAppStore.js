import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { projectService, healthService, historyService } from '../services/api'
import { clarificationService } from '../services/clarificationService'

const useAppStore = create()(
  devtools(
    persist(
      (set, get) => ({
        // 🔐 Estado de autenticación
        user: null,
        isAuthenticated: false,
        authToken: localStorage.getItem('auth_token'),

        // 📁 Estado de proyectos
        projects: [],
        activeProject: null,
        loadingProjects: false,

        // 💬 Estado de conversación
        conversations: [],
        activeConversation: null,
        isQuerying: false,
        lastResponse: null,

        // 🧠 Estado de clarificación PreAnalyst
        clarificationSession: null,
        isClarificationActive: false,
        clarificationLoading: false,

        // 🤖 Estado de IAs
        aiAgents: [],
        aiHealth: null,
        loadingAiHealth: false,

        // ⚙️ Configuración del moderador
        moderatorConfig: {
          personality: 'Analytical',
          temperature: 0.7,
          length: 0.5
        },

        // 📊 Estado del sistema
        systemHealth: null,
        lastHealthCheck: null,

        // 🔄 Acciones de autenticación
        setUser: (user) => set({ user, isAuthenticated: !!user }),
        setAuthToken: (token) => {
          localStorage.setItem('auth_token', token)
          set({ authToken: token, isAuthenticated: !!token })
        },
        clearAuth: () => {
          localStorage.removeItem('auth_token')
          set({ user: null, isAuthenticated: false, authToken: null })
        },

        // 📁 Acciones de proyectos
        setProjects: (projects) => set({ projects }),
        setActiveProject: (project) => set({ activeProject: project }),
        
        loadProjects: async () => {
          set({ loadingProjects: true })
          try {
            const projects = await projectService.getProjects()
            set({ projects, loadingProjects: false })
            
            // Si no hay proyecto activo, seleccionar el primero
            if (!get().activeProject && projects.length > 0) {
              set({ activeProject: projects[0] })
            }
          } catch (error) {
            console.error('Error loading projects:', error)
            set({ loadingProjects: false })
          }
        },

        createProject: async (projectData) => {
          try {
            const newProject = await projectService.createProject(projectData)
            const currentProjects = get().projects
            set({ 
              projects: [...currentProjects, newProject],
              activeProject: newProject 
            })
            return newProject
          } catch (error) {
            console.error('Error creating project:', error)
            throw error
          }
        },

        updateProject: async (projectId, projectData) => {
          try {
            const updatedProject = await projectService.updateProject(projectId, projectData)
            const projects = get().projects.map(p => 
              p.id === projectId ? updatedProject : p
            )
            set({ projects })
            
            if (get().activeProject?.id === projectId) {
              set({ activeProject: updatedProject })
            }
            return updatedProject
          } catch (error) {
            console.error('Error updating project:', error)
            throw error
          }
        },

        deleteProject: async (projectId) => {
          try {
            await projectService.deleteProject(projectId)
            const projects = get().projects.filter(p => p.id !== projectId)
            set({ projects })
            
            if (get().activeProject?.id === projectId) {
              set({ activeProject: projects[0] || null })
            }
          } catch (error) {
            console.error('Error deleting project:', error)
            throw error
          }
        },

        // 💬 Acciones de conversación
        setConversations: (conversations) => set({ conversations }),
        addConversation: (conversation) => {
          const conversations = get().conversations
          set({ conversations: [conversation, ...conversations] })
        },

        // 🧠 Acciones de clarificación PreAnalyst
        startClarification: async (message) => {
          console.log('startClarification', message)
          const { activeProject } = get()
          if (!activeProject) {
            throw new Error('No hay proyecto activo')
          }

          set({ clarificationLoading: true, isClarificationActive: true })
          
          try {
            const response = await clarificationService.startClarificationSession(
              activeProject.id, 
              message
            )
            
            set({ 
              clarificationSession: response,
              clarificationLoading: false
            })

            return response
          } catch (error) {
            set({ clarificationLoading: false, isClarificationActive: false })
            console.error('Error starting clarification:', error)
            throw error
          }
        },

        continueClarification: async (userResponse) => {
          console.log('continueClarification', userResponse)
          const { activeProject, clarificationSession } = get()
          if (!activeProject || !clarificationSession) {
            throw new Error('No hay sesión de clarificación activa')
          }

          set({ clarificationLoading: true })
          
          try {
            const response = await clarificationService.continueClarificationSession(
              clarificationSession.session_id,
              activeProject.id,
              userResponse
            )
            
            set({ 
              clarificationSession: response,
              clarificationLoading: false
            })

            return response
          } catch (error) {
            set({ clarificationLoading: false })
            console.error('Error continuing clarification:', error)
            throw error
          }
        },

        completeClarification: (refinedPrompt) => {
          console.log('completeClarification', refinedPrompt)
          set({ 
            isClarificationActive: false,
            clarificationSession: null,
            clarificationLoading: false
          })
          
                     // Enviar la consulta refinada automáticamente (saltando pre-análisis)
           return get().sendQuery(refinedPrompt, true, true)
        },

        cancelClarification: () => {
          console.log('cancelClarification')
          set({ 
            isClarificationActive: false,
            clarificationSession: null,
            clarificationLoading: false
          })
        },

        // 🌟 ACCIÓN PRINCIPAL - QUERY/CHAT
        sendQuery: async (message, includeContext = true, skipPreAnalysis = false) => {
          console.log('sendQuery', message, includeContext, skipPreAnalysis)
          const { activeProject, moderatorConfig } = get()
          if (!activeProject) {
            throw new Error('No hay proyecto activo')
          }

          // Detectar si necesita pre-análisis (prompts cortos o con palabras clave)
          const needsPreAnalysis = !skipPreAnalysis && (
            message.length < 50 || 
            /\b(ayuda|necesito|quiero|como|que|puedo)\b/i.test(message)
          )

          if (needsPreAnalysis) {
            // Intentar iniciar clarificación primero
            try {
              return await get().startClarification(message)
            } catch (error) {
              console.warn('PreAnalyst no disponible, continuando con query normal:', error)
              // Si el PreAnalyst falla, continuar con el flujo normal
            }
          }

          set({ isQuerying: true, lastResponse: null })
          
          try {
            const queryData = {
              user_prompt_text: message,
              include_context: includeContext,
              temperature: moderatorConfig.temperature,
              max_tokens: Math.round(moderatorConfig.length * 4000) + 100 // Convertir 0-1 a 100-4000
            }

            const response = await projectService.query(activeProject.id, queryData)
            
            // Crear objeto de conversación
            const conversation = {
              id: response.interaction_event_id,
              question: message,
              response: response.synthesis_text,
              moderatorQuality: response.moderator_quality,
              keyThemes: response.key_themes,
              contradictions: response.contradictions,
              consensusAreas: response.consensus_areas,
              recommendations: response.recommendations,
              suggestedQuestions: response.suggested_questions,
              researchAreas: response.research_areas,
              individualResponses: response.individual_responses,
              processingTime: response.processing_time_ms,
              fallbackUsed: response.fallback_used,
              createdAt: response.created_at,
              projectId: activeProject.id,
              contextInfo: response.context_info
            }

            set({ 
              isQuerying: false, 
              lastResponse: response,
              activeConversation: conversation
            })

            // Agregar a la lista de conversaciones
            get().addConversation(conversation)

            return response
          } catch (error) {
            set({ isQuerying: false })
            console.error('Error sending query:', error)
            throw error
          }
        },

        // 📜 Acciones de historial
        loadConversations: async (projectId) => {
          try {
            const history = await historyService.getInteractions(projectId || get().activeProject?.id)
            set({ conversations: history.interactions || [] })
          } catch (error) {
            console.error('Error loading conversations:', error)
          }
        },

        // 🤖 Acciones de IAs
        setAiAgents: (agents) => set({ aiAgents: agents }),
        setAiHealth: (health) => set({ aiHealth: health }),

        loadAiHealth: async () => {
          set({ loadingAiHealth: true })
          try {
            // Solo usar endpoints que existen
            const aiProviders = await healthService.getAiProvidersHealth()
            
            // Para performance y active, usar valores por defecto si fallan
            let performance = {
              avg_response_time_ms: 1500,
              total_queries_today: 0,
              success_rate: 100,
              active_sessions: 1
            }
            
            let active = { active: [] }
            
            // Intentar obtener métricas adicionales, pero no fallar si no existen
            try {
              performance = await healthService.getPerformanceMetrics()
            } catch (error) {
              console.warn('Performance metrics endpoint not available:', error.message)
            }
            
            try {
              active = await healthService.getActiveOrchestrations()
            } catch (error) {
              console.warn('Active orchestrations endpoint not available:', error.message)
            }
            
            // Simular datos de agentes basados en el health real
            const mockAgents = [
              {
                id: 1, name: 'Agent1', status: 'online', latency: '1.2s',
                icon: '🤖', color: 'blue', provider: 'OpenAI'
              },
              {
                id: 2, name: 'Agent2', status: 'online', latency: '0.8s',
                icon: '🤖', color: 'blue', provider: 'Anthropic'
              },
              {
                id: 3, name: 'Agent3', status: aiProviders.openai?.status === 'healthy' ? 'online' : 'error',
                latency: '12.0s', icon: '💎', color: 'blue', provider: 'OpenAI'
              }
            ]

            set({ 
              aiAgents: mockAgents,
              aiHealth: { aiProviders, performance, active },
              loadingAiHealth: false 
            })
          } catch (error) {
            console.error('Error loading AI health:', error)
            set({ loadingAiHealth: false })
          }
        },

        // ⚙️ Acciones de configuración
        setModeratorConfig: (config) => set({ moderatorConfig: config }),
        updateModeratorConfig: (updates) => {
          const currentConfig = get().moderatorConfig
          set({ moderatorConfig: { ...currentConfig, ...updates } })
        },

        // 📊 Acciones de sistema
        loadSystemHealth: async () => {
          try {
            const health = await healthService.getDetailedHealth()
            set({ 
              systemHealth: health, 
              lastHealthCheck: new Date().toISOString() 
            })
          } catch (error) {
            console.error('Error loading system health:', error)
          }
        },

        // 🔄 Acciones de inicialización
        initialize: async () => {
          const token = localStorage.getItem('auth_token')
          if (token) {
            set({ authToken: token, isAuthenticated: true })
            try {
              // En una implementación real, validaríamos el token aquí
              await get().loadProjects()
              await get().loadAiHealth()
              await get().loadSystemHealth()
            } catch (error) {
              console.error('Error initializing app:', error)
            }
          }
        }
      }),
      {
        name: 'orquix-app-storage',
        partialize: (state) => ({
          moderatorConfig: state.moderatorConfig,
          activeProject: state.activeProject,
          authToken: state.authToken
        })
      }
    ),
    {
      name: 'orquix-app-store'
    }
  )
)

export default useAppStore 