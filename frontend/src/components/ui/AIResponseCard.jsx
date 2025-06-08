import { useState } from 'react'
import { ChevronDownIcon, ChevronUpIcon, ClockIcon, CpuIcon } from 'lucide-react'

const AIResponseCard = ({ response, index }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!response) return null

  const getProviderColor = (provider) => {
    switch (provider?.toLowerCase()) {
      case 'openai': return 'bg-green-100 text-green-700 border-green-200'
      case 'anthropic': return 'bg-purple-100 text-purple-700 border-purple-200'
      default: return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'success': return 'bg-green-100 text-green-700'
      case 'error': return 'bg-red-100 text-red-700'
      default: return 'bg-yellow-100 text-yellow-700'
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div 
        className={`px-4 py-3 cursor-pointer select-none ${getProviderColor(response.ia_provider_name)}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="font-medium">
              IA #{index} - {response.ia_provider_name?.toUpperCase()}
            </span>
            
            {/* Status Badge */}
            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(response.status)}`}>
              {response.status}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            {/* Latency */}
            <div className="flex items-center space-x-1 text-sm">
              <ClockIcon className="w-3 h-3" />
              <span>{response.latency_ms}ms</span>
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
          {/* Response Text */}
          {response.response_text && (
            <div className="p-4 border-b border-gray-100">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Respuesta:</h4>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
                  {response.response_text}
                </p>
              </div>
            </div>
          )}

          {/* Usage Info */}
          {response.usage_info && (
            <div className="p-4 border-b border-gray-100">
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                <CpuIcon className="w-4 h-4 inline mr-1" />
                Uso de Tokens:
              </h4>
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {response.usage_info.prompt_tokens && (
                    <div>
                      <span className="text-gray-600">Prompt:</span>
                      <span className="ml-1 font-mono text-blue-700">
                        {response.usage_info.prompt_tokens}
                      </span>
                    </div>
                  )}
                  {response.usage_info.completion_tokens && (
                    <div>
                      <span className="text-gray-600">Respuesta:</span>
                      <span className="ml-1 font-mono text-blue-700">
                        {response.usage_info.completion_tokens}
                      </span>
                    </div>
                  )}
                  {response.usage_info.total_tokens && (
                    <div>
                      <span className="text-gray-600">Total:</span>
                      <span className="ml-1 font-mono font-medium text-blue-700">
                        {response.usage_info.total_tokens}
                      </span>
                    </div>
                  )}
                  {response.usage_info.model && (
                    <div>
                      <span className="text-gray-600">Modelo:</span>
                      <span className="ml-1 text-xs text-gray-500">
                        {response.usage_info.model}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {response.error_message && (
            <div className="p-4">
              <h4 className="text-sm font-medium text-red-900 mb-2">Error:</h4>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-700 text-sm">{response.error_message}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default AIResponseCard 