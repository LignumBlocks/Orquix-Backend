import { useState, useEffect } from 'react'
import { ChevronDownIcon, ChevronRightIcon, PlusIcon, SettingsIcon, LoaderIcon } from 'lucide-react'
import ProjectModal from '../ui/ProjectModal'
import CreateProjectModal from '../ui/CreateProjectModal'
import useAppStore from '../../store/useAppStore'

const LeftSidebar = ({ activeProject, setActiveProject, moderatorConfig, setModeratorConfig }) => {
  const [projectsExpanded, setProjectsExpanded] = useState(true)
  const [moderatorExpanded, setModeratorExpanded] = useState(true)
  const [sessionsExpanded, setSessionsExpanded] = useState(true)
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [selectedProjectForModal, setSelectedProjectForModal] = useState(null)
  const [showCreateProjectModal, setShowCreateProjectModal] = useState(false)

  // Zustand store
  const {
    projects,
    loadingProjects,
    conversations,
    moderatorConfig: storeModeratorConfig,
    loadProjects,
    setActiveProject: setStoreActiveProject,
    updateModeratorConfig,
    loadConversations
  } = useAppStore()

  // Cargar proyectos al montar el componente
  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  // Cargar conversaciones cuando cambie el proyecto activo
  useEffect(() => {
    if (activeProject?.id) {
      loadConversations(activeProject.id)
    }
  }, [activeProject?.id, loadConversations])

  const handleProjectClick = (project) => {
    if (project.id === activeProject?.id) {
      // Si es el mismo proyecto, abrir modal
      setSelectedProjectForModal(project)
      setShowProjectModal(true)
    } else {
      // Si es diferente, cambiar proyecto activo
      setActiveProject(project)
      setStoreActiveProject(project)
    }
  }

  const handleModeratorConfigChange = (key, value) => {
    const updates = { [key]: value }
    setModeratorConfig({ ...moderatorConfig, ...updates })
    updateModeratorConfig(updates)
  }

  // Formatear conversaciones recientes para mostrar
  const recentSessions = conversations.slice(0, 5).map(conv => ({
    id: conv.id,
    time: new Date(conv.createdAt).toLocaleString('es-ES', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }),
    preview: conv.question.length > 30 
      ? conv.question.substring(0, 30) + '...' 
      : conv.question
  }))

  return (
    <div className="p-4 h-full custom-scrollbar">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Control Panel</h2>
      
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

      {/* Moderator Section */}
      <div className="mb-6">
        <button
          onClick={() => setModeratorExpanded(!moderatorExpanded)}
          className="flex items-center w-full text-left text-sm font-medium text-gray-700 mb-2 smooth-transition hover:text-gray-900"
        >
          {moderatorExpanded ? (
            <ChevronDownIcon className="w-4 h-4 mr-1" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 mr-1" />
          )}
          Moderator
        </button>
        
        {moderatorExpanded && (
          <div className="ml-5 space-y-3">
            {/* Personality */}
            <div>
              <label className="block text-xs text-gray-600 mb-1">Personality</label>
              <select 
                value={moderatorConfig.personality}
                onChange={(e) => handleModeratorConfigChange('personality', e.target.value)}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent smooth-transition"
              >
                <option value="Analytical">Analytical</option>
                <option value="Creative">Creative</option>
                <option value="Balanced">Balanced</option>
                <option value="Critical">Critical</option>
              </select>
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-xs text-gray-600 mb-1">
                Temperature: {moderatorConfig.temperature.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={moderatorConfig.temperature}
                onChange={(e) => handleModeratorConfigChange('temperature', parseFloat(e.target.value))}
                className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Conservador</span>
                <span>Creativo</span>
              </div>
            </div>

            {/* Length */}
            <div>
              <label className="block text-xs text-gray-600 mb-1">
                Length: {moderatorConfig.length.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={moderatorConfig.length}
                onChange={(e) => handleModeratorConfigChange('length', parseFloat(e.target.value))}
                className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>Conciso</span>
                <span>Detallado</span>
              </div>
            </div>

            {/* Live Preview */}
            <div className="bg-gray-50 rounded p-2 text-xs">
              <div className="text-gray-600 mb-1">Configuración actual:</div>
              <div className="text-gray-800">
                {moderatorConfig.personality} • 
                Temp: {moderatorConfig.temperature.toFixed(1)} • 
                Tokens: ~{Math.round(moderatorConfig.length * 4000) + 100}
              </div>
            </div>
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
          {recentSessions.length > 0 && (
            <span className="ml-2 bg-gray-200 text-gray-600 text-xs px-1.5 py-0.5 rounded-full">
              {recentSessions.length}
            </span>
          )}
        </button>
        
        {sessionsExpanded && (
          <div className="ml-5 space-y-2">
            {recentSessions.length === 0 ? (
              <div className="text-sm text-gray-500 py-2">
                {activeProject ? 'No hay conversaciones recientes' : 'Selecciona un proyecto'}
              </div>
            ) : (
              recentSessions.map((session) => (
                <button
                  key={session.id}
                  className="block w-full text-left p-2 hover:bg-gray-50 rounded smooth-transition"
                >
                  <div className="text-xs text-gray-500">{session.time}</div>
                  <div className="text-sm text-gray-700 truncate">{session.preview}</div>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {/* Project Modal */}
      {showProjectModal && (
        <ProjectModal 
          project={selectedProjectForModal}
          onClose={() => setShowProjectModal(false)}
        />
      )}

      {/* Create Project Modal */}
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