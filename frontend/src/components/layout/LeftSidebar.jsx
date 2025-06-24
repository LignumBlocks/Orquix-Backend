import { useState, useEffect } from 'react'
import { ChevronDownIcon, ChevronRightIcon, PlusIcon, XIcon, MessageSquareIcon, TrashIcon, LoaderIcon } from 'lucide-react'
import ProjectModal from '../ui/ProjectModal'
import CreateProjectModal from '../ui/CreateProjectModal'
import ConfirmDialog from '../ui/ConfirmDialog'
import useAppStore from '../../store/useAppStore'

const LeftSidebar = ({ 
  activeProject,
  onClose,
  isMobile = false,
  inlineMode = false
}) => {
  const [projectsExpanded, setProjectsExpanded] = useState(true)
  const [expandedProjects, setExpandedProjects] = useState(new Set()) // Proyectos con chats expandidos
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [selectedProjectForModal, setSelectedProjectForModal] = useState(null)
  const [showCreateProjectModal, setShowCreateProjectModal] = useState(false)
  const [showCreateChatModal, setShowCreateChatModal] = useState(false)
  const [selectedProjectForChat, setSelectedProjectForChat] = useState(null)
  const [newChatTitle, setNewChatTitle] = useState('')
  
  // Estados para confirmación de eliminación
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [chatToDelete, setChatToDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  // Zustand store
  const {
    projects = [],
    loadingProjects = false,
    projectChats = {},
    activeChat = null,
    loadingChats = false,
    loadProjects = () => {},
    loadProjectChats = () => {},
    createChat = () => {},
    deleteChat = () => {},
    setActiveProject = () => {},
    setActiveChat = () => {},
    selectChatAndLoadContext = () => {}
  } = useAppStore()

  // Cargar proyectos al montar el componente
  useEffect(() => {
    if (typeof loadProjects === 'function') {
      loadProjects().catch(console.error)
    }
  }, [loadProjects])

  // Cargar chats cuando se expande un proyecto
  const handleProjectExpand = async (project) => {
    const newExpanded = new Set(expandedProjects)
    
    if (expandedProjects.has(project.id)) {
      // Colapsar
      newExpanded.delete(project.id)
    } else {
      // Expandir y cargar chats
      newExpanded.add(project.id)
      if (typeof loadProjectChats === 'function') {
        await loadProjectChats(project.id).catch(console.error)
      }
    }
    
    setExpandedProjects(newExpanded)
  }

  const handleProjectClick = (project) => {
    if (project.id === activeProject?.id) {
      // Si es el mismo proyecto, abrir modal
      setSelectedProjectForModal(project)
      setShowProjectModal(true)
    } else {
      // Si es diferente, cambiar proyecto activo
      setActiveProject(project)
    }
    
    // Cerrar sidebar en móvil después de seleccionar proyecto
    if (isMobile && onClose) {
      onClose()
    }
  }

  const handleChatClick = async (chat) => {
    try {
      // Encontrar el proyecto al que pertenece este chat
      const chatProject = projects.find(p => {
        const chatsForProject = projectChats[p.id] || []
        return chatsForProject.some(c => c.id === chat.id)
      })
      
      console.log('🔍 Chat click - Proyecto encontrado:', {
        chatId: chat.id,
        chatTitle: chat.title,
        projectId: chatProject?.id,
        projectName: chatProject?.name,
        chatProjectId: chat.project_id
      })
      
      // Usar la nueva función que carga todo el contexto del chat
      await selectChatAndLoadContext(chat, chatProject)
      
      console.log('✅ Chat seleccionado y contexto cargado:', {
        chatId: chat.id,
        chatTitle: chat.title
      })
    } catch (error) {
      console.error('❌ Error seleccionando chat:', error)
      // Fallback: al menos seleccionar el chat
      setActiveChat(chat)
    }
    
    // Cerrar sidebar en móvil después de seleccionar chat
    if (isMobile && onClose) {
      onClose()
    }
  }

  const handleCreateChat = async () => {
    if (!newChatTitle.trim() || !selectedProjectForChat) return
    
    try {
      await createChat(selectedProjectForChat.id, newChatTitle.trim())
      setShowCreateChatModal(false)
      setNewChatTitle('')
      setSelectedProjectForChat(null)
    } catch (error) {
      console.error('Error creating chat:', error)
    }
  }

  const handleDeleteChatClick = (chatId, projectId, chatTitle, e) => {
    e.stopPropagation() // Evitar que se seleccione el chat al hacer click en eliminar
    
    setChatToDelete({ chatId, projectId, chatTitle })
    setShowDeleteConfirm(true)
  }

  const confirmDeleteChat = async () => {
    if (!chatToDelete) return
    
    setIsDeleting(true)
    try {
      await deleteChat(chatToDelete.chatId, chatToDelete.projectId)
      setShowDeleteConfirm(false)
      setChatToDelete(null)
    } catch (error) {
      console.error('Error deleting chat:', error)
      // El error se mostrará en el store, no necesitamos manejarlo aquí
    } finally {
      setIsDeleting(false)
    }
  }

  const cancelDeleteChat = () => {
    setShowDeleteConfirm(false)
    setChatToDelete(null)
  }

  const openCreateChatModal = (project, e) => {
    e.stopPropagation() // Evitar expandir/colapsar el proyecto
    setSelectedProjectForChat(project)
    setShowCreateChatModal(true)
  }

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
          <div className="ml-3 space-y-1">
            {/* Loading State */}
            {loadingProjects && projects.length === 0 && (
              <div className="text-sm text-gray-500 py-2">
                Cargando proyectos...
              </div>
            )}

            {/* Projects List */}
            {projects.map((project) => (
              <div key={project.id} className="select-none">
                {/* Project Header */}
                <div className="flex items-center">
                  <button
                    onClick={() => handleProjectExpand(project)}
                    className="p-1 hover:bg-gray-100 rounded transition-colors mr-1"
                  >
                    {expandedProjects.has(project.id) ? (
                      <ChevronDownIcon className="w-3 h-3 text-gray-500" />
                    ) : (
                      <ChevronRightIcon className="w-3 h-3 text-gray-500" />
                    )}
                  </button>
                  
                  <button
                    onClick={() => handleProjectClick(project)}
                    className={`flex-1 text-left text-sm py-1 px-2 rounded smooth-transition hover:bg-gray-100 ${
                      project.id === activeProject?.id ? 'text-blue-600 font-medium bg-blue-50' : 'text-gray-600'
                    }`}
                  >
                    {project.name}
                    {project.id === activeProject?.id && (
                      <span className="text-xs text-blue-500 ml-1">(activo)</span>
                    )}
                  </button>
                  
                  <button
                    onClick={(e) => openCreateChatModal(project, e)}
                    className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors ml-1"
                    title="Crear nuevo chat"
                  >
                    <PlusIcon className="w-3 h-3" />
                  </button>
                </div>

                {/* Project Chats */}
                {expandedProjects.has(project.id) && (
                  <div className="ml-6 mt-1 space-y-1">
                    {loadingChats && (
                      <div className="text-xs text-gray-500 py-1 flex items-center">
                        <LoaderIcon className="w-3 h-3 mr-1 animate-spin" />
                        Cargando chats...
                      </div>
                    )}
                    
                    {(projectChats[project.id] || []).map((chat) => (
                      <div
                        key={chat.id}
                        className="flex items-center group"
                      >
                        <button
                          onClick={() => handleChatClick(chat)}
                          className={`flex-1 flex items-center text-xs py-1 px-2 rounded smooth-transition hover:bg-gray-100 ${
                            activeChat?.id === chat.id ? 'text-blue-600 font-medium bg-blue-50' : 'text-gray-500'
                          }`}
                        >
                          <MessageSquareIcon className="w-3 h-3 mr-1" />
                          <span className="truncate">{chat.title}</span>
                        </button>
                        
                        <button
                          onClick={(e) => handleDeleteChatClick(chat.id, project.id, chat.title, e)}
                          className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-all ml-1"
                          title="Eliminar chat"
                        >
                          <TrashIcon className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                    
                    {!loadingChats && (projectChats[project.id] || []).length === 0 && (
                      <div className="text-xs text-gray-400 py-1 px-2">
                        No hay chats. Haz click en + para crear uno.
                      </div>
                    )}
                  </div>
                )}
              </div>
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

      {/* Create Chat Modal */}
      {showCreateChatModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-[90vw]">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Crear Nuevo Chat
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Proyecto: <strong>{selectedProjectForChat?.name}</strong>
            </p>
            
            <input
              type="text"
              value={newChatTitle}
              onChange={(e) => setNewChatTitle(e.target.value)}
              placeholder="Nombre del chat..."
              className="w-full p-3 border text-gray-900 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4"
              autoFocus
              onKeyPress={(e) => e.key === 'Enter' && handleCreateChat()}
            />
            
            <div className="flex space-x-3">
              <button
                onClick={handleCreateChat}
                disabled={!newChatTitle.trim()}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Crear Chat
              </button>
              <button
                onClick={() => {
                  setShowCreateChatModal(false)
                  setNewChatTitle('')
                  setSelectedProjectForChat(null)
                }}
                className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={cancelDeleteChat}
        onConfirm={confirmDeleteChat}
        title="Eliminar Chat"
        message={
          chatToDelete 
            ? `¿Estás seguro de que quieres eliminar el chat "${chatToDelete.chatTitle}"? Esta acción no se puede deshacer y se perderán todas las conversaciones y sesiones asociadas.`
            : "¿Estás seguro de que quieres eliminar este chat?"
        }
        confirmText="Eliminar"
        cancelText="Cancelar"
        confirmButtonClass="bg-red-600 hover:bg-red-700 text-white"
        isDestructive={true}
        isLoading={isDeleting}
      />
    </div>
  )
}

export default LeftSidebar 