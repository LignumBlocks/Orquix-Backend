import { useState, useEffect } from 'react'
import { MicIcon, SendIcon, VolumeXIcon, LoaderIcon, AlertCircleIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'
import AIResponseCard from '../ui/AIResponseCard'
import ContextDisplay from '../ui/ContextDisplay'
import MetricsDisplay from '../ui/MetricsDisplay'
import ClarificationDialog from '../ui/ClarificationDialog'

const CenterColumn = ({ activeProject, moderatorConfig }) => {
  const [message, setMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)

  // Zustand store
  const {
    sendQuery,
    isQuerying,
    activeConversation,
    lastResponse,
    conversations,
    // Estados de clarificación
    clarificationSession,
    isClarificationActive,
    clarificationLoading,
    continueClarification,
    completeClarification,
    cancelClarification
  } = useAppStore()

  const handleSendMessage = async () => {
    if (!message.trim() || isQuerying || clarificationLoading) return

    setError(null)
    const currentMessage = message.trim()
    setMessage('') // Limpiar inmediatamente para mejor UX

    try {
      await sendQuery(currentMessage, true) // includeContext = true por defecto
    } catch (error) {
      console.error('Error sending message:', error)
      setError(error.message || 'Error al enviar el mensaje')
      setMessage(currentMessage) // Restaurar mensaje si hay error
    }
  }

  // Manejadores de clarificación
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

  const handleCancelClarification = () => {
    cancelClarification()
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // TODO: Implementar speech-to-text
    if (!isRecording) {
      console.log('Iniciando grabación...')
    } else {
      console.log('Deteniendo grabación...')
    }
  }

  // Usar conversación activa o la más reciente
  const displayConversation = activeConversation || conversations[0]
  const hasActiveProject = !!activeProject

  // Calcular tokens totales de las respuestas individuales
  const calculateTotalTokens = (responses) => {
    if (!responses) return null
    return responses.reduce((total, response) => {
      const tokens = response.usage_info?.total_tokens || 0
      return total + tokens
    }, 0)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 lg:p-6 custom-scrollbar">
        
        {/* No Project State */}
        {!hasActiveProject && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <AlertCircleIcon className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No hay proyecto activo</h3>
              <p className="text-gray-500">Selecciona o crea un proyecto para comenzar a hacer consultas.</p>
            </div>
          </div>
        )}

        {/* Active Project Content */}
        {hasActiveProject && (
          <>
            {/* Current Question */}
            {displayConversation && (
              <div className="mb-6">
                <div className="bg-blue-600 text-white px-4 py-4 lg:px-6 rounded-lg shadow-sm hover-lift smooth-transition">
                  <p className="text-base lg:text-lg font-medium">{displayConversation.question}</p>
                </div>
              </div>
            )}

            {/* PreAnalyst Loading State */}
            {clarificationLoading && (
              <div className="mb-6">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                      <LoaderIcon className="w-4 h-4 text-white animate-spin" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-medium text-gray-900">PreAnalyst</span>
                      <span className="text-xs text-purple-600">Analizando tu consulta...</span>
                    </div>
                    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <LoaderIcon className="w-4 h-4 text-purple-600 animate-spin" />
                          <p className="text-gray-600">Generando preguntas de clarificación inteligentes...</p>
                        </div>
                        <div className="text-xs text-gray-500 bg-purple-50 rounded p-2">
                          <p><strong>PreAnalyst en acción:</strong></p>
                          <p>• Interpretando la intención de tu consulta</p>
                          <p>• Identificando información faltante</p>
                          <p>• Generando preguntas de clarificación específicas</p>
                          <p className="mt-1 text-purple-600">🧠 <strong>Tiempo estimado:</strong> 5-10 segundos</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Main Orchestration Loading State */}
            {isQuerying && (
              <div className="mb-6">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <LoaderIcon className="w-4 h-4 text-white animate-spin" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-medium text-gray-900">Moderator v2.0</span>
                      <span className="text-xs text-blue-600">Procesando con {moderatorConfig.personality}...</span>
                    </div>
                    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <LoaderIcon className="w-4 h-4 text-blue-600 animate-spin" />
                          <p className="text-gray-600">Orquestando múltiples IAs y generando síntesis inteligente...</p>
                        </div>
                        <div className="text-xs text-gray-500 bg-gray-50 rounded p-2">
                          <p><strong>Proceso en curso:</strong></p>
                          <p>• Consultando OpenAI y Anthropic en paralelo</p>
                          <p>• Aplicando Context Manager inteligente</p>
                          <p>• Sintetizando con meta-análisis profesional</p>
                          <p className="mt-1 text-amber-600">⏱️ <strong>Tiempo estimado:</strong> 30-60 segundos</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Conversation Results */}
            {displayConversation && !isQuerying && (
              <div className="space-y-6">
                
                {/* Metrics Display */}
                <MetricsDisplay 
                  processingTime={displayConversation.processingTime}
                  moderatorQuality={displayConversation.moderatorQuality}
                  fallbackUsed={displayConversation.fallbackUsed}
                  aiResponsesCount={displayConversation.individualResponses?.length}
                  totalTokens={calculateTotalTokens(displayConversation.individualResponses)}
                />

                {/* Context Display */}
                {displayConversation.contextInfo && (
                  <ContextDisplay contextInfo={displayConversation.contextInfo} />
                )}

                {/* Moderator Synthesis */}
                <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                  <div className="px-4 py-4 lg:px-6 border-b border-gray-200">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white font-semibold text-sm">M</span>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-900">Síntesis del Moderador</span>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            displayConversation.moderatorQuality === 'high' ? 'bg-green-100 text-green-700' :
                            displayConversation.moderatorQuality === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {displayConversation.moderatorQuality}
                          </span>
                          <span className="text-xs text-gray-500">
                            {displayConversation.processingTime}ms
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-4 lg:p-6">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap mb-4">
                      {displayConversation.response}
                    </p>
                    
                    {/* Meta-análisis */}
                    {displayConversation.keyThemes && displayConversation.keyThemes.length > 0 && (
                      <div className="mt-6 pt-4 border-t border-gray-100">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                          
                          {/* Key Themes */}
                          {displayConversation.keyThemes.length > 0 && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">Temas Clave:</h4>
                              <div className="flex flex-wrap gap-2">
                                {displayConversation.keyThemes.map((theme, i) => (
                                  <span key={i} className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs">
                                    {theme}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Recommendations */}
                          {displayConversation.recommendations && displayConversation.recommendations.length > 0 && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-2">Recomendaciones:</h4>
                              <ul className="text-gray-600 text-sm space-y-1">
                                {displayConversation.recommendations.slice(0, 4).map((rec, i) => (
                                  <li key={i} className="flex items-start">
                                    <span className="text-blue-500 mr-2">•</span>
                                    <span>{rec}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {/* Suggested Questions */}
                          {displayConversation.suggestedQuestions && displayConversation.suggestedQuestions.length > 0 && (
                            <div className="md:col-span-2">
                              <h4 className="font-medium text-gray-900 mb-2">Preguntas Sugeridas:</h4>
                              <div className="flex flex-wrap gap-2">
                                {displayConversation.suggestedQuestions.slice(0, 3).map((question, i) => (
                                  <button 
                                    key={i}
                                    onClick={() => setMessage(question)}
                                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer"
                                  >
                                    {question}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Individual AI Responses */}
                {displayConversation.individualResponses && displayConversation.individualResponses.length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Respuestas Individuales de las IAs ({displayConversation.individualResponses.length})
                    </h3>
                    <div className="space-y-4">
                      {displayConversation.individualResponses.map((response, index) => (
                        <AIResponseCard 
                          key={`${response.ia_provider_name}-${index}`}
                          response={response} 
                          index={index + 1} 
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="mb-6">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <AlertCircleIcon className="w-5 h-5 text-red-500 flex-shrink-0" />
                    <div>
                      <p className="text-red-700 font-medium">Error al procesar consulta</p>
                      <p className="text-red-600 text-sm mt-1">{error}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Input Area */}
      {hasActiveProject && (
        <div className="border-t border-gray-200 p-3 lg:p-4 bg-white">
          <div className="flex items-end space-x-2 lg:space-x-3">
            <div className="flex-1">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  clarificationLoading 
                    ? "PreAnalyst está analizando tu consulta..." 
                    : "Escribe tu consulta para el moderador..."
                }
                className={`w-full px-4 py-3 border rounded-lg resize-none focus:ring-2 focus:border-transparent text-gray-900 placeholder-gray-500 ${
                  clarificationLoading 
                    ? 'border-purple-300 focus:ring-purple-500' 
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
                rows="3"
                disabled={isQuerying || clarificationLoading}
              />
            </div>
            
            <div className="flex lg:flex-col space-x-2 lg:space-x-0 lg:space-y-2">
              <button
                onClick={toggleRecording}
                className={`p-2 lg:p-3 rounded-lg transition-colors ${
                  isRecording 
                    ? 'bg-red-500 text-white' 
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                disabled={isQuerying || clarificationLoading}
              >
                <MicIcon className="w-4 h-4 lg:w-5 lg:h-5" />
              </button>
              
              <button
                onClick={handleSendMessage}
                disabled={!message.trim() || isQuerying || clarificationLoading}
                className={`p-2 lg:p-3 rounded-lg transition-colors ${
                  clarificationLoading 
                    ? 'bg-purple-600 text-white hover:bg-purple-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                } disabled:bg-gray-300 disabled:cursor-not-allowed`}
                title={clarificationLoading ? 'PreAnalyst analizando...' : 'Enviar consulta'}
              >
                {isQuerying || clarificationLoading ? (
                  <LoaderIcon className="w-4 h-4 lg:w-5 lg:h-5 animate-spin" />
                ) : (
                  <SendIcon className="w-4 h-4 lg:w-5 lg:h-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Diálogo de Clarificación */}
      {isClarificationActive && (
        <ClarificationDialog
          clarificationSession={clarificationSession}
          onContinue={handleContinueClarification}
          onComplete={handleCompleteClarification}
          onCancel={handleCancelClarification}
          isLoading={clarificationLoading}
        />
      )}
    </div>
  )
}

export default CenterColumn 