import { useState, useRef, useEffect } from 'react'
import { MicIcon, SendIcon, LoaderIcon, AlertCircleIcon, MessageSquareIcon, BrainIcon, SparklesIcon, ArrowRightIcon, ChevronDownIcon, ChevronUpIcon, CheckIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'
import ConversationFlow from '../ui/ConversationFlow'
import AIResponseCard from '../ui/AIResponseCard'
import ClarificationDialog from '../ui/ClarificationDialog'
import ConversationStatePanel from '../ui/ConversationStatePanel'

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
    clearLoadingStates
  } = useAppStore()

  // Limpiar estados de carga al montar el componente o cambiar proyecto
  useEffect(() => {
    clearLoadingStates()
    setError(null)
    setConversationFlow([])
    setContextSession(null)
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
      const response = await fetch(`http://localhost:8000/api/v1/context-chat/projects/${activeProject.id}/context-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-mock-token-12345'
        },
        body: JSON.stringify({
          user_message: userMessage,
          session_id: contextSession?.session_id || null
        })
      })

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      // Actualizar session si es nueva
      if (!contextSession) {
        setContextSession({ session_id: data.session_id })
      }

      // Agregar interacción al flujo conversacional
      const newInteraction = {
        id: Date.now(),
        type: 'context_interaction',
        user_message: userMessage,
        ai_response: data.ai_response,
        message_type: data.message_type,
        accumulated_context: data.accumulated_context,
        suggestions: data.suggestions || [],
        context_elements_count: data.context_elements_count,
        suggested_final_question: data.suggested_final_question,
        timestamp: new Date()
      }

      setConversationFlow(prev => [...prev, newInteraction])

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
      const finalizeResponse = await fetch(`http://localhost:8000/api/v1/context-chat/context-sessions/${contextSession.session_id}/generate-ai-prompts`, {
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

  const handleQueryAIs = async () => {
    if (!contextSession?.session_id || !activeProject?.id) {
      setError('No hay sesión de contexto o proyecto activo')
      return
    }

    setIsQueryingAIs(true)
    setError(null)

    try {
      // Obtener la pregunta de la última interacción de prompts generados
      const promptsInteraction = conversationFlow.find(interaction => interaction.type === 'prompts_generated')
      const userQuestion = promptsInteraction?.user_question || "¿Qué recomendaciones me puedes dar basándote en este contexto?"

      console.log('🤖 Consultando IAs individualmente:', userQuestion)

      // Consultar las IAs usando el nuevo endpoint específico
      const queryResponse = await fetch(`http://localhost:8000/api/v1/context-chat/context-sessions/${contextSession.session_id}/query-ais`, {
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

      if (!queryResponse.ok) {
        throw new Error(`Error al consultar IAs: ${queryResponse.status}`)
      }

      const queryData = await queryResponse.json()
      console.log('🤖 Respuestas individuales recibidas:', queryData)

      // Agregar las respuestas individuales al flujo conversacional
      const aiResponsesInteraction = {
        id: Date.now() + 2,
        type: 'ai_responses',
        user_question: queryData.user_question,
        individual_responses: queryData.individual_responses || [],
        total_processing_time_ms: queryData.total_processing_time_ms,
        successful_responses: queryData.successful_responses,
        total_responses: queryData.total_responses,
        context_used: queryData.context_used,
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

      const retryResponse = await fetch(`http://localhost:8000/api/v1/context-chat/context-sessions/${contextSession.session_id}/retry-ai/${provider}`, {
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
                         
                         {/* Contexto Acumulado */}
                         {interaction.accumulated_context && (
                           <div className="mt-3 p-3 bg-blue-50 rounded border border-blue-200">
                             <div className="flex items-center space-x-2 mb-2">
                               <SparklesIcon className="w-4 h-4 text-blue-600" />
                               <span className="text-xs font-medium text-blue-600">CONTEXTO ACUMULADO</span>
                             </div>
                             <p className="text-xs text-blue-800">{interaction.accumulated_context}</p>
                           </div>
                         )}
                         
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
                   /* Renderizar prompts generados */
                   <div className="space-y-4">
                     <div className="text-center p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
                       <h3 className="text-lg font-semibold text-green-800 mb-2">✨ Prompts Generados para las IAs</h3>
                       <p className="text-sm text-green-700 mb-2">Los siguientes prompts están listos para las IAs principales:</p>
                       <p className="text-xs text-green-600 font-medium">"{interaction.user_question}"</p>
                     </div>
                     
                     {/* Info del sistema usado */}
                     {interaction.prompt_system && (
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

                     {/* Prompts para cada IA disponible */}
                     {Object.entries(interaction.prompts || {}).map(([providerKey, promptData]) => {
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
                 ) : null}
               </div>
             ))}
             
             {/* Botón "Generar Prompts" - visible si hay contexto y no se han generado prompts */}
             {conversationFlow.length > 0 && !conversationFlow.some(interaction => interaction.type === 'prompts_generated') && (
               <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
                 <button
                   onClick={handleGeneratePrompts}
                   disabled={isSendingToAIs}
                   className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium transition-colors ${
                     isSendingToAIs
                       ? 'bg-gray-300 cursor-not-allowed'
                       : 'bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white'
                   }`}
                 >
                   {isSendingToAIs ? (
                     <>
                       <LoaderIcon className="w-5 h-5 animate-spin" />
                       <span>Generando Prompts...</span>
                     </>
                   ) : (
                     <>
                       <SparklesIcon className="w-5 h-5" />
                       <span>Generar Prompts para las IAs</span>
                     </>
                   )}
                 </button>
               </div>
             )}

             {/* Botón "Consultar a las IAs" - visible solo después de generar prompts y antes de consultar */}
             {conversationFlow.some(interaction => interaction.type === 'prompts_generated') && 
              !conversationFlow.some(interaction => interaction.type === 'ai_responses') && (
               <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
                 <button
                   onClick={handleQueryAIs}
                   disabled={isQueryingAIs}
                   className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium transition-colors ${
                     isQueryingAIs
                       ? 'bg-gray-300 cursor-not-allowed'
                       : 'bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white'
                   }`}
                 >
                   {isQueryingAIs ? (
                     <>
                       <LoaderIcon className="w-5 h-5 animate-spin" />
                       <span>Consultando IAs...</span>
                     </>
                   ) : (
                     <>
                       <BrainIcon className="w-5 h-5" />
                       <span>Consultar a las IAs</span>
                     </>
                   )}
                 </button>
               </div>
             )}
           </div>
        )}
      </div>

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
                disabled={isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs}
              />
            </div>
            
            <button
              type="button"
              onClick={handleButtonClick}
              disabled={!message.trim() || isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs}
              className={`px-4 py-2 rounded-lg flex items-center justify-center min-w-[44px] h-[44px] ${
                !message.trim() || isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600'
              } text-white transition-colors`}
            >
              {isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs ? (
                <LoaderIcon className="w-5 h-5 animate-spin" />
              ) : (
                <SendIcon className="w-5 h-5" />
              )}
            </button>
          </div>
          
          <div className="mt-2 text-xs text-gray-500 flex items-center justify-between">
            <span>Presiona Enter para enviar, Shift+Enter para nueva línea</span>
            {(isQuerying || isContextBuilding || isProcessing || isSendingToAIs || isQueryingAIs) && (
              <span className="text-blue-600 flex items-center">
                <LoaderIcon className="w-3 h-3 animate-spin mr-1" />
                Procesando...
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