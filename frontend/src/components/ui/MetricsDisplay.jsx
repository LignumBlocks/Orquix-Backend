import { ClockIcon, CpuIcon, TrendingUpIcon, AlertTriangleIcon } from 'lucide-react'

const MetricsDisplay = ({ 
  processingTime, 
  moderatorQuality, 
  fallbackUsed, 
  aiResponsesCount,
  totalTokens 
}) => {
  const getQualityColor = (quality) => {
    switch (quality?.toLowerCase()) {
      case 'high': return 'bg-green-100 text-green-700 border-green-200'
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'low': return 'bg-red-100 text-red-700 border-red-200'
      default: return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const formatTime = (ms) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
  }

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
        <TrendingUpIcon className="w-4 h-4 mr-1" />
        Métricas de Rendimiento
      </h4>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Processing Time */}
        {processingTime && (
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <ClockIcon className="w-4 h-4 text-gray-500" />
            </div>
            <div className="text-lg font-semibold text-gray-900">
              {formatTime(processingTime)}
            </div>
            <div className="text-xs text-gray-500">Tiempo Total</div>
          </div>
        )}

        {/* Moderator Quality */}
        {moderatorQuality && (
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <div className={`px-2 py-1 rounded text-xs font-medium ${getQualityColor(moderatorQuality)}`}>
                {moderatorQuality}
              </div>
            </div>
            <div className="text-xs text-gray-500">Calidad Síntesis</div>
          </div>
        )}

        {/* AI Responses */}
        {aiResponsesCount !== undefined && (
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <CpuIcon className="w-4 h-4 text-gray-500" />
            </div>
            <div className="text-lg font-semibold text-gray-900">
              {aiResponsesCount}
            </div>
            <div className="text-xs text-gray-500">IAs Consultadas</div>
          </div>
        )}

        {/* Total Tokens */}
        {totalTokens && (
          <div className="text-center">
            <div className="text-lg font-semibold text-gray-900">
              {totalTokens.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">Tokens Usados</div>
          </div>
        )}
      </div>

      {/* Fallback Warning */}
      {fallbackUsed && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center space-x-2 text-orange-700 bg-orange-50 rounded p-2">
            <AlertTriangleIcon className="w-4 h-4 flex-shrink-0" />
            <span className="text-xs">
              Se utilizó modo fallback - algunos proveedores de IA no estuvieron disponibles
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default MetricsDisplay 