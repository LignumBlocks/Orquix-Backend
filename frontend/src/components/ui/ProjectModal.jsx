import { useState } from 'react'
import { XIcon, PlusIcon, TrashIcon, DownloadIcon, RotateCcwIcon, ChevronDownIcon, ChevronRightIcon, EditIcon, SaveIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'

const ProjectModal = ({ project, onClose }) => {
  const [contextFilesExpanded, setContextFilesExpanded] = useState(true)
  const [backupsExpanded, setBackupsExpanded] = useState(true)
  const [expandedBackups, setExpandedBackups] = useState(new Set(['2024-01-15']))
  const [isEditingProject, setIsEditingProject] = useState(false)
  const [editData, setEditData] = useState({
    name: project?.name || '',
    description: project?.description || ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { updateProject, deleteProject, setActiveProject } = useAppStore()

  const contextFiles = [
    { id: 1, name: 'fintech_trends.pdf', size: '2.3 MB', type: 'PDF' },
    { id: 2, name: 'market_analysis.xlsx', size: '1.8 MB', type: 'Excel' },
    { id: 3, name: 'competitor_report.docx', size: '945 KB', type: 'Word' },
    { id: 4, name: 'user_interviews.txt', size: '234 KB', type: 'Text' },
    { id: 5, name: 'regulatory_changes.pdf', size: '1.2 MB', type: 'PDF' }
  ]

  const conversationBackups = [
    { 
      id: 1, 
      date: '2024-01-15', 
      size: '2.1 MB',
      messages: 42
    },
    { 
      id: 2, 
      date: '2024-01-12', 
      size: '1.8 MB',
      messages: 35
    }
  ]

  const toggleBackupExpansion = (date) => {
    const newExpanded = new Set(expandedBackups)
    if (newExpanded.has(date)) {
      newExpanded.delete(date)
    } else {
      newExpanded.add(date)
    }
    setExpandedBackups(newExpanded)
  }

  const getFileIcon = (type) => {
    switch (type) {
      case 'PDF':
        return '📄'
      case 'Excel':
        return '📊'
      case 'Word':
        return '📝'
      case 'Text':
        return '📋'
      default:
        return '📁'
    }
  }

  const handleEditProject = async () => {
    if (!editData.name.trim()) return

    setIsSubmitting(true)
    try {
      await updateProject(project.id, {
        name: editData.name.trim(),
        description: editData.description.trim()
      })
      
      if (window.showToast) {
        window.showToast.success('Proyecto actualizado exitosamente')
      }
      
      setIsEditingProject(false)
    } catch (error) {
      console.error('Error updating project:', error)
      if (window.showToast) {
        window.showToast.error('Error al actualizar el proyecto')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteProject = async () => {
    if (!project?.id) return

    const confirmDelete = window.confirm(
      `¿Estás seguro que quieres eliminar el proyecto "${project.name}"?\n\nEsta acción no se puede deshacer y se perderán todas las conversaciones asociadas.`
    )

    if (!confirmDelete) return

    setIsSubmitting(true)
    try {
      await deleteProject(project.id)
      
      if (window.showToast) {
        window.showToast.success(`Proyecto "${project.name}" eliminado exitosamente`)
      }
      
      onClose() // Cerrar modal después de eliminar
    } catch (error) {
      console.error('Error deleting project:', error)
      if (window.showToast) {
        window.showToast.error('Error al eliminar el proyecto')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancelEdit = () => {
    setEditData({
      name: project?.name || '',
      description: project?.description || ''
    })
    setIsEditingProject(false)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 modal-overlay flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-96 max-h-[80vh] overflow-hidden hover-lift">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-200">
          <div className="flex-1">
            {!isEditingProject ? (
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">{project?.name}</h3>
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => setIsEditingProject(true)}
                    className="text-blue-600 hover:text-blue-800 transition-colors"
                    title="Editar proyecto"
                  >
                    <EditIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={handleDeleteProject}
                    disabled={isSubmitting}
                    className="text-red-600 hover:text-red-800 transition-colors disabled:opacity-50"
                    title="Eliminar proyecto"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <input
                  type="text"
                  value={editData.name}
                  onChange={(e) => setEditData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full text-lg font-semibold bg-gray-50 border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Nombre del proyecto"
                />
                <textarea
                  value={editData.description}
                  onChange={(e) => setEditData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full text-sm bg-gray-50 border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  rows="2"
                  placeholder="Descripción del proyecto"
                />
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleEditProject}
                    disabled={!editData.name.trim() || isSubmitting}
                    className="flex items-center text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    <SaveIcon className="w-3 h-3 mr-1" />
                    Guardar
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    disabled={isSubmitting}
                    className="text-sm bg-gray-200 text-gray-700 px-3 py-1 rounded hover:bg-gray-300 transition-colors disabled:opacity-50"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </div>
          <button 
            onClick={onClose}
            disabled={isSubmitting}
            className="text-gray-400 hover:text-gray-600 smooth-transition disabled:opacity-50 ml-2"
          >
            <XIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Project Info */}
        {!isEditingProject && project?.description && (
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <p className="text-sm text-gray-600">{project.description}</p>
          </div>
        )}

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(80vh-80px)] custom-scrollbar">
          {/* Context Files Section */}
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <button
                onClick={() => setContextFilesExpanded(!contextFilesExpanded)}
                className="flex items-center text-sm font-medium text-gray-700 smooth-transition hover:text-gray-900"
              >
                {contextFilesExpanded ? (
                  <ChevronDownIcon className="w-4 h-4 mr-1" />
                ) : (
                  <ChevronRightIcon className="w-4 h-4 mr-1" />
                )}
                Context Files
              </button>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                {contextFiles.length} files loaded
              </span>
            </div>

            {contextFilesExpanded && (
              <div className="space-y-2">
                {contextFiles.map((file) => (
                  <div key={file.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded border border-gray-200 smooth-transition">
                    <div className="flex items-center flex-1 min-w-0">
                      <span className="text-lg mr-2">{getFileIcon(file.type)}</span>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {file.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {file.type} • {file.size}
                        </div>
                      </div>
                    </div>
                    <button className="ml-2 text-red-600 hover:text-red-800 text-xs font-medium smooth-transition hover:bg-red-50 px-2 py-1 rounded">
                      Delete
                    </button>
                  </div>
                ))}
                
                <button className="flex items-center justify-center w-full p-2 border-2 border-dashed border-gray-300 hover:border-blue-400 rounded text-blue-600 hover:text-blue-700 smooth-transition hover:bg-blue-50">
                  <PlusIcon className="w-4 h-4 mr-1" />
                  <span className="text-sm font-medium">Add file</span>
                </button>
              </div>
            )}
          </div>

          {/* Conversation Backups Section */}
          <div className="p-4">
            <button
              onClick={() => setBackupsExpanded(!backupsExpanded)}
              className="flex items-center text-sm font-medium text-gray-700 mb-3 smooth-transition hover:text-gray-900"
            >
              {backupsExpanded ? (
                <ChevronDownIcon className="w-4 h-4 mr-1" />
              ) : (
                <ChevronRightIcon className="w-4 h-4 mr-1" />
              )}
              Conversation Backups
            </button>

            {backupsExpanded && (
              <div className="space-y-2">
                {conversationBackups.map((backup) => (
                  <div key={backup.id} className="border border-gray-200 rounded smooth-transition hover:border-gray-300">
                    <button
                      onClick={() => toggleBackupExpansion(backup.date)}
                      className="w-full flex items-center justify-between p-3 hover:bg-gray-50 smooth-transition"
                    >
                      <div className="flex items-center">
                        {expandedBackups.has(backup.date) ? (
                          <ChevronDownIcon className="w-4 h-4 mr-2 text-gray-400" />
                        ) : (
                          <ChevronRightIcon className="w-4 h-4 mr-2 text-gray-400" />
                        )}
                        <div className="text-left">
                          <div className="text-sm font-medium text-gray-900">{backup.date}</div>
                          <div className="text-xs text-gray-500">{backup.messages} messages</div>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {backup.size}
                      </div>
                    </button>
                    
                    {expandedBackups.has(backup.date) && (
                      <div className="px-3 pb-3 flex space-x-2 border-t border-gray-100">
                        <button className="flex items-center text-xs text-blue-600 hover:text-blue-800 font-medium smooth-transition hover:bg-blue-50 px-2 py-1 rounded">
                          <RotateCcwIcon className="w-3 h-3 mr-1" />
                          Restore
                        </button>
                        <button className="flex items-center text-xs text-blue-600 hover:text-blue-800 font-medium smooth-transition hover:bg-blue-50 px-2 py-1 rounded">
                          <DownloadIcon className="w-3 h-3 mr-1" />
                          Download
                        </button>
                        <button className="flex items-center text-xs text-red-600 hover:text-red-800 font-medium smooth-transition hover:bg-red-50 px-2 py-1 rounded">
                          <TrashIcon className="w-3 h-3 mr-1" />
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProjectModal 