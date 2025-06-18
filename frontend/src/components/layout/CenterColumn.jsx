import { useState, useRef, useEffect } from 'react'
import { MicIcon, SendIcon, LoaderIcon, AlertCircleIcon, BrainIcon, MessageSquareIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'
import ConversationFlow from '../ui/ConversationFlow'
import ConversationModeToggle from '../ui/ConversationModeToggle'
import AIResponseCard from '../ui/AIResponseCard'
import ClarificationDialog from '../ui/ClarificationDialog'
import ConversationStatePanel from '../ui/ConversationStatePanel'
import ContextBuildingFlow from '../ui/ContextBuildingFlow'

const CenterColumn = ({ activeProject }) => {
  const [message, setMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const [conversationMode, setConversationMode] = useState('auto')
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
    // Estados de construcción de contexto
    contextBuildingMode,
    contextMessages,
    accumulatedContext,
    contextSessionId,
    isContextBuilding,
    startContextBuilding,
    sendContextMessage,
    finalizeContextSession,
    cancelContextBuilding,
    clearLoadingStates
  } = useAppStore()

  // Limpiar estados de carga al montar el componente o cambiar proyecto
  useEffect(() => {
    clearLoadingStates()
    setError(null)
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
  }, [conversations, contextMessages])

  const handleSendMessage = async (e) => {
    if (e) {
      e.preventDefault()
    }
    
    console.log('🚀 handleSendMessage called:', { 
      message: message.trim(), 
      contextBuildingMode, 
      isQuerying, 
      clarificationLoading, 
      isContextBuilding,
      activeProject: activeProject?.id 
    })
    
    if (!message.trim()) {
      console.log('❌ Message is empty, returning')
      return
    }
    
    const currentMessage = message.trim()
    setMessage('')
    setError(null)

    try {
      if (contextBuildingMode) {
        // Modo construcción de contexto
        console.log('🧠 Sending context message:', currentMessage)
        await sendContextMessage(currentMessage)
      } else {
        // Modo consulta directa
        console.log('💬 Sending direct query:', currentMessage)
        await sendQuery(currentMessage, true, false, 'auto')
      }
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

  const handleStartContextBuilding = () => {
    startContextBuilding()
  }

  const handleFinalizeContext = async (finalQuestion) => {
    try {
      await finalizeContextSession(finalQuestion)
    } catch (error) {
      console.error('Error finalizing context:', error)
      setError(error.message || 'Error al finalizar el contexto')
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

  const displayConversation = activeConversation || conversations[0]
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
        ) : contextBuildingMode ? (
          // Modo construcción de contexto
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center space-x-2">
                <BrainIcon className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-blue-900">Modo Construcción de Contexto</span>
              </div>
              <button
                onClick={cancelContextBuilding}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Cancelar
              </button>
            </div>
            
            <ContextBuildingFlow
              contextMessages={contextMessages}
              accumulatedContext={accumulatedContext}
              sessionId={contextSessionId}
              onFinalize={handleFinalizeContext}
              isLoading={isContextBuilding}
            />
          </div>
        ) : conversations.length === 0 ? (
          // Estado inicial - mostrar opciones
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-6">
              <div>
                <h3 className="text-lg text-gray-900 font-medium mb-2">Proyecto: {activeProject.name}</h3>
                <p className="text-gray-600">¿Cómo quieres comenzar?</p>
              </div>
              
              <div className="flex flex-col space-y-3 max-w-md">
                <button
                  onClick={handleStartContextBuilding}
                  className="flex items-center justify-center space-x-3 p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors"
                >
                  <BrainIcon className="w-6 h-6 text-blue-600" />
                  <div className="text-left">
                    <div className="font-medium text-blue-900">Construcción de Contexto</div>
                    <div className="text-sm text-blue-700">Conversa para construir contexto antes de preguntar</div>
                  </div>
                </button>
                
                <div className="text-center text-gray-500 text-sm">
                  <span>o escribe directamente tu consulta abajo</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          // Mostrar conversaciones existentes
          conversations.map((conversation, index) => (
            <AIResponseCard
              key={conversation.id || index}
              conversation={conversation}
            />
          ))
        )}
      </div>

      {/* Estado de la Conversación */}
      <ConversationStatePanel />

      {/* Input Form - Solo mostrar si hay un proyecto activo */}
      {activeProject && (
        <form onSubmit={handleSendMessage} className="p-4 border-t">
          {/* Error Message */}
          {error && (
            <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
              <AlertCircleIcon className="w-4 h-4 text-red-500 flex-shrink-0" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
          
          <div className="flex space-x-4">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                contextBuildingMode 
                  ? "Comparte información o haz preguntas para construir contexto..."
                  : "Escribe tu consulta..."
              }
              className="text-gray-900 flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isQuerying || clarificationLoading || isContextBuilding}
            />
            
            {contextBuildingMode && !isContextBuilding && (
              <button
                type="button"
                onClick={cancelContextBuilding}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Salir
              </button>
            )}
            
            <button
              type="button"
              onClick={handleButtonClick}
              disabled={!message.trim() || isQuerying || clarificationLoading || isContextBuilding}
              className={`px-4 py-2 rounded-lg ${
                !message.trim() || isQuerying || clarificationLoading || isContextBuilding
                  ? 'bg-gray-300 cursor-not-allowed'
                  : contextBuildingMode
                  ? 'bg-blue-500 hover:bg-blue-600'
                  : 'bg-green-500 hover:bg-green-600'
              } text-white transition-colors`}
            >
              {isQuerying || clarificationLoading || isContextBuilding ? (
                <LoaderIcon className="w-5 h-5 animate-spin" />
              ) : (
                <SendIcon className="w-5 h-5" />
              )}
            </button>
          </div>
          
          {contextBuildingMode && (
            <div className="mt-2 text-xs text-blue-600">
              💡 Comparte información paso a paso. La IA te ayudará a construir el contexto antes de hacer tu pregunta final.
            </div>
          )}
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