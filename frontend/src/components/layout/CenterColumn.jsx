import { useState, useRef, useEffect } from 'react'
import { MicIcon, SendIcon, LoaderIcon, AlertCircleIcon, MessageSquareIcon, BrainIcon, SparklesIcon, ArrowRightIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'
import ConversationFlow from '../ui/ConversationFlow'
import AIResponseCard from '../ui/AIResponseCard'
import ClarificationDialog from '../ui/ClarificationDialog'
import ConversationStatePanel from '../ui/ConversationStatePanel'

const CenterColumn = ({ activeProject }) => {
  const [message, setMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSendingToAIs, setIsSendingToAIs] = useState(false)
  const [contextSession, setContextSession] = useState(null)
  const [conversationFlow, setConversationFlow] = useState([])
  const [finalPrompts, setFinalPrompts] = useState(null)
  const chatContainerRef = useRef(null)

  const {
    conversations,
    activeConversation,
    isQuerying,
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
    isContextBuilding,
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
    setFinalPrompts(null)
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

  const handleSendToAIs = async () => {
    if (!contextSession?.session_id) {
      setError('No hay sesión de contexto activa')
      return
    }

    setIsSendingToAIs(true)
    setError(null)

    try {
      // Obtener la última interacción para conseguir la pregunta sugerida
      const lastInteraction = conversationFlow[conversationFlow.length - 1]
      const suggestedQuestion = lastInteraction?.suggested_final_question || "¿Qué recomendaciones me puedes dar basándote en este contexto?"

      // Finalizar la sesión de contexto
      const finalizeResponse = await fetch(`http://localhost:8000/api/v1/context-chat/context-sessions/${contextSession.session_id}/finalize`, {
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

      // Generar los prompts reales usando el servicio del backend
      const promptsResponse = await fetch(`http://localhost:8000/api/v1/context-chat/context-sessions/${contextSession.session_id}/generate-ai-prompts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-mock-token-12345'
        },
        body: JSON.stringify({
          session_id: contextSession.session_id,
          final_question: finalizeData.final_question
        })
      })

      if (!promptsResponse.ok) {
        throw new Error(`Error al generar prompts: ${promptsResponse.status}`)
      }

      const promptsData = await promptsResponse.json()

      // Agregar los prompts reales al flujo conversacional
      const promptsInteraction = {
        id: Date.now() + 1,
        type: 'final_prompts',
        prompts: promptsData.ai_prompts,
        finalized_context: finalizeData.accumulated_context,
        final_question: finalizeData.final_question,
        timestamp: new Date()
      }

      setConversationFlow(prev => [...prev, promptsInteraction])
      setFinalPrompts(promptsData.ai_prompts)

    } catch (error) {
      console.error('Error al enviar a las IAs:', error)
      setError(error.message || 'Error al enviar a las IAs')
    } finally {
      setIsSendingToAIs(false)
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
                 ) : interaction.type === 'final_prompts' ? (
                   /* Renderizar prompts finales */
                   <div className="space-y-4">
                     <div className="text-center p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200">
                       <h3 className="text-lg font-semibold text-green-800 mb-2">🎯 Contexto Finalizado y Enviado a las IAs</h3>
                       <p className="text-sm text-green-700">Los siguientes prompts se han generado para las IAs principales:</p>
                     </div>
                     
                     {/* Prompts para cada IA disponible */}
                     {interaction.prompts.openai && (
                       <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                         <div className="flex items-center space-x-2 mb-3">
                           <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                           <span className="font-medium text-green-800">{interaction.prompts.openai.provider} ({interaction.prompts.openai.model})</span>
                         </div>
                         
                         {/* Parámetros */}
                         <div className="mb-3 p-2 bg-green-100 rounded text-xs">
                           <span className="font-medium">Parámetros:</span> 
                           max_tokens: {interaction.prompts.openai.parameters.max_tokens}, 
                           temperature: {interaction.prompts.openai.parameters.temperature}
                         </div>
                         
                         {/* System Message */}
                         <div className="mb-3">
                           <div className="text-xs font-medium text-green-800 mb-1">SYSTEM MESSAGE:</div>
                           <div className="text-xs text-green-700 bg-white p-2 rounded border">
                             {interaction.prompts.openai.system_message}
                           </div>
                         </div>
                         
                         {/* Prompt principal */}
                         <div className="mb-3">
                           <div className="text-xs font-medium text-green-800 mb-1">USER PROMPT:</div>
                           <pre className="text-xs text-green-700 whitespace-pre-wrap bg-white p-3 rounded border max-h-40 overflow-y-auto">
                             {interaction.prompts.openai.user_prompt}
                           </pre>
                         </div>
                       </div>
                     )}
                     
                     {interaction.prompts.anthropic && (
                       <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                         <div className="flex items-center space-x-2 mb-3">
                           <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                           <span className="font-medium text-orange-800">{interaction.prompts.anthropic.provider} ({interaction.prompts.anthropic.model})</span>
                         </div>
                         
                         {/* Parámetros */}
                         <div className="mb-3 p-2 bg-orange-100 rounded text-xs">
                           <span className="font-medium">Parámetros:</span> 
                           max_tokens: {interaction.prompts.anthropic.parameters.max_tokens}, 
                           temperature: {interaction.prompts.anthropic.parameters.temperature}
                         </div>
                         
                         {/* System Message */}
                         <div className="mb-3">
                           <div className="text-xs font-medium text-orange-800 mb-1">SYSTEM MESSAGE:</div>
                           <div className="text-xs text-orange-700 bg-white p-2 rounded border">
                             {interaction.prompts.anthropic.system_message}
                           </div>
                         </div>
                         
                         {/* Prompt principal */}
                         <div className="mb-3">
                           <div className="text-xs font-medium text-orange-800 mb-1">USER PROMPT:</div>
                           <pre className="text-xs text-orange-700 whitespace-pre-wrap bg-white p-3 rounded border max-h-40 overflow-y-auto">
                             {interaction.prompts.anthropic.user_prompt}
                           </pre>
                         </div>
                       </div>
                     )}
                   </div>
                 ) : null}
               </div>
             ))}
             
             {/* Botón "Enviar a las IAs" - siempre visible si hay contexto */}
             {conversationFlow.length > 0 && !finalPrompts && (
               <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4">
                 <button
                   onClick={handleSendToAIs}
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
                       <span>Enviando a las IAs...</span>
                     </>
                   ) : (
                     <>
                       <ArrowRightIcon className="w-5 h-5" />
                       <span>Enviar a las IAs Principales</span>
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
                disabled={isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs}
              />
            </div>
            
            <button
              type="button"
              onClick={handleButtonClick}
              disabled={!message.trim() || isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs}
              className={`px-4 py-2 rounded-lg flex items-center justify-center min-w-[44px] h-[44px] ${
                !message.trim() || isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600'
              } text-white transition-colors`}
            >
              {isQuerying || clarificationLoading || isContextBuilding || isProcessing || isSendingToAIs ? (
                <LoaderIcon className="w-5 h-5 animate-spin" />
              ) : (
                <SendIcon className="w-5 h-5" />
              )}
            </button>
          </div>
          
          <div className="mt-2 text-xs text-gray-500 flex items-center justify-between">
            <span>Presiona Enter para enviar, Shift+Enter para nueva línea</span>
            {(isQuerying || isContextBuilding || isProcessing || isSendingToAIs) && (
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