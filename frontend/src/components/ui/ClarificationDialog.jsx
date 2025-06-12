import { useState, useRef, useEffect } from 'react'
import { SendIcon, MessageCircleIcon, BrainIcon, LoaderIcon, CheckCircleIcon, ChevronDownIcon } from 'lucide-react'

const ClarificationDialog = ({ 
  clarificationSession, 
  onContinue, 
  onComplete, 
  onCancel,
  isLoading = false
}) => {
  const [userResponse, setUserResponse] = useState('')
  const [showScrollHint, setShowScrollHint] = useState(false)
  const scrollContainerRef = useRef(null)

  // Verificar si hay contenido para hacer scroll
  useEffect(() => {
    const container = scrollContainerRef.current
    if (container) {
      const checkScroll = () => {
        const hasScroll = container.scrollHeight > container.clientHeight
        const isAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 10
        setShowScrollHint(hasScroll && !isAtBottom)
      }
      
      checkScroll()
      container.addEventListener('scroll', checkScroll)
      
      return () => container.removeEventListener('scroll', checkScroll)
    }
  }, [clarificationSession?.conversation_history])

  // Auto-scroll al final cuando hay nuevos mensajes
  useEffect(() => {
    const container = scrollContainerRef.current
    if (container && clarificationSession?.conversation_history?.length > 0) {
      setTimeout(() => {
        container.scrollTop = container.scrollHeight
      }, 100)
    }
  }, [clarificationSession?.conversation_history?.length])

  if (!clarificationSession) return null

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!userResponse.trim() || isLoading) return

    if (clarificationSession.is_complete) {
      onComplete(clarificationSession.final_refined_prompt)
    } else {
      onContinue(userResponse.trim())
      setUserResponse('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full h-[90vh] flex flex-col">
        
        {/* Header */}
        <div className="flex-shrink-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 lg:p-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
              <BrainIcon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-medium">PreAnalyst - Clarificación de Consulta</h3>
              <p className="text-purple-100 text-sm">
                {clarificationSession.is_complete 
                  ? '✨ Consulta refinada lista para procesar'
                  : '🤔 Necesito más información para ayudarte mejor'
                }
              </p>
            </div>
          </div>
        </div>

        {/* Conversation History */}
        <div className="flex-1 min-h-0 relative">
          <div 
            ref={scrollContainerRef}
            className="absolute inset-0 p-4 lg:p-6 overflow-y-auto"
            style={{ scrollbarWidth: 'thin', scrollbarColor: '#9333ea #f3f4f6' }}
          >
            <div className="space-y-4">
              {clarificationSession.conversation_history?.map((turn, index) => (
                <div 
                  key={index} 
                  className={`flex ${turn.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div 
                    className={`max-w-[80%] p-3 rounded-lg ${
                      turn.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {turn.role === 'assistant' && (
                        <MessageCircleIcon className="w-4 h-4 mt-1 flex-shrink-0" />
                      )}
                      <p className="text-sm whitespace-pre-wrap">{turn.content}</p>
                    </div>
                    {turn.timestamp && (
                      <p className={`text-xs mt-1 ${
                        turn.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        {new Date(turn.timestamp).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Scroll hint */}
          {showScrollHint && (
            <div className="absolute bottom-2 right-2 bg-purple-600 text-white p-1 rounded-full opacity-75 animate-bounce pointer-events-none">
              <ChevronDownIcon className="w-4 h-4" />
            </div>
          )}
        </div>

        {/* Current Status */}
        {clarificationSession.is_complete ? (
          <div className="flex-shrink-0 p-4 lg:p-6 border-t border-gray-200 bg-white">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <CheckCircleIcon className="w-5 h-5 text-green-600 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h4 className="text-green-800 font-medium mb-2">
                    ¡Consulta refinada generada!
                  </h4>
                  <div className="bg-white border border-green-200 rounded p-3 mb-3">
                    <p className="text-sm text-gray-700 font-medium">Consulta refinada:</p>
                    <p className="text-sm text-gray-800 mt-1">
                      {clarificationSession.final_refined_prompt}
                    </p>
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => onComplete(clarificationSession.final_refined_prompt)}
                      disabled={isLoading}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center space-x-2"
                    >
                      {isLoading ? (
                        <LoaderIcon className="w-4 h-4 animate-spin" />
                      ) : (
                        <SendIcon className="w-4 h-4" />
                      )}
                      <span>Enviar consulta refinada</span>
                    </button>
                    <button
                      onClick={onCancel}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-shrink-0 p-4 lg:p-6 border-t border-gray-200 bg-white">
                          {/* Indicador de scroll arriba */}
              {clarificationSession.conversation_history?.length > 2 && (
                <div className="flex items-center justify-center mb-3 text-xs text-gray-600">
                  <div className="flex items-center space-x-1">
                    <ChevronDownIcon className="w-3 h-3 rotate-180" />
                    <span>Desliza hacia arriba para ver toda la conversación</span>
                    <ChevronDownIcon className="w-3 h-3 rotate-180" />
                  </div>
                </div>
              )}
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Next Questions */}
              {clarificationSession.next_questions?.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-800 mb-3">
                    Preguntas pendientes:
                  </h4>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                    <ul className="space-y-2">
                      {clarificationSession.next_questions.map((question, index) => (
                        <li key={index} className="text-sm text-gray-800 flex items-start space-x-2">
                          <span className="text-purple-600 font-medium text-lg leading-4">•</span>
                          <span className="flex-1">{question}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Input Area */}
              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-800">
                  Tu respuesta:
                </label>
                <textarea
                  value={userResponse}
                  onChange={(e) => setUserResponse(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Proporciona la información solicitada..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none text-gray-900 placeholder-gray-500"
                  rows="3"
                  disabled={isLoading}
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={onCancel}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={!userResponse.trim() || isLoading}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isLoading ? (
                    <LoaderIcon className="w-4 h-4 animate-spin" />
                  ) : (
                    <SendIcon className="w-4 h-4" />
                  )}
                  <span>Continuar</span>
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}

export default ClarificationDialog 