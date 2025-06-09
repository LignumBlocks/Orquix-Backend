import { useState, useEffect } from 'react'
import { config } from './config'
import LeftSidebar from './components/layout/LeftSidebar'
import CenterColumn from './components/layout/CenterColumn'
import RightSidebar from './components/layout/RightSidebar'
import MobileNavigation from './components/layout/MobileNavigation'
import { ToastContainer, useToast } from './components/ui/Toast'
import useAppStore from './store/useAppStore'
import { initMockAuthIfNeeded, mockAuth } from './utils/mockAuth'

function App() {
  const [localActiveProject, setLocalActiveProject] = useState(null)
  const [activeTab, setActiveTab] = useState('chat') // chat, projects, agents
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { toasts, removeToast, success, error, warning, info } = useToast()

  // Zustand store
  const {
    activeProject: storeActiveProject,
    moderatorConfig: storeModeratorConfig,
    initialize,
    setActiveProject: setStoreActiveProject,
    updateModeratorConfig,
    setUser,
    setAuthToken
  } = useAppStore()

  // Inicializar la aplicación
  useEffect(() => {
    // Siempre configurar autenticación mock para que la app funcione sin login
    const authSetup = initMockAuthIfNeeded()
    
    // Configurar usuario mock en el store siempre
    setUser(mockAuth.getMockUser())
    setAuthToken(mockAuth.MOCK_TOKEN)
    
    // Inicializar store
    initialize()
  }, [initialize, setUser, setAuthToken])

  // Sincronizar estado local con store
  useEffect(() => {
    if (storeActiveProject) {
      setLocalActiveProject(storeActiveProject)
    }
  }, [storeActiveProject])

  // Handlers para compatibilidad con props existentes
  const handleSetActiveProject = (project) => {
    setLocalActiveProject(project)
    setStoreActiveProject(project)
  }

  const handleSetModeratorConfig = (config) => {
    updateModeratorConfig(config)
  }

  // Hacer las notificaciones disponibles globalmente
  useEffect(() => {
    window.showToast = { success, error, warning, info }
  }, [success, error, warning, info])

  // Cerrar sidebar al cambiar de tab en móvil
  const handleTabChange = (tab) => {
    setActiveTab(tab)
    setSidebarOpen(false)
  }

  return (
    <div className="h-screen-mobile bg-gray-50 flex flex-col">
      {/* Mobile Navigation */}
      <MobileNavigation 
        activeTab={activeTab}
        onTabChange={handleTabChange}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activeProject={localActiveProject}
        className="lg:hidden"
      />

      {/* Desktop Layout */}
      <div className="hidden lg:flex flex-1">
        {/* Left Sidebar - Desktop & Tablet */}
        <div className="w-[280px] min-w-[280px] xl:w-[320px] xl:min-w-[320px] bg-white border-r border-gray-200 overflow-y-auto">
          <LeftSidebar 
            activeProject={localActiveProject}
            setActiveProject={handleSetActiveProject}
            moderatorConfig={storeModeratorConfig}
            setModeratorConfig={handleSetModeratorConfig}
          />
        </div>

        {/* Center Column - Desktop */}
        <div className="flex-1 bg-gray-50 flex flex-col min-w-0">
          <CenterColumn 
            activeProject={localActiveProject}
            moderatorConfig={storeModeratorConfig}
          />
        </div>

        {/* Right Sidebar - Desktop */}
        <div className="w-[320px] min-w-[320px] xl:w-[360px] xl:min-w-[360px] bg-white border-l border-gray-200 overflow-y-auto">
          <RightSidebar />
        </div>
      </div>

      {/* Mobile Layout */}
      <div className="lg:hidden flex-1 flex flex-col overflow-hidden">
        {/* Mobile Sidebar Overlay */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-50 flex">
            {/* Backdrop */}
            <div 
              className="fixed inset-0 bg-black bg-opacity-50"
              onClick={() => setSidebarOpen(false)}
            />
            
            {/* Sidebar */}
            <div className="relative w-80 max-w-[85vw] bg-white border-r border-gray-200 overflow-y-auto">
              <LeftSidebar 
                activeProject={localActiveProject}
                setActiveProject={handleSetActiveProject}
                moderatorConfig={storeModeratorConfig}
                setModeratorConfig={handleSetModeratorConfig}
                onClose={() => setSidebarOpen(false)}
                isMobile={true}
              />
            </div>
          </div>
        )}

        {/* Mobile Content */}
        <div className="flex-1 overflow-hidden">
          {/* Chat Tab - Mobile */}
          {activeTab === 'chat' && (
            <div className="h-full bg-gray-50">
              <CenterColumn 
                activeProject={localActiveProject}
                moderatorConfig={storeModeratorConfig}
              />
            </div>
          )}

          {/* Projects Tab - Mobile */}
          {activeTab === 'projects' && (
            <div className="h-full bg-white overflow-y-auto">
              <LeftSidebar 
                activeProject={localActiveProject}
                setActiveProject={handleSetActiveProject}
                moderatorConfig={storeModeratorConfig}
                setModeratorConfig={handleSetModeratorConfig}
                isMobile={true}
                inlineMode={true}
              />
            </div>
          )}

          {/* Agents Tab - Mobile */}
          {activeTab === 'agents' && (
            <div className="h-full bg-white overflow-y-auto">
              <RightSidebar isMobile={true} />
            </div>
          )}
        </div>
      </div>

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
    </div>
  )
}

export default App
