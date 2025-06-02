import { useState } from 'react'
import { SettingsIcon, ChevronDownIcon, ChevronRightIcon } from 'lucide-react'

const RightSidebar = () => {
  const [expandedAgents, setExpandedAgents] = useState(new Set())

  const agents = [
    {
      id: 1,
      name: 'Agent1',
      status: 'online',
      latency: '1.2s',
      prompt: 'What are the main emerging tr...',
      icon: '🤖',
      color: 'blue'
    },
    {
      id: 2,
      name: 'Agent2',
      status: 'online',
      latency: '0.8s',
      prompt: 'What are the main emerging trends i...',
      icon: '🤖',
      color: 'blue'
    },
    {
      id: 3,
      name: 'Agent3',
      status: 'error',
      latency: '12.0s',
      prompt: 'What are the main emerging trends i...',
      icon: '💎',
      color: 'blue'
    },
    {
      id: 4,
      name: 'Agent4',
      status: 'online',
      latency: '2.1s',
      prompt: 'What are the main emerging trends i...',
      icon: '⚡',
      color: 'orange'
    },
    {
      id: 5,
      name: 'Agent5',
      status: 'online',
      latency: '1.5s',
      prompt: 'What are the main emerging trends i...',
      icon: '🌲',
      color: 'green'
    },
    {
      id: 6,
      name: 'Agent6',
      status: 'online',
      latency: '0.9s',
      prompt: 'What are the main emerging trends i...',
      icon: '🌲',
      color: 'green'
    }
  ]

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

  return (
    <div className="p-4 h-full custom-scrollbar">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Active AIs</h2>
      
      <div className="space-y-3">
        {agents.map((agent) => (
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
                </div>
                
                <button className="text-gray-400 hover:text-gray-600 smooth-transition hover:bg-gray-100 p-1 rounded">
                  <SettingsIcon className="w-4 h-4" />
                </button>
              </div>
              
              <div className="text-xs text-gray-500 mb-2">
                Latency: <span className={agent.status === 'error' ? 'text-red-600 font-medium' : 'text-gray-700'}>{agent.latency}</span>
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
                      What are the main emerging trends in the fintech sector for 2024? 
                      Please provide detailed analysis including market data, regulatory changes, 
                      and technological innovations.
                    </div>
                  </div>
                  
                  <div className="mt-2 flex items-center justify-between text-xs">
                    <div className="text-gray-500">
                      Model: <span className="font-medium">GPT-4</span>
                    </div>
                    <div className="text-gray-500">
                      Tokens: <span className="font-medium">1,247</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Model Selection */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-sm font-medium text-gray-700 mb-2">Change model:</div>
        <div className="space-y-1">
          {['Agent1', 'Agent2', 'Agent3', 'Agent4', 'Agent5', 'Agent6'].map((agent) => (
            <button 
              key={agent}
              className="flex items-center w-full text-left text-xs text-blue-600 hover:text-blue-800 py-1 smooth-transition hover:bg-blue-50 px-2 rounded"
            >
              <span className="mr-2">🤖</span>
              {agent}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default RightSidebar 