import { useState, useRef, useEffect } from 'react'
import { MicIcon, SendIcon, LoaderIcon, AlertCircleIcon, MessageSquareIcon, BrainIcon, ArrowRightIcon, ChevronDownIcon, ChevronUpIcon, CheckIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'
import ConversationFlow from '../ui/ConversationFlow'
import AIResponseCard from '../ui/AIResponseCard'
import ClarificationDialog from '../ui/ClarificationDialog'
import ConversationStatePanel from '../ui/ConversationStatePanel'
import config from '../../config'


const CenterColumn = ({ activeProject }) => {
  const [contextSession, setContextSession] = useState(null)
  const [conversationFlow, setConversationFlow] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState(null)
  const [isQuerying, setIsQuerying] = useState(false)
  const [isSendingToAIs, setIsSendingToAIs] = useState(false)
  const [isContextBuilding, setIsContextBuilding] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [expandedPrompts, setExpandedPrompts] = useState({})
  const [isQueryingAIs, setIsQueryingAIs] = useState(false)
  const [retryingProviders, setRetryingProviders] = useState({}) // Track which providers are being retried
  const [isGeneratingModeratorPrompt, setIsGeneratingModeratorPrompt] = useState(false)
  const [moderatorPromptData, setModeratorPromptData] = useState(null)
  const [isSynthesizing, setIsSynthesizing] = useState(false)
  const [synthesisData, setSynthesisData] = useState(null)
  
  // ==========================================
  // NUEVO: Estados para el botón "Orquestar"
  // ==========================================
  // Estado de orquestación eliminado - ahora todo se hace en un solo paso
  const [currentPromptId, setCurrentPromptId] = useState(null)
  const [generatedPrompt, setGeneratedPrompt] = useState(null)
  const [synthesisSessionId, setSynthesisSessionId] = useState(null)
  const [isOrchestrating, setIsOrchestrating] = useState(false)
  const [isEditingPrompt, setIsEditingPrompt] = useState(false)
  const [editingPromptId, setEditingPromptId] = useState(null)
  const [editedPromptText, setEditedPromptText] = useState('')

  const chatContainerRef = useRef(null)

  const {
    conversations,
    activeConversation,
    clarificationLoading,
    clarificationNeeded,
    clarificationQuestions,
    continueClarification,
    completeClarification,
    cancelClarification,
    sendQuery,
    // Estados de construcción de contexto integrados
    contextMessages,
    accumulatedContext,
    contextSessionId,
    isContextBuilding: storeIsContextBuilding,
    sendContextMessage,
    finalizeContextSession,
    refreshSessionContext,  // ✅ NUEVO: Función para refrescar contexto
    loadProjectSessionsSummary,  // ✅ NUEVO: Función para recargar todas las sesiones
    clearLoadingStates
  } = useAppStore()

  // Limpiar estados de carga al montar el componente o cambiar proyecto
  useEffect(() => {
    clearLoadingStates()
    setError(null)
    setConversationFlow([])
    setContextSession(null)
    // Resetear estados de orquestación
    setCurrentPromptId(null)
    setGeneratedPrompt(null)
    setSynthesisSessionId(null)
    setIsOrchestrating(false)
  }, [activeProject?.id, clearLoadingStates])

  // Auto-limpiar errores después de 5 segundos
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error])

  // Scroll al fondo cuando se agregan nuevos mensajes
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [conversationFlow])

  const sendToContextChat = async (userMessage) => {
    setIsProcessing(true)
    setError(null)

    try {
      // Usar la función del store para que se actualice correctamente el accumulatedContext
      const response = await sendContextMessage(userMessage)
      
      if (response) {
        // Actualizar session si es nueva
        if (!contextSession && response.session_id) {
          setContextSession({ session_id: response.session_id })
        }

        // Agregar interacción al flujo conversacional LOCAL
        const newInteraction = {
          id: Date.now(),
          type: 'context_interaction',
          user_message: userMessage,
          ai_response: response.ai_response,
          message_type: response.message_type,
          accumulated_context: response.accumulated_context,
          suggestions: response.suggestions || [],
          context_elements_count: response.context_elements_count,
          suggested_final_question: response.suggested_final_question,
          timestamp: new Date()
        }

        setConversationFlow(prev => [...prev, newInteraction])
      }

    } catch (error) {
      console.error('Error en context chat:', error)
      setError(error.message || 'Error al procesar el mensaje')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSendMessage = async (e) => {
    if (e) {
      e.preventDefault()
    }
    
    console.log('🚀 handleSendMessage called:', { 
      message: message.trim(), 
      isQuerying, 
      clarificationLoading, 
      isContextBuilding,
      activeProject: activeProject?.id 
    })
    
    if (!message.trim() || isProcessing) {
      console.log('❌ Message is empty or processing, returning')
      return
    }
    
    const currentMessage = message.trim()
    setMessage('')
    setError(null)

    try {
      // Siempre usar el flujo normal de consulta
      console.log('💬 Sending query:', currentMessage)
      await sendToContextChat(currentMessage)
    } catch (error) {
      console.error('Error sending message:', error)
      setError(error.message || 'Error al enviar el mensaje')
      // Restaurar el mensaje en caso de error para que el usuario pueda intentar de nuevo
      setMessage(currentMessage)
    } finally {
      // Asegurar que los estados de carga se limpien
      setTimeout(() => {
        clearLoadingStates()
      }, 100)
    }
  }

  const handleGeneratePrompts = async () => {
    if (!contextSession?.session_id || !activeProject?.id) {
      setError('No hay sesión de contexto o proyecto activo')
      return
    }

    setIsSendingToAIs(true)
    setError(null)

    try {
      // Obtener la última interacción para conseguir la pregunta sugerida
      const lastInteraction = conversationFlow[conversationFlow.length - 1]
      const suggestedQuestion = lastInteraction?.suggested_final_question || "¿Qué recomendaciones me puedes dar basándote en este contexto?"

      console.log('🎯 Generando prompts para las IAs:', suggestedQuestion)

      // Generar los prompts usando el sistema correcto con prompt_templates.py
      const finalizeResponse = await fetch(`${config.apiUrl}/api/v1/context-chat/context-sessions/${contextSession.session_id}/generate-ai-prompts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-mock-token-12345'
        },
        body: JSON.stringify({
          session_id: contextSession.session_id,
          final_question: suggestedQuestion
        })
      })

      if (!finalizeResponse.ok) {
        throw new Error(`Error al finalizar sesión: ${finalizeResponse.status}`)
      }

      const finalizeData = await finalizeResponse.json()
      console.log('📋 Prompts generados con prompt_templates.py:', finalizeData)

      // Agregar los prompts generados al flujo conversacional
      const promptsInteraction = {
        id: Date.now() + 1,
        type: 'prompts_generated',
        user_question: suggestedQuestion,
        prompts: finalizeData.ai_prompts || {},
        context_used: finalizeData.context_used || '',
        prompt_system: finalizeData.prompt_system || 'query_service + prompt_templates',
        timestamp: new Date()
      }

      setConversationFlow(prev => [...prev, promptsInteraction])

    } catch (error) {
      console.error('Error al generar prompts:', error)
      setError(error.message || 'Error al generar prompts para las IAs')
    } finally {
      setIsSendingToAIs(false)
    }
  }

  // Nueva función que usa la pregunta del input directamente
  const handleGeneratePromptsWithQuestion = async (userQuestion) => {
    if (!contextSessionId || !activeProject?.id) {
      setError('No hay sesión de contexto o proyecto activo')
      return
    }

    setIsSendingToAIs(true)
    setError(null)
    setMessage('') // Limpiar el input después de tomar la pregunta

    try {
      console.log('🎯 Generando prompts para las IAs con pregunta del input:', userQuestion)

      // Generar los prompts usando la pregunta del input
      const finalizeResponse = await fetch(`${config.apiUrl}/api/v1/context-chat/context-sessions/${contextSessionId}/generate-ai-prompts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-mock-token-12345'
        },
        body: JSON.stringify({
          session_id: contextSessionId,
          final_question: userQuestion
        })
      })

      if (!finalizeResponse.ok) {
        throw new Error(`Error al generar prompts: ${finalizeResponse.status}`)
      }

      const finalizeData = await finalizeResponse.json()
      console.log('📋 Prompts generados con pregunta del input:', finalizeData)

      // Agregar los prompts generados al flujo conversacional
      const promptsInteraction = {
        id: Date.now() + 1,
        type: 'prompts_generated',
        user_question: userQuestion,
        prompts: finalizeData.ai_prompts || {},
        context_used: finalizeData.context_used || '',
        prompt_system: finalizeData.prompt_system || 'query_service + prompt_templates',
        timestamp: new Date()
      }

      setConversationFlow(prev => [...prev, promptsInteraction])

    } catch (error) {
      console.error('Error al generar prompts:', error)
      setError(error.message || 'Error al generar prompts para las IAs')
    } finally {
      setIsSendingToAIs(false)
    }
  }

  const handleQueryAIs = async (customQuestion = null) => {
    if (!activeProject?.id) {
      setError('No hay proyecto activo')
      return
    }

    setIsQueryingAIs(true)
    setError(null)

    try {
      let userQuestion = customQuestion
      
      if (!userQuestion) {
        // Obtener la pregunta de la última interacción de prompts generados
        const promptsInteraction = conversationFlow.find(interaction => interaction.type === 'prompts_generated')
        userQuestion = promptsInteraction?.user_question || "¿Qué recomendaciones me puedes dar basándote en este contexto?"
      }

      console.log('🤖 Consultando IAs:', userQuestion)
      console.log('🔍 Session ID:', contextSession?.session_id || 'No disponible')

      let queryResponse

      if (contextSession?.session_id) {
        // Si hay sesión de contexto, usarla
        queryResponse = await fetch(`${config.apiUrl}/api/v1/context-chat/context-sessions/${contextSession.session_id}/query-ais`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer dev-mock-token-12345'
          },
          body: JSON.stringify({
            session_id: contextSession.session_id,
            final_question: userQuestion
          })
        })
      } else {
        // Si no hay sesión de contexto, crear una temporal
        console.log('🆕 Creando sesión temporal para consulta directa')
        
        const contextResponse = await fetch(`${config.apiUrl}/api/v1/context-chat/projects/${activeProject.id}/context-chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer dev-mock-token-12345'
          },
                  body: JSON.stringify({
          user_message: userQuestion,
          session_id: null
        })
        })

        if (!contextResponse.ok) {
          throw new Error(`Error creando sesión temporal: ${contextResponse.status}`)
        }

        const contextData = await contextResponse.json()
        const tempSessionId = contextData.session_id

        queryResponse = await fetch(`${config.apiUrl}/api/v1/context-chat/context-sessions/${tempSessionId}/query-ais`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer dev-mock-token-12345'
          },
          body: JSON.stringify({
            session_id: tempSessionId,
            final_question: userQuestion
          })
        })
      }

      if (!queryResponse.ok) {
        throw new Error(`Error al consultar IAs: ${queryResponse.status}`)
      }

      const queryData = await queryResponse.json()
      console.log('🤖 Respuestas recibidas:', queryData)

      // Limpiar el input si se usó una pregunta personalizada
      if (customQuestion) {
        setMessage('')
      }

      // Agregar las respuestas al flujo conversacional
      const aiResponsesInteraction = {
        id: Date.now() + 2,
        type: 'ai_responses',
        user_question: userQuestion,
        individual_responses: queryData.individual_responses || [],
        total_processing_time_ms: queryData.total_processing_time_ms,
        successful_responses: queryData.successful_responses,
        total_responses: queryData.total_responses,
        context_used: queryData.context_used || (accumulatedContext ? 'Contexto acumulado utilizado' : 'Sin contexto previo'),
        timestamp: new Date()
      }

      setConversationFlow(prev => [...prev, aiResponsesInteraction])

    } catch (error) {
      console.error('Error al consultar IAs:', error)
      setError(error.message || 'Error al consultar las IAs')
    } finally {
      setIsQueryingAIs(false)
    }
  }



  const handleRetryAI = async (provider) => {
    if (!contextSession?.session_id) {
      setError('No hay sesión de contexto activa')
      return
    }

    setRetryingProviders(prev => ({ ...prev, [provider]: true }))
    setError(null)

    try {
      // Obtener la última interacción para conseguir la pregunta sugerida
      const lastInteraction = conversationFlow[conversationFlow.length - 1]
      const suggestedQuestion = lastInteraction?.suggested_final_question || "¿Qué recomendaciones me puedes dar basándote en este contexto?"

      console.log(`🔄 Reintentando ${provider.toUpperCase()}:`, suggestedQuestion)

      const retryResponse = await fetch(`${config.apiUrl}/api/v1/context-chat/context-sessions/${contextSession.session_id}/retry-ai/${provider}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          final_question: suggestedQuestion
        })
      })

      if (!retryResponse.ok) {
        throw new Error(`Error ${retryResponse.status}: ${retryResponse.statusText}`)
      }

      const retryData = await retryResponse.json()
      console.log(`✅ Reintento de ${provider.toUpperCase()} completado:`, retryData)

      // Actualizar la interacción existente con la nueva respuesta
      setConversationFlow(prevFlow => {
        const newFlow = [...prevFlow]
        const aiResponseIndex = newFlow.findIndex(interaction => interaction.type === 'ai_responses')
        
        if (aiResponseIndex !== -1) {
          const updatedResponses = [...newFlow[aiResponseIndex].ai_responses]
          const providerIndex = updatedResponses.findIndex(response => response.provider === provider)
          
          if (providerIndex !== -1) {
            updatedResponses[providerIndex] = retryData.response
          }
          
          newFlow[aiResponseIndex] = {
            ...newFlow[aiResponseIndex],
            ai_responses: updatedResponses
          }
        }
        
        return newFlow
      })

      console.log(`🎉 ${provider.toUpperCase()} reintentado exitosamente`)

    } catch (error) {
      console.error(`❌ Error reintentando ${provider.toUpperCase()}:`, error)
      setError(`Error reintentando ${provider.toUpperCase()}: ${error.message}`)
    } finally {
      setRetryingProviders(prev => ({ ...prev, [provider]: false }))
    }
  }

  const handleGenerateModeratorPrompt = async () => {
    if (!contextSession?.session_id) {
      setError('No hay sesión de contexto activa')
      return
    }

    setIsGeneratingModeratorPrompt(true)
    setError(null)

    try {
      const lastInteraction = conversationFlow[conversationFlow.length - 1]
      const userQuestion = lastInteraction?.user_question || "¿Qué recomendaciones me puedes dar?"

      console.log('📝 Generando prompt del moderador para sesión:', contextSession.session_id)

      const response = await fetch(`${config.apiUrl}/api/v1/context-chat/context-sessions/${contextSession.session_id}/generate-moderator-prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-mock-token-12345'
        },
        body: JSON.stringify({
          session_id: contextSession.session_id,
          final_question: userQuestion
        })
      })

      if (!response.ok) {
        throw new Error(`Error generando prompt del moderador: ${response.status}`)
      }

      const promptData = await response.json()
      console.log('📝 Prompt del moderador generado:', promptData)

      setModeratorPromptData(promptData)

      // Agregar el prompt al flujo conversacional
      const promptInteraction = {
        id: Date.now() + 100,
        type: 'moderator_prompt_generated',
        prompt_data: promptData,
        timestamp: new Date()
      }

      setConversationFlow(prev => [...prev, promptInteraction])

    } catch (error) {
      console.error('Error generando prompt del moderador:', error)
      setError(`Error generando prompt del moderador: ${error.message}`)
    } finally {
      setIsGeneratingModeratorPrompt(false)
    }
  }

  // Función handleSynthesizeResponses eliminada - ahora todo se hace automáticamente en el endpoint /execute

  // ==========================================
  // NUEVAS FUNCIONES PARA EL FLUJO "ORQUESTAR"
  // ==========================================

  const handleOrchestrate = async () => {
    // Ejecutar todo el flujo completo: generar prompt, consultar IAs y sintetizar automáticamente
    await handleGeneratePromptForOrchestration()
  }

  const handleGeneratePromptForOrchestration = async () => {
    if (!activeProject?.id || !message.trim()) {
      setError('No hay proyecto activo o mensaje vacío')
      return
    }

    setIsOrchestrating(true)
    setError(null)

    try {
      const userQuery = message.trim()
      console.log('🎯 Generando prompt para orquestación:', userQuery)

      // Si no hay contextSessionId, crear una sesión de contexto primero
      let sessionId = contextSessionId
      if (!sessionId) {
        console.log('📝 Creando sesión de contexto para el prompt...')
        const contextResponse = await fetch(`${config.apiUrl}/api/v1/context-chat/projects/${activeProject.id}/context-chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer dev-mock-token-12345'
          },
          body: JSON.stringify({
            user_message: userQuery,
            context_session_id: null
          })
        })

        if (!contextResponse.ok) {
          throw new Error(`Error creando sesión de contexto: ${contextResponse.status}`)
        }

        const contextData = await contextResponse.json()
        sessionId = contextData.session_id
        console.log('✅ Sesión de contexto creada:', sessionId)
      }

      // Llamar al nuevo endpoint de generar prompt
      const response = await fetch(`${config.apiUrl}/api/v1/context-chat/projects/${activeProject.id}/generate-prompt`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-mock-token-12345'
        },
        body: JSON.stringify({
          query: userQuery,
          context_session_id: sessionId
        })
      })

      if (!response.ok) {
        throw new Error(`Error al generar prompt: ${response.status}`)
      }

      const promptData = await response.json()
      console.log('✅ Prompt generado:', promptData)

      // Guardar el sessionId para usar en la síntesis
      setSynthesisSessionId(sessionId)
      console.log('🔄 SessionId guardado para síntesis:', sessionId)

      // Guardar el prompt generado
      setCurrentPromptId(promptData.prompt_id)
      setGeneratedPrompt(promptData)
      setMessage('') // Limpiar el input

      // Agregar el prompt generado al flujo conversacional
      const promptInteraction = {
        id: Date.now(),
        type: 'prompt_generated',
        user_query: userQuery,
        prompt_data: promptData,
        timestamp: new Date()
      }

      setConversationFlow(prev => [...prev, promptInteraction])

    } catch (error) {
      console.error('❌ Error generando prompt:', error)
      setError(error.message || 'Error al generar el prompt')
    } finally {
      setIsOrchestrating(false)
    }
  }

  const handleExecutePromptForOrchestration = async (useEditedVersion = false) => {
    if (!currentPromptId) {
      setError('No hay prompt generado para ejecutar')
      return
    }

    setIsOrchestrating(true)
    setError(null)

    try {
      console.log('🚀 Ejecutando prompt:', currentPromptId, 'usar editado:', useEditedVersion)

      // Llamar al endpoint de ejecutar prompt
      const response = await fetch(`${config.apiUrl}/api/v1/context-chat/prompts/${currentPromptId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-mock-token-12345'
        },
        body: JSON.stringify({
          prompt_id: currentPromptId,
          use_edited_version: useEditedVersion
        })
      })

      if (!response.ok) {
        throw new Error(`Error al ejecutar prompt: ${response.status}`)
      }

      const executionData = await response.json()
      console.log('✅ Prompt ejecutado:', executionData)

      // Convertir el objeto responses en array para que funcione con .map()
      const responsesArray = Object.values(executionData.responses || {})
      
      // ✅ NUEVO: Agregar síntesis del moderador al array de respuestas si existe
      if (executionData.moderator_synthesis) {
        responsesArray.push(executionData.moderator_synthesis)
      }
      
      // Agregar las respuestas al flujo conversacional
      const aiResponsesInteraction = {
        id: Date.now() + 1,
        type: 'ai_responses_from_prompt',
        prompt_id: currentPromptId,
        execution_data: executionData,
        responses: responsesArray,
        moderator_synthesis: executionData.moderator_synthesis, // ✅ NUEVO: Incluir síntesis
        successful_responses: executionData.successful_responses,
        total_responses: executionData.total_responses,
        timestamp: new Date()
      }

      setConversationFlow(prev => [...prev, aiResponsesInteraction])

      // ✅ NUEVO: Refrescar contexto acumulado si la sesión se completó
      if (executionData.session_completed && executionData.context_session_id) {
        try {
          console.log('🔄 Refrescando contexto acumulado después de completar sesión...')
          await refreshSessionContext(executionData.context_session_id)
          
          // ✅ NUEVO: Recargar todas las sesiones para actualizar el sidebar
          if (activeProject?.id) {
            console.log('🔄 Recargando todas las sesiones de contexto...')
            await loadProjectSessionsSummary(activeProject.id)
          }
        } catch (error) {
          console.error('❌ Error refrescando contexto:', error)
        }
      }

      // Estado de orquestación ya no es necesario - todo se hace automáticamente

    } catch (error) {
      console.error('❌ Error ejecutando prompt:', error)
      setError(error.message || 'Error al ejecutar el prompt')
    } finally {
      setIsOrchestrating(false)
    }
  }

  const handleEditPrompt = async (promptId, originalPrompt) => {
    console.log('✏️ Iniciando edición de prompt:', { promptId, originalPrompt: originalPrompt?.substring(0, 100) + '...' })
    if (!promptId) {
      setError('No se encontró el ID del prompt para editar')
      return
    }
    if (!originalPrompt) {
      setError('No se encontró el texto del prompt para editar')
      return
    }
    setEditingPromptId(promptId)
    setEditedPromptText(originalPrompt)
    setIsEditingPrompt(true)
  }

  const handleSaveEditedPrompt = async () => {
    if (!editingPromptId || !editedPromptText?.trim()) {
      setError('No hay texto para guardar')
      return
    }

    setIsOrchestrating(true)
    setError(null)

    try {
      console.log('💾 Guardando prompt editado:', editingPromptId)

      const response = await fetch(`${config.apiUrl}/api/v1/context-chat/prompts/${editingPromptId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-mock-token-12345'
        },
        body: JSON.stringify({
          edited_prompt: editedPromptText?.trim() || ''
        })
      })

      if (!response.ok) {
        throw new Error(`Error al guardar prompt editado: ${response.status}`)
      }

      const updatedPrompt = await response.json()
      console.log('✅ Prompt editado guardado:', updatedPrompt)

      // Actualizar el prompt en el flujo conversacional
      setConversationFlow(prev => {
        const updated = prev.map(interaction => {
          if (interaction.type === 'prompt_generated' && interaction.prompt_data?.prompt_id === editingPromptId) {
            console.log('🔄 Actualizando prompt:', interaction.id)
            return {
              ...interaction,
              prompt_data: {
                ...interaction.prompt_data,
                generated_prompt: editedPromptText?.trim() || '', // Actualizar el prompt directamente
                status: 'edited'
              }
            }
          }
          return interaction
        })
        console.log('🔄 Prompt actualizado en el flujo')
        return updated
      })

      // Cerrar el editor
      setIsEditingPrompt(false)
      setEditingPromptId(null)
      setEditedPromptText('')

    } catch (error) {
      console.error('❌ Error guardando prompt editado:', error)
      setError(error.message || 'Error al guardar el prompt editado')
    } finally {
      setIsOrchestrating(false)
    }
  }

  const handleCancelEditPrompt = () => {
    setIsEditingPrompt(false)
    setEditingPromptId(null)
    setEditedPromptText('')
  }

  const handleContinueClarification = async (userResponse) => {
    try {
      await continueClarification(userResponse)
    } catch (error) {
      console.error('Error continuing clarification:', error)
      setError(error.message || 'Error en la clarificación')
    }
  }

  const handleCompleteClarification = async (refinedPrompt) => {
    try {
      await completeClarification(refinedPrompt)
    } catch (error) {
      console.error('Error completing clarification:', error)
      setError(error.message || 'Error al completar la clarificación')
    }
  }

  const handleClarificationResponse = async (response) => {
    if (response.type === 'continue') {
      await handleContinueClarification(response.userResponse)
    } else if (response.type === 'complete') {
      await handleCompleteClarification(response.refinedPrompt)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleButtonClick = (e) => {
    e.preventDefault()
    console.log('🔘 Button clicked')
    handleSendMessage()
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    if (!isRecording) {
      console.log('Iniciando grabación...')
    } else {
      console.log('Deteniendo grabación...')
    }
  }

  const hasActiveProject = !!activeProject?.id

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Chat Container */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar"
      >
        {!activeProject ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <h3 className="text-lg font-medium mb-2">Ningún proyecto seleccionado</h3>
              <p>Selecciona o crea un proyecto para comenzar a chatear</p>
            </div>
          </div>
        ) : conversationFlow.length === 0 ? (
          // Estado inicial - mensaje de bienvenida
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-6">
              <div className="flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mx-auto">
                <BrainIcon className="w-8 h-8 text-blue-600" />
              </div>
              <div>
                <h3 className="text-xl text-gray-900 font-medium mb-2">¡Hola! 👋</h3>
                <h4 className="text-lg text-gray-700 mb-3">Proyecto: {activeProject.name}</h4>
                <p className="text-gray-600 max-w-md mx-auto">
                  Comienza compartiendo información sobre tu proyecto. La IA construirá contexto 
                  inteligentemente y te sugerirá cuándo enviar a las IAs principales.
                </p>
              </div>
              <div className="text-sm text-gray-500 bg-gray-50 p-3 rounded-lg max-w-lg mx-auto">
                <p className="font-medium mb-1">💡 Ejemplos de cómo empezar:</p>
                <ul className="text-left space-y-1">
                  <li>• "Mi startup se dedica a..."</li>
                  <li>• "Tenemos un problema con..."</li>
                  <li>• "Operamos en el sector de..."</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          // Mostrar flujo de construcción de contexto
          <div className="space-y-6">
                         {conversationFlow.map((interaction, index) => (
               <div key={interaction.id || `interaction-${index}`} className="space-y-4">
                 {interaction.type === 'context_interaction' ? (
                   <>
                     {/* Mensaje del usuario */}
                     <div className="flex justify-end">
                       <div className="max-w-[80%] bg-blue-500 text-white p-3 rounded-lg">
                         <p className="text-sm">{interaction.user_message}</p>
                       </div>
                     </div>
                     
                     {/* Respuesta de la IA */}
                     <div className="flex justify-start">
                       <div className="max-w-[80%] bg-gray-100 p-4 rounded-lg space-y-3">
                         <div className="flex items-center space-x-2">
                           <BrainIcon className="w-4 h-4 text-green-600" />
                           <span className="text-xs font-medium text-green-600 uppercase">
                             {interaction.message_type === 'question' ? 'PREGUNTA' : 
                              interaction.message_type === 'information' ? 'INFORMACIÓN' : 
                              interaction.message_type === 'ready' ? 'LISTO' : interaction.message_type}
                           </span>
                           <span className="text-xs text-gray-500">
                             {interaction.context_elements_count} elementos de contexto
                           </span>
                         </div>
                         
                         <p className="text-sm text-gray-800">{interaction.ai_response}</p>
                         
                         {/* Contexto Acumulado - OCULTO: Ahora se muestra en el sidebar derecho */}
                         {/* {interaction.accumulated_context && (
                           <div className="mt-3 p-3 bg-blue-50 rounded border border-blue-200">
                             <div className="flex items-center space-x-2 mb-2">
                               <SparklesIcon className="w-4 h-4 text-blue-600" />
                               <span className="text-xs font-medium text-blue-600">CONTEXTO ACUMULADO</span>
                             </div>
                             <p className="text-xs text-blue-800">{interaction.accumulated_context}</p>
                           </div>
                         )} */}
                         
                         {/* Sugerencias */}
                         {interaction.suggestions && interaction.suggestions.length > 0 && (
                           <div className="mt-3 p-3 bg-purple-50 rounded border border-purple-200">
                             <div className="flex items-center space-x-2 mb-2">
                               <MessageSquareIcon className="w-4 h-4 text-purple-600" />
                               <span className="text-xs font-medium text-purple-600">SUGERENCIAS</span>
                             </div>
                             <ul className="text-xs text-purple-800 space-y-1">
                               {interaction.suggestions.map((suggestion, idx) => (
                                 <li key={idx} className="flex items-start space-x-1">
                                   <span>•</span>
                                   <span>{suggestion}</span>
                                 </li>
                               ))}
                             </ul>
                           </div>
                         )}
                         
                         {/* Pregunta sugerida para finalizar */}
                         {interaction.suggested_final_question && (
                           <div className="mt-3 p-3 bg-orange-50 rounded border border-orange-200">
                             <div className="flex items-center space-x-2 mb-2">
                               <ArrowRightIcon className="w-4 h-4 text-orange-600" />
                               <span className="text-xs font-medium text-orange-600">PREGUNTA SUGERIDA</span>
                             </div>
                             <p className="text-xs text-orange-800">{interaction.suggested_final_question}</p>
                           </div>
                         )}
                       </div>
                     </div>
                   </>
                 ) : interaction.type === 'prompts_generated' ? (
                   /* Renderizar prompts generados - Mostrar/ocultar basado en showGeneratedPrompts */
                   <div className="space-y-4">
                     <div className="text-center p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
                       <h3 className="text-lg font-semibold text-green-800 mb-2">✨ Prompts Generados para las IAs</h3>
                       <p className="text-sm text-green-700 mb-2">Los siguientes prompts están listos para las IAs principales:</p>
                       <p className="text-xs text-green-600 font-medium">"{interaction.user_question}"</p>
                       {!showGeneratedPrompts && (
                         <div className="mt-3">
                           <p className="text-xs text-blue-600 mb-2 italic">
                             👁️ Los prompts están listos. Usa el botón en el input para ver detalles.
                           </p>
                           <button
                             onClick={() => setShowGeneratedPrompts(true)}
                             className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded-md transition-colors"
                           >
                             Ver Prompts Aquí
                           </button>
                         </div>
                       )}
                     </div>
                     
                     {/* Info del sistema usado - Solo mostrar si showGeneratedPrompts es true */}
                     {showGeneratedPrompts && interaction.prompt_system && (
                       <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                         <div className="text-xs font-medium text-blue-800 mb-1">SISTEMA DE PROMPTS:</div>
                         <div className="text-xs text-blue-700">{interaction.prompt_system}</div>
                         {interaction.context_used && (
                           <div className="mt-2">
                             <div className="text-xs font-medium text-blue-800 mb-1">CONTEXTO UTILIZADO:</div>
                             <div className="text-xs text-blue-700 italic">{interaction.context_used}</div>
                           </div>
                         )}
                       </div>
                     )}

                     {/* Prompts para cada IA disponible - Solo mostrar si showGeneratedPrompts es true */}
                     {showGeneratedPrompts && Object.entries(interaction.prompts || {}).map(([providerKey, promptData]) => {
                       const isOpenAI = providerKey === 'openai'
                       const bgColor = isOpenAI ? 'bg-green-50 border-green-200' : 'bg-orange-50 border-orange-200'
                       const textColor = isOpenAI ? 'text-green-800' : 'text-orange-800'
                       const dotColor = isOpenAI ? 'bg-green-500' : 'bg-orange-500'
                       const lightBg = isOpenAI ? 'bg-green-100' : 'bg-orange-100'
                       
                       if (promptData.error) {
                         return (
                           <div key={providerKey} className={`${bgColor} border rounded-lg p-4 mb-4`}>
                             <div className="flex items-center space-x-2 mb-3">
                               <div className={`w-3 h-3 ${dotColor} rounded-full`}></div>
                               <span className={`font-medium ${textColor}`}>{promptData.provider}</span>
                             </div>
                             <div className="text-red-600 text-sm">⚠️ {promptData.error}</div>
                           </div>
                         )
                       }

                       return (
                         <div key={providerKey} className={`${bgColor} border rounded-lg p-4 mb-4`}>
                           <div className="flex items-center space-x-2 mb-3">
                             <div className={`w-3 h-3 ${dotColor} rounded-full`}></div>
                             <span className={`font-medium ${textColor}`}>
                               {promptData.provider} ({promptData.model})
                             </span>
                             {promptData.template_used && (
                               <span className="text-xs bg-white px-2 py-1 rounded">
                                 {promptData.template_used}
                               </span>
                             )}
                           </div>
                           
                           {/* Parámetros */}
                           {promptData.parameters && (
                             <div className={`mb-3 p-2 ${lightBg} rounded text-xs`}>
                               <span className="font-medium">Parámetros:</span> 
                               max_tokens: {promptData.parameters.max_tokens}, 
                               temperature: {promptData.parameters.temperature}
                             </div>
                           )}
                           
                           {/* System Message */}
                           {promptData.system_message && (
                             <div className="mb-4">
                               <button
                                 onClick={() => {
                                   const key = `system-${providerKey}`
                                   setExpandedPrompts(prev => ({
                                     ...prev,
                                     [key]: !prev[key]
                                   }))
                                 }}
                                 className={`w-full flex items-center justify-between text-xs font-medium ${textColor} mb-2 p-2 rounded hover:bg-gray-50`}
                               >
                                 <span>SYSTEM MESSAGE: (Click para expandir/colapsar)</span>
                                 {expandedPrompts[`system-${providerKey}`] ? 
                                   <ChevronUpIcon className="w-3 h-3" /> : 
                                   <ChevronDownIcon className="w-3 h-3" />
                                 }
                               </button>
                               {expandedPrompts[`system-${providerKey}`] && (
                                 <div className={`text-xs ${textColor} bg-white p-4 rounded border max-h-96 overflow-y-auto leading-relaxed`}>
                                   <div className="whitespace-pre-wrap">
                                     {promptData.system_message.split('**').map((part, index) => {
                                       if (index % 2 === 1) {
                                         // Texto entre ** se formatea como negrita
                                         return <strong key={index} className="font-bold text-gray-900">{part}</strong>
                                       }
                                       return part
                                     }).map((part, index) => {
                                       if (typeof part === 'string') {
                                         // Dividir por párrafos y aplicar formato
                                         return part.split('\n\n').map((paragraph, pIndex) => (
                                           <div key={`${index}-${pIndex}`} className="mb-3">
                                             {paragraph.split('\n').map((line, lIndex) => (
                                               <div key={lIndex} className={
                                                 line.trim().startsWith('###') ? 'font-semibold mt-3 mb-2 text-blue-800 text-sm' : 
                                                 line.trim().startsWith('**') && line.trim().endsWith('**') ? 'font-bold mt-2 mb-1 text-gray-900' :
                                                 line.trim().startsWith('- ') ? 'ml-6 mb-1 pl-2 border-l-2 border-gray-200' : 
                                                 line.trim() === '' ? 'mb-2' : 'mb-1'
                                               }>
                                                 {line}
                                               </div>
                                             ))}
                                           </div>
                                         ))
                                       }
                                       return part
                                     })}
                                   </div>
                                 </div>
                               )}
                             </div>
                           )}
                           
                           {/* User Prompt */}
                           {promptData.user_prompt && (
                             <div className="mb-3">
                               <button
                                 onClick={() => {
                                   const key = `user-${providerKey}`
                                   setExpandedPrompts(prev => ({
                                     ...prev,
                                     [key]: !prev[key]
                                   }))
                                 }}
                                 className={`w-full flex items-center justify-between text-xs font-medium ${textColor} mb-2 p-2 rounded hover:bg-gray-50`}
                               >
                                 <span>USER PROMPT: (Click para expandir/colapsar)</span>
                                 {expandedPrompts[`user-${providerKey}`] ? 
                                   <ChevronUpIcon className="w-3 h-3" /> : 
                                   <ChevronDownIcon className="w-3 h-3" />
                                 }
                               </button>
                               {expandedPrompts[`user-${providerKey}`] && (
                                 <div className={`text-xs ${textColor} bg-white p-4 rounded border max-h-64 overflow-y-auto leading-relaxed`}>
                                   <div className="whitespace-pre-wrap">
                                     {promptData.user_prompt.split('**').map((part, index) => {
                                       if (index % 2 === 1) {
                                         // Texto entre ** se formatea como negrita
                                         return <strong key={index} className="font-bold text-gray-900">{part}</strong>
                                       }
                                       return part
                                     }).map((part, index) => {
                                       if (typeof part === 'string') {
                                         // Dividir por párrafos y aplicar formato
                                         return part.split('\n\n').map((paragraph, pIndex) => (
                                           <div key={`${index}-${pIndex}`} className="mb-3">
                                             {paragraph.split('\n').map((line, lIndex) => (
                                               <div key={lIndex} className={
                                                 line.trim().startsWith('###') ? 'font-semibold mt-3 mb-2 text-blue-800 text-sm' : 
                                                 line.trim().startsWith('**') && line.trim().endsWith('**') ? 'font-bold mt-2 mb-1 text-gray-900' :
                                                 line.trim().startsWith('- ') ? 'ml-6 mb-1 pl-2 border-l-2 border-gray-200' : 
                                                 line.trim() === '' ? 'mb-2' : 'mb-1'
                                               }>
                                                 {line}
                                               </div>
                                             ))}
                                           </div>
                                         ))
                                       }
                                       return part
                                     })}
                                   </div>
                                 </div>
                               )}
                             </div>
                           )}
                         </div>
                       )
                     })}
                   </div>
                 ) : interaction.type === 'ai_result' ? (
                   /* Renderizar resultado de las IAs */
                   <div className="space-y-4">
                     {/* Header con la pregunta */}
                     <div className="text-center p-4 bg-gradient-to-r from-emerald-50 to-cyan-50 rounded-lg border-2 border-emerald-300">
                       <h3 className="text-lg font-semibold text-emerald-800 mb-2">🎯 Respuesta de las IAs Principales</h3>
                       <p className="text-sm text-emerald-700 font-medium">{interaction.user_question}</p>
                       <div className="mt-2 text-xs text-emerald-600">
                         Procesado en {interaction.processing_time_ms}ms • Calidad: {interaction.moderator_quality}
                       </div>
                     </div>
                     
                     {/* Síntesis Principal */}
                     <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-lg p-5">
                       <div className="flex items-center space-x-2 mb-3">
                         <BrainIcon className="w-5 h-5 text-blue-600" />
                         <span className="font-semibold text-blue-800">SÍNTESIS MODERADA</span>
                       </div>
                       <div className="text-gray-800 leading-relaxed">
                         {interaction.synthesis_text}
                       </div>
                     </div>
                     
                     {/* Meta-análisis */}
                     {(interaction.key_themes?.length > 0 || interaction.recommendations?.length > 0) && (
                       <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                         {/* Temas Clave */}
                         {interaction.key_themes?.length > 0 && (
                           <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                             <div className="flex items-center space-x-2 mb-3">
                               <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                               <span className="font-medium text-purple-800">TEMAS CLAVE</span>
                             </div>
                             <ul className="space-y-1">
                               {interaction.key_themes.map((theme, idx) => (
                                 <li key={idx} className="text-sm text-purple-700">• {theme}</li>
                               ))}
                             </ul>
                           </div>
                         )}
                         
                         {/* Recomendaciones */}
                         {interaction.recommendations?.length > 0 && (
                           <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                             <div className="flex items-center space-x-2 mb-3">
                               <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                               <span className="font-medium text-green-800">RECOMENDACIONES</span>
                             </div>
                             <ul className="space-y-1">
                               {interaction.recommendations.map((rec, idx) => (
                                 <li key={idx} className="text-sm text-green-700">• {rec}</li>
                               ))}
                             </ul>
                           </div>
                         )}
                       </div>
                     )}
                     
                     {/* Respuestas Individuales */}
                     {interaction.individual_responses?.length > 0 && (
                       <div className="space-y-3">
                         <h4 className="font-medium text-gray-800 flex items-center space-x-2">
                           <ArrowRightIcon className="w-4 h-4" />
                           <span>Respuestas Individuales de las IAs</span>
                         </h4>
                         
                         {interaction.individual_responses.map((response, idx) => (
                           <div key={idx} className={`border rounded-lg p-4 ${
                             response.provider === 'openai' ? 'bg-green-50 border-green-200' : 
                             response.provider === 'anthropic' ? 'bg-orange-50 border-orange-200' : 
                             'bg-gray-50 border-gray-200'
                           }`}>
                             <div className="flex items-center space-x-2 mb-3">
                               <div className={`w-3 h-3 rounded-full ${
                                 response.provider === 'openai' ? 'bg-green-500' : 
                                 response.provider === 'anthropic' ? 'bg-orange-500' : 
                                 'bg-gray-500'
                               }`}></div>
                               <span className={`font-medium ${
                                 response.provider === 'openai' ? 'text-green-800' : 
                                 response.provider === 'anthropic' ? 'text-orange-800' : 
                                 'text-gray-800'
                               }`}>
                                 {response.provider?.toUpperCase()} {response.model && `(${response.model})`}
                               </span>
                             </div>
                             
                             <div className={`text-sm whitespace-pre-wrap ${
                               response.provider === 'openai' ? 'text-green-800' : 
                               response.provider === 'anthropic' ? 'text-orange-800' : 
                               'text-gray-800'
                             }`}>
                               {response.content || response.response}
                             </div>
                           </div>
                         ))}
                       </div>
                     )}
                     
                     {/* Preguntas Sugeridas */}
                     {interaction.suggested_questions?.length > 0 && (
                       <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                         <div className="flex items-center space-x-2 mb-3">
                           <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                           <span className="font-medium text-yellow-800">PREGUNTAS SUGERIDAS</span>
                         </div>
                         <ul className="space-y-1">
                           {interaction.suggested_questions.map((question, idx) => (
                             <li key={idx} className="text-sm text-yellow-700">• {question}</li>
                           ))}
                         </ul>
                       </div>
                     )}
                   </div>
                 ) : interaction.type === 'ai_responses' ? (
                   /* Renderizar respuestas individuales de las IAs */
                   <div className="space-y-4">
                     <div className="text-center p-4 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg border border-blue-200">
                       <h3 className="text-lg font-semibold text-blue-800 mb-2">🤖 Respuestas de las IAs</h3>
                       <p className="text-sm text-blue-700 mb-2">
                         {interaction.successful_responses}/{interaction.total_responses} IAs respondieron exitosamente
                       </p>
                       <p className="text-xs text-blue-600 font-medium">
                         Tiempo total: {interaction.total_processing_time_ms}ms
                       </p>
                       <p className="text-xs text-blue-600 italic mt-1">
                         "{interaction.user_question}"
                       </p>
                     </div>

                     {/* Respuestas Individuales */}
                     <div className="space-y-4">
                       {interaction.individual_responses.map((response, idx) => {
                         const isOpenAI = response.provider === 'openai'
                         const isAnthropic = response.provider === 'anthropic'
                         const bgColor = isOpenAI ? 'bg-green-50 border-green-200' : 
                                        isAnthropic ? 'bg-orange-50 border-orange-200' : 
                                        'bg-gray-50 border-gray-200'
                         const textColor = isOpenAI ? 'text-green-800' : 
                                          isAnthropic ? 'text-orange-800' : 
                                          'text-gray-800'
                         const dotColor = isOpenAI ? 'bg-green-500' : 
                                         isAnthropic ? 'bg-orange-500' : 
                                         'bg-gray-500'
                         
                         return (
                           <div key={idx} className={`${bgColor} border rounded-lg p-4`}>
                             <div className="flex items-center justify-between mb-3">
                               <div className="flex items-center space-x-2">
                                 <div className={`w-3 h-3 ${dotColor} rounded-full`}></div>
                                 <span className={`font-medium ${textColor}`}>
                                   {response.provider?.toUpperCase()} {response.model && `(${response.model})`}
                                 </span>
                               </div>
                               <div className="flex items-center space-x-2 text-xs">
                                 {response.success ? (
                                   <span className="text-green-600 flex items-center">
                                     <CheckIcon className="w-3 h-3 mr-1" />
                                     {response.processing_time_ms}ms
                                   </span>
                                 ) : (
                                   <span className="text-red-600 flex items-center">
                                     <AlertCircleIcon className="w-3 h-3 mr-1" />
                                     Error
                                   </span>
                                 )}
                               </div>
                             </div>
                             
                             {response.success ? (
                               <div className={`text-sm whitespace-pre-wrap ${textColor} leading-relaxed`}>
                                 {response.content}
                               </div>
                             ) : (
                               <div className="space-y-3">
                                 <div className="text-red-600 text-sm">
                                   ⚠️ {response.error}
                                 </div>
                                 <button
                                   onClick={() => handleRetryAI(response.provider)}
                                   disabled={retryingProviders[response.provider]}
                                   className={`px-3 py-1.5 text-xs rounded-md font-medium transition-colors ${
                                     retryingProviders[response.provider]
                                       ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                       : 'bg-blue-500 hover:bg-blue-600 text-white'
                                   }`}
                                 >
                                   {retryingProviders[response.provider] ? (
                                     <>
                                       <LoaderIcon className="w-3 h-3 animate-spin inline mr-1" />
                                       Reintentando...
                                     </>
                                   ) : (
                                     '🔄 Reintentar'
                                   )}
                                 </button>
                               </div>
                             )}
                           </div>
                         )
                       })}
                     </div>
                   </div>
                 ) : interaction.type === 'prompt_generated' ? (
                   /* Renderizar prompt generado para orquestación */
                   <div className="space-y-4">
                     <div className="text-center p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
                       <h3 className="text-lg font-semibold text-purple-800 mb-2">🎯 Prompt Generado</h3>
                       <p className="text-sm text-purple-700 mb-2">
                         Prompt listo para consultar a las IAs
                       </p>
                       <p className="text-xs text-purple-600 italic">
                         "{interaction.user_query}"
                       </p>
                     </div>

                     {/* Vista previa del prompt */}
                     <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                       <div className="flex items-center justify-between mb-3">
                         <h4 className="font-medium text-gray-800">Prompt Generado</h4>
                         <button
                           onClick={() => setExpandedPrompts(prev => ({
                             ...prev,
                             [`prompt-${interaction.id}`]: !prev[`prompt-${interaction.id}`]
                           }))}
                           className="text-blue-600 hover:text-blue-800 text-sm flex items-center space-x-1"
                         >
                           {expandedPrompts[`prompt-${interaction.id}`] ? (
                             <>
                               <ChevronUpIcon className="w-4 h-4" />
                               <span>Contraer</span>
                             </>
                           ) : (
                             <>
                               <ChevronDownIcon className="w-4 h-4" />
                               <span>Ver Completo</span>
                             </>
                           )}
                         </button>
                       </div>
                       
                       <div className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-white p-3 rounded border">
                         {expandedPrompts[`prompt-${interaction.id}`] 
                           ? interaction.prompt_data?.generated_prompt 
                           : (interaction.prompt_data?.generated_prompt?.substring(0, 200) + '...')
                         }
                       </div>

                       {/* Metadatos del prompt */}
                       <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-600">
                         <div className="grid grid-cols-2 gap-4">
                           <div>
                             <span className="font-medium">ID del Prompt:</span>
                             <br />
                             {interaction.prompt_data?.prompt_id}
                           </div>
                           <div>
                             <span className="font-medium">Estado:</span>
                             <br />
                             <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                               interaction.prompt_data?.status === 'edited' 
                                 ? 'bg-blue-100 text-blue-800' 
                                 : 'bg-gray-100 text-gray-800'
                             }`}>
                               {interaction.prompt_data?.status === 'edited' ? '✏️ Editado' : (interaction.prompt_data?.status || 'draft')}
                             </span>
                           </div>
                         </div>
                       </div>
                     </div>

                     {/* Botones de acción */}
                     <div className="flex space-x-3">
                       <button
                         onClick={() => {
                           setCurrentPromptId(interaction.prompt_data?.prompt_id)
                           setGeneratedPrompt(interaction.prompt_data)
                           handleExecutePromptForOrchestration(interaction.prompt_data?.status === 'edited')
                         }}
                         disabled={isOrchestrating}
                         className={`flex-1 px-4 py-2 rounded-lg flex items-center justify-center ${
                           isOrchestrating
                             ? 'bg-gray-300 cursor-not-allowed'
                             : 'bg-green-600 hover:bg-green-700'
                         } text-white font-medium transition-colors`}
                       >
                         {isOrchestrating ? (
                           <LoaderIcon className="w-4 h-4 animate-spin mr-2" />
                         ) : (
                           <span className="mr-2">✅</span>
                         )}
                         Ejecutar Prompt{interaction.prompt_data?.status === 'edited' ? ' (Editado)' : ''}
                       </button>
                       
                       <button
                         onClick={() => handleEditPrompt(interaction.prompt_data?.prompt_id, interaction.prompt_data?.generated_prompt)}
                         disabled={isOrchestrating}
                         className="flex-1 px-4 py-2 rounded-lg flex items-center justify-center bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium transition-colors"
                       >
                         <span className="mr-2">✏️</span>
                         Modificar Prompt
                       </button>
                     </div>
                   </div>
                 ) : interaction.type === 'ai_responses_from_prompt' ? (
                   /* Renderizar respuestas de IAs desde prompt */
                   <div className="space-y-4">
                     <div className="text-center p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
                       <h3 className="text-lg font-semibold text-green-800 mb-2">
                         🤖 Respuestas de las IAs {interaction.moderator_synthesis && interaction.moderator_synthesis.success && '+ 🔬 Síntesis del Moderador'}
                       </h3>
                       <p className="text-sm text-green-700 mb-2">
                         {interaction.successful_responses}/{interaction.total_responses} IAs respondieron exitosamente
                         {interaction.moderator_synthesis && interaction.moderator_synthesis.success && ' • Síntesis completada'}
                       </p>
                       <p className="text-xs text-green-600 font-medium">
                         Prompt ID: {interaction.prompt_id}
                       </p>
                     </div>

                     {/* Respuestas Individuales con Acordeón */}
                     <div className="space-y-3">
                       {interaction.responses?.map((response, idx) => {
                         const isOpenAI = response.provider === 'openai'
                         const isAnthropic = response.provider === 'anthropic'
                         const isModerator = response.provider === 'moderator'
                         const bgColor = isOpenAI ? 'bg-green-50 border-green-200' : 
                                        isAnthropic ? 'bg-orange-50 border-orange-200' : 
                                        isModerator ? 'bg-purple-50 border-purple-200' :
                                        'bg-gray-50 border-gray-200'
                         const textColor = isOpenAI ? 'text-green-800' : 
                                          isAnthropic ? 'text-orange-800' : 
                                          isModerator ? 'text-purple-800' :
                                          'text-gray-800'
                         const dotColor = isOpenAI ? 'bg-green-500' : 
                                         isAnthropic ? 'bg-orange-500' : 
                                         isModerator ? 'bg-purple-500' :
                                         'bg-gray-500'
                         const accordionKey = `response-${interaction.id}-${idx}`
                         
                         return (
                           <div key={idx} className={`${bgColor} border rounded-lg overflow-hidden`}>
                             {/* Header del Acordeón */}
                             <button
                               onClick={() => {
                                 setExpandedPrompts(prev => ({
                                   ...prev,
                                   [accordionKey]: !prev[accordionKey]
                                 }))
                               }}
                               className="w-full p-4 flex items-center justify-between hover:bg-opacity-80 transition-colors"
                             >
                               <div className="flex items-center space-x-3">
                                 <div className={`w-3 h-3 ${dotColor} rounded-full`}></div>
                                 <span className={`font-medium ${textColor}`}>
                                   {isModerator ? 'MODERADOR' : response.provider?.toUpperCase()} {response.model && `(${response.model})`}
                                 </span>
                                 <div className="flex items-center space-x-2 text-xs">
                                   {response.success ? (
                                     <span className="text-green-600 flex items-center">
                                       <CheckIcon className="w-3 h-3 mr-1" />
                                       {response.processing_time_ms}ms
                                     </span>
                                   ) : (
                                     <span className="text-red-600 flex items-center">
                                       <AlertCircleIcon className="w-3 h-3 mr-1" />
                                       Error
                                     </span>
                                   )}
                                 </div>
                               </div>
                               
                               <div className="flex items-center space-x-2">
                                 {/* Preview del contenido */}
                                 {response.success && !expandedPrompts[accordionKey] && (
                                   <span className={`text-xs ${textColor} opacity-70 max-w-xs truncate`}>
                                     {response.content?.substring(0, 80)}...
                                   </span>
                                 )}
                                 <div className={`transform transition-transform ${expandedPrompts[accordionKey] ? 'rotate-180' : ''}`}>
                                   ▼
                                 </div>
                               </div>
                             </button>
                             
                             {/* Contenido del Acordeón */}
                             {expandedPrompts[accordionKey] && (
                               <div className="px-4 pb-4 border-t border-opacity-30">
                                 {response.success ? (
                                   isModerator ? (
                                     /* Renderizado especial para síntesis del moderador */
                                     <div className="mt-3 space-y-4">
                                       {/* Síntesis principal */}
                                       <div className="bg-white rounded-lg border border-gray-200 p-4">
                                         <h5 className="font-semibold text-purple-800 mb-3">📋 Síntesis</h5>
                                         <div className={`text-sm whitespace-pre-wrap ${textColor} leading-relaxed`}>
                                           {response.content}
                                         </div>
                                       </div>
                                       
                                       {/* Información adicional */}
                                       <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                                         {response.quality && (
                                           <div className="bg-purple-100 rounded p-2">
                                             <span className="font-medium text-purple-800">Calidad:</span>
                                             <span className="text-purple-700 ml-2">{response.quality}</span>
                                           </div>
                                         )}
                                         {response.responses_synthesized && (
                                           <div className="bg-purple-100 rounded p-2">
                                             <span className="font-medium text-purple-800">Respuestas analizadas:</span>
                                             <span className="text-purple-700 ml-2">{response.responses_synthesized}</span>
                                           </div>
                                         )}
                                       </div>
                                       
                                       {/* Temas clave */}
                                       {response.key_themes && response.key_themes.length > 0 && (
                                         <div className="bg-blue-50 rounded-lg border border-blue-200 p-3">
                                           <h6 className="font-medium text-blue-800 mb-2">🔑 Temas Clave</h6>
                                           <ul className="space-y-1">
                                             {response.key_themes.map((theme, themeIdx) => (
                                               <li key={themeIdx} className="text-sm text-blue-700 flex items-start">
                                                 <span className="text-blue-500 mr-2">•</span>
                                                 {theme}
                                               </li>
                                             ))}
                                           </ul>
                                         </div>
                                       )}
                                       
                                       {/* Recomendaciones */}
                                       {response.recommendations && response.recommendations.length > 0 && (
                                         <div className="bg-green-50 rounded-lg border border-green-200 p-3">
                                           <h6 className="font-medium text-green-800 mb-2">💡 Recomendaciones</h6>
                                           <ul className="space-y-1">
                                             {response.recommendations.map((rec, recIdx) => (
                                               <li key={recIdx} className="text-sm text-green-700 flex items-start">
                                                 <span className="text-green-500 mr-2">•</span>
                                                 {rec}
                                               </li>
                                             ))}
                                           </ul>
                                         </div>
                                       )}
                                     </div>
                                   ) : (
                                     /* Renderizado normal para IAs */
                                     <div className={`text-sm whitespace-pre-wrap ${textColor} leading-relaxed mt-3`}>
                                       {response.content}
                                     </div>
                                   )
                                 ) : (
                                   <div className="text-red-600 text-sm mt-3">
                                     ⚠️ {response.error}
                                   </div>
                                 )}
                               </div>
                             )}
                           </div>
                         )
                       })}
                     </div>
                   </div>
                 ) : interaction.type === 'synthesis_completed' ? (
                   /* Renderizar síntesis del moderador */
                   <div className="space-y-6">
                     <div className="text-center p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                       <h3 className="text-lg font-semibold text-purple-800 mb-2">🔬 Síntesis del Moderador Completada</h3>
                       <p className="text-sm text-purple-700 mb-2">
                         Análisis de {interaction.synthesis_data?.metadata?.responses_analyzed || 0} respuestas
                       </p>
                       <p className="text-xs text-purple-600 font-medium">
                         Tiempo de síntesis: {interaction.synthesis_data?.metadata?.synthesis_time_ms || 0}ms
                       </p>
                     </div>

                     {/* Síntesis principal */}
                     <div className="bg-white rounded-lg border border-gray-200 p-6">
                       <h4 className="text-lg font-semibold text-gray-800 mb-4">📋 Síntesis Principal</h4>
                       <div className="prose prose-sm max-w-none text-gray-700">
                         {interaction.synthesis_data?.synthesis?.text?.split('\n').map((paragraph, idx) => (
                           paragraph.trim() && (
                             <p key={idx} className="mb-3">{paragraph}</p>
                           )
                         ))}
                       </div>
                     </div>

                     {/* Análisis estructurado */}
                     <div className="grid md:grid-cols-2 gap-4">
                       {/* Temas clave */}
                       {interaction.synthesis_data?.synthesis?.key_themes?.length > 0 && (
                         <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
                           <h5 className="font-semibold text-blue-800 mb-3 flex items-center">
                             <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                             Temas Clave
                           </h5>
                           <ul className="space-y-2">
                             {interaction.synthesis_data.synthesis.key_themes.map((theme, idx) => (
                               <li key={idx} className="text-sm text-blue-700 flex items-start">
                                 <span className="text-blue-500 mr-2">•</span>
                                 {theme}
                               </li>
                             ))}
                           </ul>
                         </div>
                       )}

                       {/* Áreas de consenso */}
                       {interaction.synthesis_data?.synthesis?.consensus_areas?.length > 0 && (
                         <div className="bg-green-50 rounded-lg border border-green-200 p-4">
                           <h5 className="font-semibold text-green-800 mb-3 flex items-center">
                             <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                             Áreas de Consenso
                           </h5>
                           <ul className="space-y-2">
                             {interaction.synthesis_data.synthesis.consensus_areas.map((area, idx) => (
                               <li key={idx} className="text-sm text-green-700 flex items-start">
                                 <span className="text-green-500 mr-2">•</span>
                                 {area}
                               </li>
                             ))}
                           </ul>
                         </div>
                       )}

                         {/* Contradicciones */}
                         {interaction.synthesis_data.synthesis.contradictions?.length > 0 && (
                           <div className="bg-amber-50 rounded-lg border border-amber-200 p-4">
                             <h5 className="font-semibold text-amber-800 mb-3 flex items-center">
                               <span className="w-2 h-2 bg-amber-500 rounded-full mr-2"></span>
                               Contradicciones
                             </h5>
                             <ul className="space-y-2">
                               {interaction.synthesis_data.synthesis.contradictions.map((contradiction, idx) => (
                                 <li key={idx} className="text-sm text-amber-700 flex items-start">
                                   <span className="text-amber-500 mr-2">•</span>
                                   {contradiction}
                                 </li>
                               ))}
                             </ul>
                           </div>
                         )}

                         {/* Recomendaciones */}
                         {interaction.synthesis_data.synthesis.recommendations?.length > 0 && (
                           <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
                             <h5 className="font-semibold text-blue-800 mb-3 flex items-center">
                               <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                               Recomendaciones
                             </h5>
                             <ul className="space-y-2">
                               {interaction.synthesis_data.synthesis.recommendations.map((recommendation, idx) => (
                                 <li key={idx} className="text-sm text-blue-700 flex items-start">
                                   <span className="text-blue-500 mr-2">•</span>
                                   {recommendation}
                                 </li>
                               ))}
                             </ul>
                           </div>
                         )}

                         {/* Preguntas sugeridas */}
                         {interaction.synthesis_data?.synthesis?.suggested_questions?.length > 0 && (
                           <div className="bg-purple-50 rounded-lg border border-purple-200 p-4">
                             <h5 className="font-semibold text-purple-800 mb-3 flex items-center">
                               <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                               Preguntas Sugeridas
                             </h5>
                             <ul className="space-y-2">
                               {interaction.synthesis_data.synthesis.suggested_questions.map((question, idx) => (
                                 <li key={idx} className="text-sm text-purple-700 flex items-start">
                                   <span className="text-purple-500 mr-2">?</span>
                                   {question}
                                 </li>
                               ))}
                             </ul>
                           </div>
                         )}

                         {/* Conexiones */}
                         {interaction.synthesis_data?.synthesis?.connections?.length > 0 && (
                           <div className="bg-indigo-50 rounded-lg border border-indigo-200 p-4">
                             <h5 className="font-semibold text-indigo-800 mb-3 flex items-center">
                               <span className="w-2 h-2 bg-indigo-500 rounded-full mr-2"></span>
                               Conexiones
                             </h5>
                             <ul className="space-y-2">
                               {interaction.synthesis_data.synthesis.connections.map((connection, idx) => (
                                 <li key={idx} className="text-sm text-indigo-700 flex items-start">
                                   <span className="text-indigo-500 mr-2">↔</span>
                                   {connection}
                                 </li>
                               ))}
                             </ul>
                           </div>
                         )}

                         {/* Áreas de investigación */}
                         {interaction.synthesis_data?.synthesis?.research_areas?.length > 0 && (
                           <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                             <h5 className="font-semibold text-gray-800 mb-3 flex items-center">
                               <span className="w-2 h-2 bg-gray-500 rounded-full mr-2"></span>
                               Áreas de Investigación
                             </h5>
                             <ul className="space-y-2">
                               {interaction.synthesis_data.synthesis.research_areas.map((area, idx) => (
                                 <li key={idx} className="text-sm text-gray-700 flex items-start">
                                   <span className="text-gray-500 mr-2">🔬</span>
                                   {area}
                                 </li>
                               ))}
                             </ul>
                           </div>
                         )}
                       </div>

                     {/* Metadatos */}
                     <div className="bg-gray-50 rounded-lg p-4 text-xs text-gray-600">
                       <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                         <div>
                           <span className="font-medium">Respuestas analizadas:</span>
                           <br />
                           {interaction.synthesis_data?.metadata?.responses_analyzed || 0}
                         </div>
                         <div>
                           <span className="font-medium">Proveedores:</span>
                           <br />
                           {interaction.synthesis_data?.metadata?.providers_included?.join(', ') || 'N/A'}
                         </div>
                         <div>
                           <span className="font-medium">Calidad de síntesis:</span>
                           <br />
                           {interaction.synthesis_data?.synthesis?.quality || 'N/A'}
                         </div>
                         <div>
                           <span className="font-medium">Tiempo de síntesis:</span>
                           <br />
                           {interaction.synthesis_data?.metadata?.synthesis_time_ms || 0}ms
                         </div>
                         <div>
                           <span className="font-medium">Fallback usado:</span>
                           <br />
                           {interaction.synthesis_data?.metadata?.fallback_used ? 'Sí' : 'No'}
                         </div>
                         <div>
                           <span className="font-medium">Calidad meta-análisis:</span>
                           <br />
                           {interaction.synthesis_data?.metadata?.meta_analysis_quality || 'N/A'}
                         </div>
                       </div>
                     </div>
                   </div>
                 ) : interaction.type === 'moderator_prompt_generated' ? (
                   /* Renderizar prompt del moderador */
                   <div className="space-y-4">
                     <div className="text-center p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                       <h3 className="text-lg font-semibold text-purple-800 mb-2">📝 Prompt del Moderador Generado</h3>
                       <p className="text-sm text-purple-700 mb-2">
                         Prompt listo para síntesis de {interaction.prompt_data?.responses_count || 0} respuestas
                       </p>
                       <p className="text-xs text-purple-600 font-medium">
                         Longitud: {interaction.prompt_data?.prompt_length || 0} caracteres
                       </p>
                       <p className="text-xs text-purple-600 italic mt-1">
                         Proveedores incluidos: {interaction.prompt_data?.providers_included?.join(', ') || 'N/A'}
                       </p>
                     </div>

                     {/* Vista previa del prompt */}
                     <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                       <div className="flex items-center justify-between mb-3">
                         <h4 className="font-medium text-gray-800">Vista Previa del Prompt</h4>
                         <button
                           onClick={() => setExpandedPrompts(prev => ({
                             ...prev,
                             [`moderator-${interaction.id}`]: !prev[`moderator-${interaction.id}`]
                           }))}
                           className="text-blue-600 hover:text-blue-800 text-sm flex items-center space-x-1"
                         >
                           {expandedPrompts[`moderator-${interaction.id}`] ? (
                             <>
                               <ChevronUpIcon className="w-4 h-4" />
                               <span>Contraer</span>
                             </>
                           ) : (
                             <>
                               <ChevronDownIcon className="w-4 h-4" />
                               <span>Ver Completo</span>
                             </>
                           )}
                         </button>
                       </div>
                       
                       <div className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-white p-3 rounded border">
                         {expandedPrompts[`moderator-${interaction.id}`] 
                           ? interaction.prompt_data?.moderator_prompt 
                           : interaction.prompt_data?.prompt_preview
                         }
                       </div>
                     </div>
                   </div>
                 ) : null}
               </div>
             ))}
             

           </div>
        )}
      </div>

      {/* Modal de Edición de Prompt */}
      {isEditingPrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">✏️ Editar Prompt</h3>
              <p className="text-sm text-gray-600 mt-1">
                Modifica el prompt antes de enviarlo a las IAs. Los cambios se guardarán como versión editada.
              </p>
            </div>
            
            <div className="p-6 max-h-[60vh] overflow-y-auto">
              <textarea
                value={editedPromptText || ''}
                onChange={(e) => setEditedPromptText(e.target.value)}
                placeholder="Escribe tu prompt aquí..."
                className="w-full h-96 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
                style={{ fontFamily: 'monospace', fontSize: '14px', lineHeight: '1.5' }}
              />
              <div className="mt-2 text-xs text-gray-500">
                Longitud: {editedPromptText?.length || 0} caracteres
              </div>
            </div>
            
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={handleCancelEditPrompt}
                disabled={isOrchestrating}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-300 rounded-lg font-medium transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveEditedPrompt}
                disabled={isOrchestrating || !editedPromptText?.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors flex items-center"
              >
                {isOrchestrating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Guardando...
                  </>
                ) : (
                  <>
                    <span className="mr-2">💾</span>
                    Guardar Cambios
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

            {/* Estado de la Conversación */}
      <ConversationStatePanel />

      {/* Input Form - Solo mostrar si hay un proyecto activo */}
      {activeProject && (
        <form onSubmit={handleSendMessage} className="p-4 border-t bg-white">
          {/* Error Message */}
          {error && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <AlertCircleIcon className="w-4 h-4 text-red-500 flex-shrink-0" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
          
          <div className="flex space-x-3">
            <div className="flex-1">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Escribe tu mensaje aquí..."
                className="w-full text-gray-900 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="1"
                style={{
                  minHeight: '44px',
                  maxHeight: '120px',
                  overflow: 'auto'
                }}
                onInput={(e) => {
                  e.target.style.height = 'auto'
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
                }}
                disabled={isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs || isOrchestrating}
              />
            </div>
            
            {/* Botón "Orquestar" - Ejecuta todo el flujo automáticamente */}
            {message.trim() && (
              <button
                type="button"
                onClick={handleOrchestrate}
                disabled={isOrchestrating || isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs}
                className={`px-3 py-2 rounded-lg flex items-center justify-center min-w-[100px] h-[44px] ${
                  isOrchestrating || isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600'
                } text-white transition-colors text-sm font-medium`}
                title="Generar prompt, consultar IAs y sintetizar automáticamente"
              >
                {isOrchestrating ? (
                  <LoaderIcon className="w-4 h-4 animate-spin mr-1" />
                ) : (
                  <>
                    <span className="mr-1">🎯</span>
                    <span>Orquestar</span>
                  </>
                )}
              </button>
            )}
            
            <button
              type="button"
              onClick={handleButtonClick}
              disabled={!message.trim() || isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs || isOrchestrating}
              className={`px-4 py-2 rounded-lg flex items-center justify-center min-w-[44px] h-[44px] ${
                !message.trim() || isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs || isOrchestrating
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600'
              } text-white transition-colors`}
            >
              {isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs || isOrchestrating ? (
                <LoaderIcon className="w-5 h-5 animate-spin" />
              ) : (
                <SendIcon className="w-5 h-5" />
              )}
            </button>
          </div>
          
          <div className="mt-2 text-xs text-gray-500 flex items-center justify-between">
            <span>Presiona Enter para enviar, Shift+Enter para nueva línea</span>
            {(isQuerying || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs || isOrchestrating) && (
              <span className="text-blue-600 flex items-center">
                <LoaderIcon className="w-3 h-3 animate-spin mr-1" />
                {isOrchestrating ? 'Orquestando...' : 'Procesando...'}
              </span>
            )}
          </div>
        </form>
      )}

      {/* Diálogo de Clarificación */}
      {clarificationNeeded && (
        <ClarificationDialog
          questions={clarificationQuestions}
          onSubmit={handleClarificationResponse}
          onCancel={cancelClarification}
        />
      )}
    </div>
  )
}

export default CenterColumn 