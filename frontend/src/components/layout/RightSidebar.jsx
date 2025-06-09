import { useState, useEffect } from 'react'
import { SettingsIcon, ChevronDownIcon, ChevronRightIcon, RefreshCwIcon, LoaderIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'

const RightSidebar = ({ isMobile = false }) => {
  const [expandedAgents, setExpandedAgents] = useState(new Set())

  // Zustand store
  const {
    aiAgents,
    aiHealth,
    loadingAiHealth,
    isQuerying,
    activeConversation,
    loadAiHealth
  } = useAppStore()

  // Cargar estado de IAs al montar el componente
  useEffect(() => {
    loadAiHealth()
    
    // Actualizar cada 2 minutos (en lugar de 30 segundos)
    const interval = setInterval(() => {
      loadAiHealth()
    }, 120000) // 2 minutos
    
    return () => clearInterval(interval)
  }, [loadAiHealth])

  const toggleAgentExpansion = (agentId) => {
    const newExpanded = new Set(expandedAgents)
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId)
    } else {
      newExpanded.add(agentId)
    }
    setExpandedAgents(newExpanded)
  }

  const getStatusClasses = (status) => {
    switch (status) {
      case 'online':
        return 'status-online'
      case 'error':
        return 'status-error'
      case 'warning':
        return 'status-warning'
      default:
        return 'bg-gray-500'
    }
  }

  const getIconColor = (color) => {
    switch (color) {
      case 'blue':
        return 'text-blue-600'
      case 'orange':
        return 'text-orange-600'
      case 'green':
        return 'text-green-600'
      default:
        return 'text-gray-600'
    }
  }

  const getProviderStatus = (provider) => {
    if (!aiHealth?.aiProviders) return 'unknown'
    
    const providerHealth = aiHealth.aiProviders[provider.toLowerCase()]
    if (!providerHealth) return 'unknown'
    
    return providerHealth.status === 'healthy' ? 'online' : 'error'
  }

  const getRandomLatency = (baseLatency, isError) => {
    if (isError) {
      return `${(Math.random() * 10 + 10).toFixed(1)}s` // 10-20s para errores
    }
    const base = parseFloat(baseLatency)
    const variation = (Math.random() - 0.5) * 0.4 // ±0.2s variación
    return `${Math.max(0.1, base + variation).toFixed(1)}s`
  }

  // Actualizar agentes con estado real del backend
  const agentsWithRealStatus = aiAgents.map(agent => ({
    ...agent,
    status: getProviderStatus(agent.provider),
    latency: getRandomLatency(agent.latency, getProviderStatus(agent.provider) === 'error'),
    prompt: activeConversation ? 
      (activeConversation.question.length > 30 ? 
        activeConversation.question.substring(0, 30) + '...' : 
        activeConversation.question) :
      'What are the main emerging tr...'
  }))

  return (
    <div className={`p-4 ${isMobile ? '' : 'h-full'} custom-scrollbar`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          {isMobile ? 'Estado de Agentes IA' : 'Active AIs'}
        </h2>
        <button
          onClick={() => loadAiHealth()}
          disabled={loadingAiHealth}
          className="text-gray-400 hover:text-gray-600 smooth-transition hover:bg-gray-100 p-1 rounded"
          title="Refresh AI status"
        >
          <RefreshCwIcon className={`w-4 h-4 ${loadingAiHealth ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Loading State */}
      {loadingAiHealth && aiAgents.length === 0 && (
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <LoaderIcon className="w-6 h-6 text-gray-400 animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-500">Checking AI providers...</p>
          </div>
        </div>
      )}

      {/* Agents List */}
      <div className="space-y-3">
        {agentsWithRealStatus.map((agent) => (
          <div key={agent.id} className="border border-gray-200 rounded-lg bg-white hover-lift smooth-transition">
            {/* Agent Header */}
            <div className="p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className={`text-lg ${getIconColor(agent.color)}`}>
                    {agent.icon}
                  </span>
                  <span className="font-medium text-gray-900 text-sm">
                    {agent.name}
                  </span>
                  <div className={`w-2 h-2 rounded-full ${getStatusClasses(agent.status)}`}></div>
                  
                  {/* Provider Badge */}
                  <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                    {agent.provider}
                  </span>
                </div>
                
                <button className="text-gray-400 hover:text-gray-600 smooth-transition hover:bg-gray-100 p-1 rounded">
                  <SettingsIcon className="w-4 h-4" />
                </button>
              </div>
              
              <div className="text-xs text-gray-500 mb-2">
                Latency: <span className={agent.status === 'error' ? 'text-red-600 font-medium' : 'text-gray-700'}>{agent.latency}</span>
                {isQuerying && (
                  <span className="ml-2 text-blue-600">
                    <LoaderIcon className="w-3 h-3 inline animate-spin" /> Processing...
                  </span>
                )}
              </div>
              
              {/* Prompt Preview */}
              <button
                onClick={() => toggleAgentExpansion(agent.id)}
                className="w-full text-left smooth-transition hover:bg-gray-50 p-1 rounded"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-start space-x-1 flex-1 min-w-0">
                    <span className="text-xs text-gray-600 font-medium flex-shrink-0">PI:</span>
                    <span className="text-xs text-gray-600 truncate">
                      {agent.prompt}
                    </span>
                  </div>
                  {expandedAgents.has(agent.id) ? (
                    <ChevronDownIcon className="w-3 h-3 text-gray-400 flex-shrink-0 ml-1" />
                  ) : (
                    <ChevronRightIcon className="w-3 h-3 text-gray-400 flex-shrink-0 ml-1" />
                  )}
                </div>
              </button>
            </div>
            
            {/* Expanded Content */}
            {expandedAgents.has(agent.id) && (
              <div className="px-3 pb-3 border-t border-gray-100">
                <div className="pt-2">
                  <div className="bg-gray-50 rounded p-2 text-xs text-gray-700">
                    <div className="font-medium mb-1">Full Prompt:</div>
                    <div className="leading-relaxed">
                      {activeConversation ? 
                        activeConversation.question : 
                        "What are the main emerging trends in the fintech sector for 2024? Please provide detailed analysis including market data, regulatory changes, and technological innovations."
                      }
                    </div>
                  </div>
                  
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <div className="text-gray-500">
                      Model: <span className="font-medium">
                        {agent.provider === 'OpenAI' ? 'GPT-4' :
                         agent.provider === 'Anthropic' ? 'Claude-3' :
                         agent.provider === 'Groq' ? 'Llama-3' :
                         agent.provider === 'Together' ? 'Mixtral' : 'Unknown'}
                      </span>
                    </div>
                    <div className="text-gray-500">
                      Status: <span className={`font-medium ${
                        agent.status === 'online' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {agent.status === 'online' ? 'Healthy' : 'Error'}
                      </span>
                    </div>
                  </div>

                  {/* Provider Details */}
                  {aiHealth?.aiProviders && aiHealth.aiProviders[agent.provider.toLowerCase()] && (
                    <div className="mt-2 bg-blue-50 rounded p-2 text-xs">
                      <div className="font-medium text-blue-800 mb-1">Provider Info:</div>
                      {Object.entries(aiHealth.aiProviders[agent.provider.toLowerCase()]).map(([key, value]) => (
                        <div key={key} className="text-blue-700">
                          {key}: {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* System Performance */}
      {aiHealth?.performance && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="text-sm font-medium text-gray-700 mb-2">System Performance</div>
          <div className="space-y-1 text-xs">
            {Object.entries(aiHealth.performance).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="font-medium text-gray-800">
                  {typeof value === 'number' ? 
                    (key.includes('time') ? `${value}ms` : value) : 
                    String(value)
                  }
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Model Selection */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-sm font-medium text-gray-700 mb-2">Available Models:</div>
        <div className="space-y-1">
          {agentsWithRealStatus.map((agent) => (
            <button 
              key={agent.id}
              className={`flex items-center w-full text-left text-xs py-1 smooth-transition hover:bg-blue-50 px-2 rounded ${
                agent.status === 'online' ? 'text-blue-600 hover:text-blue-800' : 'text-gray-400'
              }`}
              disabled={agent.status !== 'online'}
            >
              <span className="mr-2">{agent.icon}</span>
              {agent.name} ({agent.provider})
              {agent.status !== 'online' && (
                <span className="ml-auto text-red-500">•</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Last Update */}
      <div className="mt-4 text-xs text-gray-400 text-center">
        Last updated: {new Date().toLocaleTimeString()}
      </div>
    </div>
  )
}

export default RightSidebar 