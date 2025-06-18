import { useState, useEffect } from 'react'
import { ChevronDownIcon, ChevronRightIcon, PlusIcon, XIcon, LoaderIcon } from 'lucide-react'
import ProjectModal from '../ui/ProjectModal'
import CreateProjectModal from '../ui/CreateProjectModal'
import useAppStore from '../../store/useAppStore'

const LeftSidebar = ({ 
  activeProject,
  onClose,
  isMobile = false,
  inlineMode = false
}) => {
  const [projectsExpanded, setProjectsExpanded] = useState(true)
  const [sessionsExpanded, setSessionsExpanded] = useState(true)
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [selectedProjectForModal, setSelectedProjectForModal] = useState(null)
  const [showCreateProjectModal, setShowCreateProjectModal] = useState(false)

  // Zustand store
  const {
    projects = [],
    loadingProjects = false,
    conversations = [],
    loadProjects = () => {},
    setActiveProject: setStoreActiveProject = () => {},
    loadConversations = () => {}
  } = useAppStore()

  // Cargar proyectos al montar el componente
  useEffect(() => {
    if (typeof loadProjects === 'function') {
      loadProjects().catch(console.error)
    }
  }, [loadProjects])

  // Cargar conversaciones cuando cambie el proyecto activo
  useEffect(() => {
    if (activeProject?.id && typeof loadConversations === 'function') {
      loadConversations(activeProject.id).catch(console.error)
    }
  }, [activeProject?.id, loadConversations])

  const handleProjectClick = (project) => {
    if (project.id === activeProject?.id) {
      // Si es el mismo proyecto, abrir modal
      setSelectedProjectForModal(project)
      setShowProjectModal(true)
    } else {
      // Si es diferente, cambiar proyecto activo
      setStoreActiveProject(project)
    }
    
    // Cerrar sidebar en móvil después de seleccionar proyecto
    if (isMobile && onClose) {
      onClose()
    }
  }

  // Formatear conversaciones recientes para mostrar
  const recentSessions = (conversations || []).slice(0, 5).map(conv => ({
    id: conv.id,
    time: new Date(conv.createdAt || conv.created_at || Date.now()).toLocaleString('es-ES', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }),
    preview: (conv.question || conv.user_message || 'Sin contenido').length > 30 
      ? (conv.question || conv.user_message || 'Sin contenido').substring(0, 30) + '...' 
      : (conv.question || conv.user_message || 'Sin contenido')
  }))

  return (
    <div className={`${inlineMode ? 'p-4' : 'p-4 h-full'} custom-scrollbar`}>
      {/* Mobile Header */}
      {isMobile && onClose && (
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Control Panel</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>
      )}
      
      {/* Desktop Header */}
      {!isMobile && (
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Control Panel</h2>
      )}
      
      {/* Projects Section */}
      <div className="mb-6">
        <button
          onClick={() => setProjectsExpanded(!projectsExpanded)}
          className="flex items-center w-full text-left text-sm font-medium text-gray-700 mb-2 smooth-transition hover:text-gray-900"
        >
          {projectsExpanded ? (
            <ChevronDownIcon className="w-4 h-4 mr-1" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 mr-1" />
          )}
          Projects {loadingProjects && <LoaderIcon className="w-3 h-3 ml-2 animate-spin" />}
        </button>
        
        {projectsExpanded && (
          <div className="ml-5 space-y-1">
            {/* Loading State */}
            {loadingProjects && projects.length === 0 && (
              <div className="text-sm text-gray-500 py-2">
                Cargando proyectos...
              </div>
            )}

            {/* Projects List */}
            {projects.map((project) => (
              <button
                key={project.id}
                onClick={() => handleProjectClick(project)}
                className={`block w-full text-left text-sm py-1 px-2 rounded smooth-transition hover:bg-gray-100 ${
                  project.id === activeProject?.id ? 'text-blue-600 font-medium bg-blue-50' : 'text-gray-600'
                }`}
              >
                • {project.name}
                {project.id === activeProject?.id && (
                  <span className="text-xs text-blue-500 ml-1">(activo)</span>
                )}
              </button>
            ))}
            
            {/* No Projects State */}
            {!loadingProjects && projects.length === 0 && (
              <div className="text-sm text-gray-500 py-2">
                No hay proyectos. Crea uno para empezar.
              </div>
            )}

            {/* Create Project Button */}
            <button 
              onClick={() => setShowCreateProjectModal(true)}
              className="flex items-center text-sm text-blue-600 py-1 px-2 hover:bg-blue-50 rounded smooth-transition"
            >
              <PlusIcon className="w-4 h-4 mr-1" />
              Nuevo proyecto
            </button>
          </div>
        )}
      </div>

      {/* Recent Sessions Section */}
      <div className="mb-6">
        <button
          onClick={() => setSessionsExpanded(!sessionsExpanded)}
          className="flex items-center w-full text-left text-sm font-medium text-gray-700 mb-2 smooth-transition hover:text-gray-900"
        >
          {sessionsExpanded ? (
            <ChevronDownIcon className="w-4 h-4 mr-1" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 mr-1" />
          )}
          Recent Sessions
        </button>
        
        {sessionsExpanded && (
          <div className="ml-5 space-y-2">
            {recentSessions.map((session) => (
              <div key={session.id} className="text-sm">
                <div className="text-gray-400">{session.time}</div>
                <div className="text-gray-600">{session.preview}</div>
              </div>
            ))}
            {recentSessions.length === 0 && (
              <div className="text-sm text-gray-500">
                No hay sesiones recientes.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {showProjectModal && (
        <ProjectModal
          project={selectedProjectForModal}
          isOpen={showProjectModal}
          onClose={() => setShowProjectModal(false)}
        />
      )}
      
      {showCreateProjectModal && (
        <CreateProjectModal
          isOpen={showCreateProjectModal}
          onClose={() => setShowCreateProjectModal(false)}
        />
      )}
    </div>
  )
}

export default LeftSidebar 