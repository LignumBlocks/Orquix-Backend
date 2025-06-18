import { useState } from 'react'
import { MessageCircleIcon, BrainIcon, SendIcon, CheckIcon, AlertCircleIcon, EditIcon, ArrowRightIcon } from 'lucide-react'

const ContextBuildingFlow = ({ 
  contextMessages = [], 
  accumulatedContext = '', 
  sessionId, 
  onSendMessage, 
  onFinalize, 
  isLoading = false 
}) => {
  const [editingQuestion, setEditingQuestion] = useState(false)
  const [customQuestion, setCustomQuestion] = useState('')

  // Buscar si hay algún mensaje con pregunta sugerida
  const readyMessage = contextMessages.find(msg => msg.message_type === 'ready')
  const suggestedQuestion = readyMessage?.suggested_final_question || ''

  const handleFinalize = (question) => {
    const finalQuestion = question || suggestedQuestion || '¿Puedes ayudarme con esto?'
    onFinalize(finalQuestion)
  }

  const handleEditQuestion = () => {
    setCustomQuestion(suggestedQuestion)
    setEditingQuestion(true)
  }

  const handleSaveCustomQuestion = () => {
    setEditingQuestion(false)
    handleFinalize(customQuestion)
  }

  const getMessageTypeIcon = (messageType) => {
    switch (messageType) {
      case 'question':
        return <AlertCircleIcon className="w-4 h-4 text-blue-500" />
      case 'information':
        return <CheckIcon className="w-4 h-4 text-green-500" />
      case 'ready':
        return <ArrowRightIcon className="w-4 h-4 text-green-600" />
      default:
        return <MessageCircleIcon className="w-4 h-4 text-gray-500" />
    }
  }

  const getMessageTypeLabel = (messageType) => {
    switch (messageType) {
      case 'question':
        return 'Pregunta'
      case 'information':
        return 'Información'
      case 'ready':
        return 'Listo para enviar'
      default:
        return 'Mensaje'
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-blue-50 border-b border-blue-100">
        <div className="flex items-center space-x-2">
          <BrainIcon className="w-5 h-5 text-blue-600" />
          <h3 className="font-medium text-blue-900">Construcción de Contexto</h3>
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
            {contextMessages.length} mensajes
          </span>
          {readyMessage && (
            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
              ✓ Contexto completo
            </span>
          )}
        </div>
      </div>

      {/* Messages Flow */}
      <div className="p-4 space-y-3 max-h-64 overflow-y-auto">
        {contextMessages.map((message, index) => (
          <div key={index} className="flex space-x-3">
            <div className="flex-shrink-0 mt-1">
              {getMessageTypeIcon(message.message_type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-xs font-medium text-gray-600">
                  {getMessageTypeLabel(message.message_type)}
                </span>
                {message.context_elements_count > 0 && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                    +{message.context_elements_count} elementos
                  </span>
                )}
              </div>
              <div className={`rounded-lg p-3 ${
                message.message_type === 'ready' ? 'bg-green-50 border border-green-200' : 'bg-gray-50'
              }`}>
                <p className="text-sm text-gray-700 mb-2">
                  <strong>Usuario:</strong> {message.user_message}
                </p>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                  <strong>IA:</strong> {message.ai_response}
                </p>
                {message.suggestions && message.suggestions.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-1">Sugerencias:</p>
                    <ul className="text-xs text-gray-600 space-y-0.5">
                      {message.suggestions.map((suggestion, idx) => (
                        <li key={idx} className="flex items-start space-x-1">
                          <span>•</span>
                          <span>{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Accumulated Context */}
      {accumulatedContext && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Contexto Acumulado:</h4>
          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {accumulatedContext}
            </p>
          </div>
        </div>
      )}

      {/* Suggested Question Section */}
      {readyMessage && suggestedQuestion && (
        <div className="px-4 py-3 bg-green-50 border-t border-green-200">
          <h4 className="text-sm font-medium text-green-900 mb-2 flex items-center space-x-2">
            <ArrowRightIcon className="w-4 h-4" />
            <span>Pregunta sugerida para las IAs principales:</span>
          </h4>
          
          {editingQuestion ? (
            <div className="space-y-3">
              <textarea
                value={customQuestion}
                onChange={(e) => setCustomQuestion(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg resize-none text-sm"
                rows={3}
                placeholder="Edita la pregunta..."
              />
              <div className="flex space-x-2">
                <button
                  onClick={handleSaveCustomQuestion}
                  disabled={!customQuestion.trim() || isLoading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm flex items-center space-x-2"
                >
                  <SendIcon className="w-4 h-4" />
                  <span>Enviar a IAs</span>
                </button>
                <button
                  onClick={() => setEditingQuestion(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm"
                >
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg p-3 border border-green-300">
              <p className="text-sm text-gray-800 mb-3 font-medium">
                "{suggestedQuestion}"
              </p>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleFinalize(suggestedQuestion)}
                  disabled={isLoading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm flex items-center space-x-2"
                >
                  <SendIcon className="w-4 h-4" />
                  <span>Enviar esta pregunta</span>
                </button>
                <button
                  onClick={handleEditQuestion}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm flex items-center space-x-2"
                >
                  <EditIcon className="w-4 h-4" />
                  <span>Editar pregunta</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Fallback Actions */}
      {contextMessages.length > 0 && !readyMessage && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <div className="flex space-x-2">
            <button
              onClick={() => handleFinalize('')}
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              <SendIcon className="w-4 h-4" />
              <span>Enviar a IAs Principales</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ContextBuildingFlow 