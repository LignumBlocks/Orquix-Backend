import { useState, useEffect } from 'react'
import { AlertCircleIcon, CheckCircleIcon, LoaderIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'

const ConversationStatePanel = () => {
  const {
    activeProject,
    isQuerying,
    clarificationNeeded,
    preAnalystResult,
    continuityInfo,
    error
  } = useAppStore()

  if (!activeProject) return null

  return (
    <div className="border-t border-gray-200 bg-gray-50 p-4">
      <div className="flex items-center space-x-4">
        {/* Estado de la consulta */}
        {isQuerying && (
          <div className="flex items-center text-blue-600">
            <LoaderIcon className="w-5 h-5 mr-2 animate-spin" />
            <span>Procesando consulta...</span>
          </div>
        )}

        {/* Indicador de clarificación */}
        {clarificationNeeded && (
          <div className="flex items-center text-yellow-600">
            <AlertCircleIcon className="w-5 h-5 mr-2" />
            <span>Se necesita clarificación</span>
          </div>
        )}

        {/* Indicador de continuidad */}
        {continuityInfo?.is_continuation && (
          <div className="flex items-center text-green-600">
            <CheckCircleIcon className="w-5 h-5 mr-2" />
            <span>Usando contexto previo</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center text-red-600">
            <AlertCircleIcon className="w-5 h-5 mr-2" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default ConversationStatePanel 