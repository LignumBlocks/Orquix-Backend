import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import api from '../services/api'
import { clarificationService } from '../services/clarificationService'

const useAppStore = create()(
  devtools(
    persist(
      (set, get) => ({
        // Estado de usuario y proyecto
        user: null,
        authToken: null,
        activeProject: null,
        projects: [],
        
        // Estado de chats
        projectChats: {}, // { projectId: [chats] }
        activeChat: null,
        loadingChats: false,

        // Estado de conversación
        conversations: [],
        activeConversation: null,
        isQuerying: false,
        lastResponse: null,

        // Estado de PreAnalyst
        preAnalystResult: null,
        clarificationSession: null,
        isClarificationActive: false,
        clarificationLoading: false,

        // Estado de continuidad
        continuityInfo: null,
        lastConversationContext: null,

        // ==========================================
        // NUEVO: Estado de Construcción de Contexto
        // ==========================================
        contextBuildingMode: false,
        contextSession: null,
        contextMessages: [],
        accumulatedContext: '',
        isContextBuilding: false,
        contextSessionId: null,

        // ✅ NUEVO: Estado de múltiples sesiones
        allContextSessions: [],
        loadingContextSessions: false,
        contextSessionsLastUpdated: null,

        // Acciones
        setUser: (user) => set({ user }),
        setAuthToken: (token) => set({ authToken: token }),
        setActiveProject: (project) => {
          console.log('🎯 Cambiando proyecto activo:', project?.name || 'null')
          
          set({ 
            activeProject: project,
            // Limpiar estados de carga
            isContextBuilding: false,
            isQuerying: false,
            clarificationLoading: false,
            error: null
          })
          
          if (project?.id) {
            // Cargar conversaciones del proyecto
            get().loadConversations(project.id).catch(error => {
              console.error('❌ Error loading conversations:', error)
              set({ conversations: [], error: null })
            })
            
            // Cargar contexto activo del proyecto (si existe)
            get().loadActiveContextForProject(project.id).catch(error => {
              console.error('❌ Error loading active context:', error)
            })
            
            // Cargar chats del proyecto
            get().loadProjectChats(project.id).catch(error => {
              console.error('❌ Error loading project chats:', error)
            })
          } else {
            // Si no hay proyecto activo, limpiamos todo
            console.log('🧹 Limpiando estado por falta de proyecto activo')
            set({ 
              conversations: [],
              accumulatedContext: '',
              contextMessages: [],
              contextSessionId: null,
              contextBuildingMode: false,
              activeChat: null,
              error: null
            })
          }
        },
        setProjects: (projects) => set({ projects }),

        // ==========================================
        // NUEVO: Acciones de Construcción de Contexto
        // ==========================================
        
        // Limpiar todos los estados de carga
        clearLoadingStates: () => {
          set({
            isQuerying: false,
            isContextBuilding: false,
            clarificationLoading: false,
            error: null
          })
        },
        
        // Activar modo de construcción de contexto
        startContextBuilding: () => {
          set({
            contextBuildingMode: true,
            contextSession: null,
            contextMessages: [],
            accumulatedContext: '',
            contextSessionId: null,
            // Limpiar estados de carga
            isQuerying: false,
            isContextBuilding: false,
            clarificationLoading: false,
            error: null
          })
        },

        // Enviar mensaje en construcción de contexto
        sendContextMessage: async (message) => {
          const { activeProject, contextSessionId } = get()
          if (!activeProject?.id) throw new Error('No hay proyecto activo')

          try {
            set({ 
              isContextBuilding: true, 
              error: null,
              // Asegurar que otros estados de carga estén limpios
              isQuerying: false,
              clarificationLoading: false
            })

            const response = await api.sendContextMessage(
              activeProject.id,
              message,
              contextSessionId
            )

            // Actualizar estado con la respuesta
            set(state => ({
              contextSessionId: response.session_id,
              contextMessages: [...state.contextMessages, {
                user_message: message,
                ai_response: response.ai_response,
                message_type: response.message_type,
                context_elements_count: response.context_elements_count || 0,
                suggestions: response.suggestions || []
              }],
              accumulatedContext: response.accumulated_context || '',
              isContextBuilding: false,
              error: null
            }))

            return response
          } catch (error) {
            console.error('Error sending context message:', error)
            
            // Asegurar que se limpia el estado de carga
            set({ 
              isContextBuilding: false,
              isQuerying: false,
              clarificationLoading: false,
              error: error.message || 'Error al enviar el mensaje'
            })
            
            // Agregar mensaje de error más informativo
            set(state => ({
              contextMessages: [...state.contextMessages, {
                user_message: message,
                ai_response: `Error: ${error.message || 'Problema de conexión'}. Por favor, intenta de nuevo.`,
                message_type: "error",
                context_elements_count: 0,
                suggestions: ["Verifica tu conexión", "Intenta reformular el mensaje", "Recarga la página si persiste"]
              }]
            }))
            
            return null
          }
        },

        // ✅ NUEVO: Refrescar contexto acumulado de una sesión
        refreshSessionContext: async (sessionId) => {
          if (!sessionId) return null

          try {
            const response = await fetch(`http://localhost:8000/api/v1/context-chat/sessions/${sessionId}/status`, {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer dev-mock-token-12345'
              }
            })

            if (!response.ok) {
              console.error('Error obteniendo estado de sesión:', response.status)
              return null
            }

            const sessionData = await response.json()
            
            // Actualizar el contexto acumulado en el store
            set({
              accumulatedContext: sessionData.accumulated_context || '',
              contextSessionId: sessionData.session_id
            })

            console.log('✅ Contexto acumulado actualizado:', {
              sessionId: sessionData.session_id,
              status: sessionData.status,
              contextLength: sessionData.context_length
            })

            return sessionData

          } catch (error) {
            console.error('❌ Error refrescando contexto de sesión:', error)
            return null
          }
        },

        // Finalizar construcción de contexto y enviar a IAs principales
        finalizeContextSession: async (finalQuestion) => {
          const { contextSessionId } = get()
          if (!contextSessionId) throw new Error('No hay sesión de contexto activa')

          try {
            set({ 
              isContextBuilding: true, 
              error: null,
              // Asegurar que otros estados de carga estén limpios
              isQuerying: false,
              clarificationLoading: false
            })

            const response = await api.finalizeContextSession(contextSessionId, finalQuestion)

            // Limpiar estado de construcción de contexto PERO MANTENER accumulatedContext para el sidebar
            set({
              contextBuildingMode: false,
              contextSession: null,
              contextMessages: [],
              // NO limpiar accumulatedContext - mantenerlo para el sidebar
              // accumulatedContext: '',
              contextSessionId: null,
              isContextBuilding: false,
              isQuerying: false,
              clarificationLoading: false
            })

            // Agregar la respuesta final a las conversaciones
            if (response.synthesis_text) {
              set(state => ({
                conversations: [{
                  id: Date.now(),
                  user_prompt: finalQuestion,
                  synthesis_preview: response.synthesis_text,
                  moderator_quality: response.quality || 'medium',
                  processing_time_ms: response.processing_time_ms || 0,
                  created_at: new Date().toISOString(),
                  context_used: get().accumulatedContext
                }, ...state.conversations]
              }))
            }

            return response
          } catch (error) {
            set({ 
              isContextBuilding: false,
              isQuerying: false,
              clarificationLoading: false,
              error: error.message 
            })
            throw error
          }
        },

        // Cancelar construcción de contexto
        cancelContextBuilding: () => {
          set({
            contextBuildingMode: false,
            contextSession: null,
            contextMessages: [],
            accumulatedContext: '',
            contextSessionId: null,
            isContextBuilding: false,
            isQuerying: false,
            clarificationLoading: false,
            error: null
          })
        },

        // Cargar contexto activo para un proyecto
        loadActiveContextForProject: async (projectId) => {
          try {
            console.log('🔍 Cargando contexto activo para proyecto:', projectId)
            const activeSession = await api.getActiveContextSession(projectId)
            
            // Si hay una sesión activa, cargar su contexto
            if (activeSession) {
              set({
                accumulatedContext: activeSession.accumulated_context || '',
                contextMessages: activeSession.conversation_history || [],
                contextSessionId: activeSession.session_id,
                contextBuildingMode: activeSession.session_status === 'active'
              })
              console.log('✅ Contexto activo cargado:', {
                sessionId: activeSession.session_id,
                contextLength: activeSession.accumulated_context?.length || 0,
                messagesCount: activeSession.conversation_history?.length || 0,
                status: activeSession.session_status
              })
            } else {
              // No hay sesión activa, limpiar contexto
              set({
                accumulatedContext: '',
                contextMessages: [],
                contextSessionId: null,
                contextBuildingMode: false
              })
              console.log('ℹ️ No hay contexto activo para proyecto:', projectId)
            }
          } catch (error) {
            // Si no hay sesión activa (404) o cualquier otro error, simplemente limpiar
            console.log('ℹ️ No se pudo cargar contexto activo:', error.message)
            set({
              accumulatedContext: '',
              contextMessages: [],
              contextSessionId: null,
              contextBuildingMode: false,
              error: null // Limpiar errores previos
            })
          }
        },

        // ==========================================
        // ACCIONES ORIGINALES (mantener compatibilidad)
        // ==========================================

        // Acciones de conversación
        sendQuery: async (query, includeContext = true, skipPreAnalysis = false, conversationMode = 'auto') => {
          try {
            set({ isQuerying: true, error: null })

            // Si no saltamos el preanálisis, lo ejecutamos primero
            if (!skipPreAnalysis) {
              set({ clarificationLoading: true })
              const preAnalysisResult = await api.analyzePrompt(query)
              set({ 
                preAnalystResult: preAnalysisResult,
                clarificationSession: preAnalysisResult.clarification_session,
                isClarificationActive: true,
                clarificationLoading: false
              })

              // Si hay preguntas de clarificación, esperamos la interacción del usuario
              if (preAnalysisResult.clarification_questions?.length > 0) {
                return
              }
            }

            // Enviamos la consulta al backend
            const response = await api.sendQuery(
              query,
              get().activeProject?.id,
              null // clarificationResponse
            )

            // Actualizamos el estado con la respuesta
            set({
              lastResponse: response,
              continuityInfo: response.continuity_info,
              lastConversationContext: response.conversation_context,
              conversations: [response, ...get().conversations],
              activeConversation: response,
              isQuerying: false,
              clarificationSession: null,
              isClarificationActive: false
            })

            return response
          } catch (error) {
            set({ 
              isQuerying: false,
              clarificationLoading: false,
              error: error.message
            })
            throw error
          }
        },

        // Acciones de clarificación
        continueClarification: async (userResponse) => {
          try {
            set({ clarificationLoading: true })
            const updatedSession = await api.continueClarification(
              get().activeProject?.id,
              get().clarificationSession.session_id,
              userResponse
            )
            set({ 
              clarificationSession: updatedSession,
              clarificationLoading: false
            })
          } catch (error) {
            set({ clarificationLoading: false })
            throw error
          }
        },

        completeClarification: async (refinedPrompt) => {
          try {
            set({ clarificationLoading: false, isClarificationActive: false })
            return await get().sendQuery(refinedPrompt, true, true)
          } catch (error) {
            set({ clarificationLoading: false })
            throw error
          }
        },

        cancelClarification: () => {
          set({
            clarificationSession: null,
            isClarificationActive: false,
            clarificationLoading: false,
            preAnalystResult: null
          })
        },

        // ==========================================
        // ACCIONES DE CHATS
        // ==========================================
        
        // Cargar chats de un proyecto
        loadProjectChats: async (projectId) => {
          if (!projectId) return
          
          try {
            set({ loadingChats: true })
            const response = await api.getProjectChats(projectId)
            const chats = response.chats || []
            
            set(state => ({
              projectChats: {
                ...state.projectChats,
                [projectId]: chats
              },
              loadingChats: false,
              error: null
            }))
            
            return chats
          } catch (error) {
            console.error('Error loading project chats:', error)
            set({ 
              loadingChats: false,
              error: null // No mostrar error al usuario, solo en consola
            })
            return []
          }
        },

        // Crear un nuevo chat
        createChat: async (projectId, title) => {
          if (!projectId || !title) return
          
          try {
            const newChat = await api.createChat(projectId, title)
            
            set(state => ({
              projectChats: {
                ...state.projectChats,
                [projectId]: [newChat, ...(state.projectChats[projectId] || [])]
              },
              activeChat: newChat
            }))
            
            return newChat
          } catch (error) {
            console.error('Error creating chat:', error)
            set({ error: error.message })
            throw error
          }
        },

        // Eliminar un chat
        deleteChat: async (chatId, projectId) => {
          if (!chatId || !projectId) return
          
          try {
            await api.deleteChat(chatId)
            
            set(state => ({
              projectChats: {
                ...state.projectChats,
                [projectId]: (state.projectChats[projectId] || []).filter(chat => chat.id !== chatId)
              },
              activeChat: state.activeChat?.id === chatId ? null : state.activeChat
            }))
          } catch (error) {
            console.error('Error deleting chat:', error)
            set({ error: error.message })
            throw error
          }
        },

        // Seleccionar chat activo
        setActiveChat: (chat) => {
          set({ activeChat: chat })
        },

        // Acciones de proyectos
        createProject: async (projectData) => {
          try {
            const newProject = await api.createProject(projectData)
            set(state => ({ 
              projects: [newProject, ...state.projects],
              activeProject: newProject, // Activar el nuevo proyecto automáticamente
              // LIMPIAR CONTEXTO para el nuevo proyecto
              accumulatedContext: '',
              contextMessages: [],
              contextSessionId: null,
              contextBuildingMode: false,
              isContextBuilding: false,
              // Limpiar también conversaciones
              conversations: []
            }))
            return newProject
          } catch (error) {
            console.error('Error creating project:', error)
            throw error
          }
        },

        // Cargar conversaciones
        loadConversations: async (projectId) => {
          try {
            const response = await api.getConversations(projectId)
            set({ 
              conversations: response.interactions || [], 
              error: null,
              conversationMetadata: {
                totalCount: response.total_count,
                currentPage: response.page,
                perPage: response.per_page,
                hasNext: response.has_next,
                hasPrev: response.has_prev
              }
            })
          } catch (error) {
            console.error('Error loading conversations:', error)
            set({ 
              conversations: [], 
              error: null,
              conversationMetadata: {
                totalCount: 0,
                currentPage: 1,
                perPage: 20,
                hasNext: false,
                hasPrev: false
              }
            }) // No mostramos error al usuario
          }
        },

        // Inicialización
        initialize: async () => {
          try {
            const projects = await api.getProjects()
            set({ projects, error: null })
          } catch (error) {
            console.error('Error loading projects:', error)
            set({ error: error.message })
          }
        },

        // Alias para mantener compatibilidad
        loadProjects: async () => {
          try {
            const projects = await api.getProjects()
            set({ projects, error: null })
          } catch (error) {
            console.error('Error loading projects:', error)
            set({ error: error.message })
          }
        },

        // Acciones adicionales
        clarificationNeeded: false,
        clarificationQuestions: [],
        error: null,
        handleClarificationResponse: async (response) => {
          const { activeProject } = get()
          if (!activeProject?.id) return

          set({ isQuerying: true, error: null })
          
          try {
            const result = await clarificationService.submitClarification(
              activeProject.id,
              get().preAnalystResult.original_query,
              response
            )

            // Actualizamos las conversaciones
            const conversations = await api.getConversations(activeProject.id)
            set({ 
              conversations,
              isQuerying: false,
              error: null,
              clarificationNeeded: false,
              clarificationQuestions: [],
              preAnalystResult: null,
              continuityInfo: result.continuity_info || null
            })
          } catch (error) {
            console.error('Error handling clarification:', error)
            set({ 
              isQuerying: false,
              error: error.message,
              clarificationNeeded: false,
              clarificationQuestions: [],
              preAnalystResult: null
            })
          }
        },
        clearError: () => set({ error: null }),

        // Refrescar contexto de sesión desde el backend
        refreshSessionContext: async () => {
          const state = get()
          if (!state.contextSessionId) return
          
          try {
            const session = await api.getContextSession(state.contextSessionId)
            if (session) {
              set({
                accumulatedContext: session.accumulated_context || '',
                contextSession: session
              })
            }
          } catch (error) {
            console.error('Error refreshing session context:', error)
          }
        },

        // ✅ NUEVO: Cargar sesiones de contexto por chat
        loadContextSessionsByChat: async (chatId) => {
          if (!chatId) return
          
          set({ loadingContextSessions: true })
          
          try {
            const response = await api.getChatSessionsDetailed(chatId)
            
            // Actualizar las sesiones en el estado
            set(state => {
              // Encontrar y actualizar el chat en allContextSessions
              const updatedSessions = [...state.allContextSessions]
              const chatIndex = updatedSessions.findIndex(chat => chat.chat_id === chatId)
              
              if (chatIndex >= 0) {
                updatedSessions[chatIndex] = {
                  chat_id: response.chat_id,
                  chat_title: response.chat_title,
                  sessions: response.sessions,
                  sessions_count: response.total_sessions
                }
              } else {
                updatedSessions.push({
                  chat_id: response.chat_id,
                  chat_title: response.chat_title,
                  sessions: response.sessions,
                  sessions_count: response.total_sessions
                })
              }
              
              return {
                allContextSessions: updatedSessions,
                contextSessionsLastUpdated: new Date(),
                loadingContextSessions: false
              }
            })
            
            // Si hay una sesión activa, actualizarla en el estado
            if (response.active_session_id) {
              const activeSession = response.sessions.find(s => s.id === response.active_session_id)
              if (activeSession) {
                set({
                  contextSessionId: activeSession.id,
                  accumulatedContext: activeSession.accumulated_context || '',
                  contextSession: activeSession
                })
              }
            }
            
            return response
          } catch (error) {
            console.error('Error loading chat sessions:', error)
            set({ 
              loadingContextSessions: false,
              error: error.message 
            })
            throw error
          }
        },

        // ✅ NUEVO: Cargar resumen de sesiones de todo el proyecto
        loadProjectSessionsSummary: async (projectId) => {
          if (!projectId) return
          
          set({ loadingContextSessions: true })
          
          try {
            const response = await api.getProjectContextSessionsSummary(projectId)
            
            // Convertir el formato del backend al formato esperado por el frontend
            const allSessions = []
            if (response.chats_with_sessions) {
              response.chats_with_sessions.forEach(chat => {
                if (chat.sessions) {
                  chat.sessions.forEach(session => {
                    allSessions.push({
                      ...session,
                      chat_id: chat.chat_id,
                      chat_title: chat.chat_title
                    })
                  })
                }
              })
            }
            
            set({
              allContextSessions: allSessions,
              contextSessionsLastUpdated: new Date(),
              loadingContextSessions: false
            })
            
            return response
          } catch (error) {
            console.error('Error loading project sessions summary:', error)
            set({ 
              loadingContextSessions: false,
              error: error.message 
            })
            throw error
          }
        },

        // ✅ NUEVO: Seleccionar sesión de contexto específica
        selectContextSession: (sessionId) => {
          const state = get()
          const session = state.allContextSessions.find(s => s.id === sessionId)
          
          if (session) {
            console.log('🎯 Seleccionando sesión:', {
              sessionId: session.id,
              status: session.status,
              contextLength: session.accumulated_context?.length || 0
            })
            
            set({
              contextSessionId: session.id,
              accumulatedContext: session.accumulated_context || '',
              contextSession: session,
              contextBuildingMode: session.status === 'active'
            })
          }
        },

        // ✅ NUEVO: Actualizar sesión específica en la lista
        updateContextSessionInList: (sessionId, updates) => {
          set(state => ({
            allContextSessions: state.allContextSessions.map(session => 
              session.id === sessionId 
                ? { ...session, ...updates }
                : session
            )
          }))
        },

        // ✅ NUEVO: Seleccionar chat y cargar todo su contexto
        selectChatAndLoadContext: async (chat, project = null) => {
          try {
            console.log('🎯 Seleccionando chat y cargando contexto:', { 
              chatId: chat.id, 
              chatTitle: chat.title,
              projectId: project?.id || chat.project_id 
            })

            // 1. Asegurar que el proyecto esté activo
            const currentProject = project || get().activeProject
            const targetProjectId = chat.project_id
            
            console.log('🔍 Verificando proyecto activo:', {
              currentProjectId: currentProject?.id,
              targetProjectId: targetProjectId,
              needsProjectChange: !currentProject || currentProject.id !== targetProjectId
            })
            
            if (!currentProject || currentProject.id !== targetProjectId) {
              // Si el chat pertenece a otro proyecto, cambiar proyecto activo
              let projectToSet = project
              
              if (!projectToSet) {
                // Buscar el proyecto en la lista
                projectToSet = get().projects.find(p => p.id === targetProjectId)
                
                // Si no está en la lista, cargar los proyectos primero
                if (!projectToSet) {
                  console.log('🔄 Proyecto no encontrado en lista, cargando proyectos...')
                  try {
                    await get().loadProjects()
                    projectToSet = get().projects.find(p => p.id === targetProjectId)
                  } catch (error) {
                    console.error('Error cargando proyectos:', error)
                  }
                }
              }
              
              if (projectToSet) {
                console.log('🎯 Activando proyecto:', projectToSet.name)
                get().setActiveProject(projectToSet)
              } else {
                console.warn('⚠️ No se pudo encontrar el proyecto para el chat')
              }
            }

            // 2. Seleccionar el chat activo
            set({ 
              activeChat: chat,
              loadingContextSessions: true,
              error: null
            })

            // 3. Cargar todas las sesiones del chat
            const chatSessionsResponse = await api.getChatSessionsDetailed(chat.id)
            
            console.log('📊 Respuesta del backend:', {
              totalSessions: chatSessionsResponse.total_sessions,
              activeSessionId: chatSessionsResponse.active_session_id,
              sessions: chatSessionsResponse.sessions?.length || 0
            })
            
            // 4. Actualizar el estado con las sesiones del chat
            set(state => {
              // Convertir las sesiones a formato plano para el sidebar
              const sessionsForSidebar = (chatSessionsResponse.sessions || []).map(session => ({
                ...session,
                chat_id: chatSessionsResponse.chat_id,
                chat_title: chatSessionsResponse.chat_title
              }))
              
              // Filtrar sesiones de otros chats y agregar las nuevas
              const otherSessions = state.allContextSessions.filter(session => 
                !session.chat_id || session.chat_id !== chat.id
              )
              
              return {
                allContextSessions: [...otherSessions, ...sessionsForSidebar],
                loadingContextSessions: false
              }
            })

            // 5. Si hay una sesión activa, cargar su contexto
            let activeSession = null
            if (chatSessionsResponse.sessions) {
              // Buscar sesión activa (status = 'active')
              activeSession = chatSessionsResponse.sessions.find(s => s.status === 'active')
              
              // Si no hay activa, tomar la más reciente
              if (!activeSession && chatSessionsResponse.sessions.length > 0) {
                activeSession = chatSessionsResponse.sessions.sort((a, b) => 
                  new Date(b.started_at) - new Date(a.started_at)
                )[0]
              }
            }

            // 6. Actualizar contexto con la sesión seleccionada
            if (activeSession) {
              set({
                contextSessionId: activeSession.id,
                accumulatedContext: activeSession.accumulated_context || '',
                contextBuildingMode: activeSession.status === 'active',
                contextSession: activeSession
              })

              console.log('✅ Contexto cargado desde sesión:', {
                sessionId: activeSession.id,
                status: activeSession.status,
                contextLength: activeSession.accumulated_context?.length || 0
              })
            } else {
              // No hay sesiones, limpiar contexto
              set({
                contextSessionId: null,
                accumulatedContext: '',
                contextBuildingMode: false,
                contextSession: null
              })

              console.log('ℹ️ No hay sesiones en el chat, contexto limpiado')
            }

            // 7. También cargar el resumen general del proyecto para tener vista completa
            if (currentProject?.id) {
              get().loadProjectSessionsSummary(currentProject.id).catch(error => {
                console.error('Error cargando resumen del proyecto:', error)
              })
            }

            console.log('✅ Chat seleccionado y contexto cargado exitosamente')
            return chatSessionsResponse

          } catch (error) {
            console.error('❌ Error seleccionando chat y cargando contexto:', error)
            set({ 
              loadingContextSessions: false,
              error: error.message 
            })
            throw error
          }
        }
      }),
      {
        name: 'orquix-store',
        partialize: (state) => ({
          // Solo persistir estos campos, NO activeProject
          user: state.user,
          authToken: state.authToken,
          projects: state.projects,
          // NO persistir activeProject, activeChat para forzar selección manual
        })
      }
    )
  )
)

export default useAppStore 