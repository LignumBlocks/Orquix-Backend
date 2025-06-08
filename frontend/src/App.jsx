import { useState, useEffect } from 'react'
import { config } from './config'
import LeftSidebar from './components/layout/LeftSidebar'
import CenterColumn from './components/layout/CenterColumn'
import RightSidebar from './components/layout/RightSidebar'
import { ToastContainer, useToast } from './components/ui/Toast'
import useAppStore from './store/useAppStore'
import { initMockAuthIfNeeded, mockAuth } from './utils/mockAuth'

function App() {
  const [localActiveProject, setLocalActiveProject] = useState(null)
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
    // Configurar autenticación mock para desarrollo
    const authSetup = initMockAuthIfNeeded()
    
    if (authSetup || mockAuth.hasMockAuth()) {
      // Configurar usuario mock en el store
      setUser(mockAuth.getMockUser())
      setAuthToken(mockAuth.MOCK_TOKEN)
    }
    
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

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Left Sidebar - 15% */}
      <div className="w-[15%] bg-white border-r border-gray-200 overflow-y-auto">
        <LeftSidebar 
          activeProject={localActiveProject}
          setActiveProject={handleSetActiveProject}
          moderatorConfig={storeModeratorConfig}
          setModeratorConfig={handleSetModeratorConfig}
        />
      </div>

      {/* Center Column - 60% */}
      <div className="w-[60%] bg-gray-50 flex flex-col">
        <CenterColumn 
          activeProject={localActiveProject}
          moderatorConfig={storeModeratorConfig}
        />
      </div>

      {/* Right Sidebar - 25% */}
      <div className="w-[25%] bg-white border-l border-gray-200 overflow-y-auto">
        <RightSidebar />
      </div>

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
    </div>
  )
}

export default App
