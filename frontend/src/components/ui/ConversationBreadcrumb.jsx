import { LinkIcon, ArrowRightIcon, MessageSquareIcon } from 'lucide-react'

const ConversationBreadcrumb = ({ 
  currentPrompt, 
  isFollowup = false, 
  previousContext = null,
  enrichmentApplied = false 
}) => {
  
  if (!isFollowup || !previousContext) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-blue-50 rounded-lg border border-blue-200">
        <MessageSquareIcon className="w-4 h-4 text-blue-600" />
        <span className="text-sm text-blue-800 font-medium">Nueva conversación</span>
      </div>
    )
  }

  // Truncar texto largo
  const truncateText = (text, maxLength = 40) => {
    if (!text || text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <div className="space-y-2">
      {/* Breadcrumb Principal */}
      <div className="flex items-center space-x-2 px-3 py-2 bg-green-50 rounded-lg border border-green-200">
        <LinkIcon className="w-4 h-4 text-green-600 flex-shrink-0" />
        <span className="text-sm text-green-800 font-medium">Continuando conversación</span>
        {enrichmentApplied && (
          <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded-full">
            ✨ Enriquecido
          </span>
        )}
      </div>

      {/* Flujo Conversacional */}
      <div className="bg-white border border-gray-200 rounded-lg p-3">
        <div className="flex items-start space-x-3">
          {/* Contexto Previo */}
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-gray-500 mb-1">Contexto previo:</div>
            <div className="bg-gray-50 rounded p-2 border border-gray-100">
              <p className="text-sm text-gray-700 line-clamp-2">
                {truncateText(previousContext.refined_prompt || previousContext.user_prompt, 80)}
              </p>
              {previousContext.synthesis && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <div className="text-xs text-gray-500 mb-1">Síntesis anterior:</div>
                  <p className="text-xs text-gray-600 line-clamp-2">
                    {truncateText(previousContext.synthesis, 100)}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Flecha */}
          <div className="flex items-center pt-6">
            <ArrowRightIcon className="w-4 h-4 text-gray-400" />
          </div>

          {/* Nueva Consulta */}
          <div className="flex-1 min-w-0">
            <div className="text-xs font-medium text-gray-500 mb-1">Nueva consulta:</div>
            <div className="bg-blue-50 rounded p-2 border border-blue-100">
              <p className="text-sm text-blue-900 font-medium line-clamp-2">
                {truncateText(currentPrompt, 80)}
              </p>
            </div>
          </div>
        </div>

        {/* Detalles del Enriquecimiento */}
        {enrichmentApplied && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="bg-green-50 rounded-lg p-2 border border-green-200">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-xs font-medium text-green-800">🔗 Contexto histórico aplicado</span>
              </div>
              <p className="text-xs text-green-700">
                Esta consulta ha sido enriquecida automáticamente con información de la conversación anterior 
                para proporcionar respuestas más coherentes y contextualmente relevantes.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ConversationBreadcrumb 