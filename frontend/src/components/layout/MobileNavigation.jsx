import { MenuIcon, MessageSquareIcon, FolderIcon, CpuIcon, XIcon } from 'lucide-react'

const MobileNavigation = ({ 
  activeTab, 
  onTabChange, 
  sidebarOpen, 
  setSidebarOpen, 
  activeProject,
  className 
}) => {
  const tabs = [
    { 
      id: 'chat', 
      name: 'Chat', 
      icon: MessageSquareIcon,
      description: 'Conversación con IA'
    },
    { 
      id: 'projects', 
      name: 'Proyectos', 
      icon: FolderIcon,
      description: 'Gestión de proyectos'
    },
    { 
      id: 'agents', 
      name: 'Agentes', 
      icon: CpuIcon,
      description: 'Estado de IAs'
    }
  ]

  return (
    <div className={className}>
      {/* Header Bar */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo & Menu */}
          <div className="flex items-center">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="mr-3 p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            >
              {sidebarOpen ? (
                <XIcon className="w-5 h-5" />
              ) : (
                <MenuIcon className="w-5 h-5" />
              )}
            </button>
            
            <div className="flex items-center">
              <h1 className="text-lg font-semibold text-gray-900">Orquix</h1>
              {activeProject && (
                <span className="ml-2 text-sm text-gray-500 truncate max-w-32">
                  • {activeProject.name}
                </span>
              )}
            </div>
          </div>

          {/* Status Indicator */}
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
            <span className="text-xs text-gray-500">Online</span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`
                  flex-1 flex flex-col items-center justify-center py-3 px-2
                  text-xs font-medium transition-colors relative
                  ${isActive 
                    ? 'text-blue-600 bg-blue-50' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }
                `}
              >
                <Icon className={`w-5 h-5 mb-1 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                <span className="truncate">{tab.name}</span>
                
                {/* Active indicator */}
                {isActive && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"></div>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default MobileNavigation 