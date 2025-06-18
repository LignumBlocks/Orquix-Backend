import { LinkIcon, InfoIcon, CheckCircleIcon } from 'lucide-react'

const ContinuityIndicator = ({ 
  isFollowup = false, 
  confidenceScore = 0, 
  referenceType = 'new_topic',
  enrichmentApplied = false,
  size = 'default' // 'compact', 'default', 'detailed'
}) => {

  if (!isFollowup) return null

  // Colores basados en el tipo de referencia
  const getIndicatorStyle = (type) => {
    switch (type) {
      case 'anaphoric':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'topic_expansion':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'clarification':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  // Emoji basado en el tipo
  const getTypeEmoji = (type) => {
    switch (type) {
      case 'anaphoric': return '🔗'
      case 'topic_expansion': return '📈'
      case 'clarification': return '❓'
      default: return '💬'
    }
  }

  // Texto descriptivo
  const getTypeDescription = (type) => {
    switch (type) {
      case 'anaphoric': return 'Referencia anafórica'
      case 'topic_expansion': return 'Expansión de tema'
      case 'clarification': return 'Clarificación'
      default: return 'Seguimiento'
    }
  }

  // Versión compacta
  if (size === 'compact') {
    return (
      <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full border text-xs font-medium 
        ${getIndicatorStyle(referenceType)}`}>
        <LinkIcon className="w-3 h-3" />
        <span>{getTypeEmoji(referenceType)}</span>
      </div>
    )
  }

  // Versión por defecto
  if (size === 'default') {
    return (
      <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg border 
        ${getIndicatorStyle(referenceType)}`}>
        <LinkIcon className="w-4 h-4 flex-shrink-0" />
        <span className="text-sm font-medium">
          {getTypeEmoji(referenceType)} {getTypeDescription(referenceType)}
        </span>
        {enrichmentApplied && (
          <CheckCircleIcon className="w-4 h-4 text-green-600" />
        )}
      </div>
    )
  }

  // Versión detallada
  return (
    <div className={`rounded-lg border p-4 ${getIndicatorStyle(referenceType)}`}>
      <div className="flex items-start space-x-3">
        <LinkIcon className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-sm font-semibold">
              {getTypeEmoji(referenceType)} {getTypeDescription(referenceType)}
            </span>
            {confidenceScore > 0 && (
              <span className="text-xs bg-white bg-opacity-60 px-2 py-1 rounded-full">
                {Math.round(confidenceScore * 100)}% confianza
              </span>
            )}
          </div>
          
          <p className="text-sm mb-3">
            Esta consulta está relacionada con conversaciones anteriores y se procesará 
            con contexto histórico para mayor coherencia.
          </p>

          {enrichmentApplied && (
            <div className="flex items-center space-x-2 text-sm">
              <CheckCircleIcon className="w-4 h-4 text-green-600" />
              <span>Enriquecimiento contextual aplicado</span>
            </div>
          )}

          {/* Detalles técnicos */}
          <div className="mt-3 pt-3 border-t border-current border-opacity-20">
            <div className="flex items-center space-x-2 text-xs opacity-75">
              <InfoIcon className="w-3 h-3" />
              <span>
                Tipo: {referenceType} | Confianza: {Math.round(confidenceScore * 100)}%
                {enrichmentApplied && ' | Contexto: Aplicado'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ContinuityIndicator 