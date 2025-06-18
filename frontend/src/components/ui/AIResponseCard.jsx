import { useState } from 'react'
import { ChevronDownIcon, ChevronUpIcon, ClockIcon, MessageSquareIcon, BrainIcon } from 'lucide-react'

const AIResponseCard = ({ conversation }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!conversation) return null

  const getQualityColor = (quality) => {
    switch (quality?.toLowerCase()) {
      case 'high': return 'bg-green-100 text-green-700 border-green-200'
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'low': return 'bg-red-100 text-red-700 border-red-200'
      default: return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const hasContextUsed = conversation.context_used && conversation.context_used.trim()

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div 
        className={`px-4 py-3 cursor-pointer select-none ${getQualityColor(conversation.moderator_quality)}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <MessageSquareIcon className="w-4 h-4" />
              {hasContextUsed && (
                <BrainIcon className="w-4 h-4 text-blue-600" title="Respuesta con contexto construido" />
              )}
            </div>
            <span className="font-medium text-sm">
              {conversation.user_prompt}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            {/* Processing Time */}
            <div className="flex items-center space-x-1 text-sm">
              <ClockIcon className="w-3 h-3" />
              <span>{conversation.processing_time_ms}ms</span>
            </div>

            {/* Expand Icon */}
            {isExpanded ? (
              <ChevronUpIcon className="w-4 h-4" />
            ) : (
              <ChevronDownIcon className="w-4 h-4" />
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="bg-white">
          {/* Context Used (if available) */}
          {hasContextUsed && (
            <div className="p-4 border-b border-gray-100 bg-blue-50">
              <h4 className="text-sm font-medium text-blue-900 mb-2 flex items-center space-x-2">
                <BrainIcon className="w-4 h-4" />
                <span>Contexto Utilizado:</span>
              </h4>
              <div className="bg-white rounded-lg p-3 border border-blue-200">
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {conversation.context_used}
                </p>
              </div>
            </div>
          )}

          {/* Synthesis Preview */}
          <div className="p-4 border-b border-gray-100">
            <h4 className="text-sm font-medium text-gray-900 mb-2">
              {hasContextUsed ? 'Respuesta de las IAs Principales:' : 'Síntesis:'}
            </h4>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
                {conversation.synthesis_preview}
              </p>
            </div>
          </div>

          {/* Metadata */}
          <div className="p-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Calidad:</span>
                <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getQualityColor(conversation.moderator_quality)}`}>
                  {conversation.moderator_quality}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Fecha:</span>
                <span className="ml-2 text-gray-700">
                  {formatDate(conversation.created_at)}
                </span>
              </div>
              {hasContextUsed && (
                <div className="col-span-2">
                  <span className="text-gray-600">Tipo:</span>
                  <span className="ml-2 text-blue-700 bg-blue-100 px-2 py-1 rounded text-xs">
                    Respuesta con Contexto Construido
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AIResponseCard 