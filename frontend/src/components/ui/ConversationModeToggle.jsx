import { useState } from 'react'
import { LinkIcon, RotateCcwIcon, MessageSquareIcon, InfoIcon } from 'lucide-react'

const ConversationModeToggle = ({ 
  mode = 'auto', // 'auto', 'continue', 'new'
  onModeChange,
  hasContext = false,
  disabled = false 
}) => {
  const [showTooltip, setShowTooltip] = useState(false)

  const modes = [
    {
      key: 'auto',
      label: 'Automático',
      icon: MessageSquareIcon,
      description: 'El sistema detecta automáticamente si es seguimiento',
      color: 'bg-blue-100 text-blue-800 border-blue-200',
      activeColor: 'bg-blue-500 text-white border-blue-500'
    },
    {
      key: 'continue',
      label: 'Continuar',
      icon: LinkIcon,
      description: 'Usar contexto de la conversación anterior',
      color: 'bg-green-100 text-green-800 border-green-200',
      activeColor: 'bg-green-500 text-white border-green-500',
      disabled: !hasContext
    },
    {
      key: 'new',
      label: 'Nueva',
      icon: RotateCcwIcon,
      description: 'Iniciar conversación desde cero',
      color: 'bg-gray-100 text-gray-800 border-gray-200',
      activeColor: 'bg-gray-500 text-white border-gray-500'
    }
  ]

  const handleModeChange = (newMode) => {
    if (disabled) return
    if (onModeChange) {
      onModeChange(newMode)
    }
  }

  return (
    <div className="relative">
      {/* Toggle Buttons */}
      <div className="flex items-center space-x-1 bg-white border border-gray-200 rounded-lg p-1">
        {modes.map((modeOption) => {
          const Icon = modeOption.icon
          const isActive = mode === modeOption.key
          const isDisabled = disabled || modeOption.disabled
          
          return (
            <button
              key={modeOption.key}
              onClick={() => handleModeChange(modeOption.key)}
              disabled={isDisabled}
              className={`
                flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium
                transition-all duration-200 border
                ${isActive 
                  ? modeOption.activeColor 
                  : `${modeOption.color} hover:bg-opacity-80`
                }
                ${isDisabled 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'cursor-pointer'
                }
              `}
              title={modeOption.description}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{modeOption.label}</span>
            </button>
          )
        })}
        
        {/* Info Button */}
        <div className="relative">
          <button
            onClick={() => setShowTooltip(!showTooltip)}
            className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <InfoIcon className="w-4 h-4" />
          </button>
          
          {/* Tooltip */}
          {showTooltip && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-10">
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Modos de Conversación</h4>
                <div className="space-y-2 text-sm">
                  {modes.map((modeOption) => {
                    const Icon = modeOption.icon
                    return (
                      <div key={modeOption.key} className="flex items-start space-x-2">
                        <Icon className="w-4 h-4 mt-0.5 text-gray-500 flex-shrink-0" />
                        <div>
                          <span className="font-medium text-gray-900">{modeOption.label}:</span>
                          <span className="text-gray-600 ml-1">{modeOption.description}</span>
                          {modeOption.disabled && (
                            <span className="text-orange-600 ml-1">(No hay contexto disponible)</span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div className="pt-2 border-t border-gray-100">
                  <p className="text-xs text-gray-500">
                    💡 <strong>Tip:</strong> El modo automático usa IA para detectar si tu consulta 
                    es continuación de la anterior. Los modos manuales te dan control total.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Current Mode Indicator */}
      {mode !== 'auto' && (
        <div className="mt-2 text-xs text-gray-600">
          {mode === 'continue' && hasContext && (
            <span className="flex items-center space-x-1">
              <LinkIcon className="w-3 h-3" />
              <span>La próxima consulta usará contexto previo</span>
            </span>
          )}
          {mode === 'new' && (
            <span className="flex items-center space-x-1">
              <RotateCcwIcon className="w-3 h-3" />
              <span>La próxima consulta iniciará conversación nueva</span>
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default ConversationModeToggle 