import { useState } from 'react'
import { XIcon, FolderPlusIcon, LoaderIcon, SettingsIcon, InfoIcon } from 'lucide-react'
import useAppStore from '../../store/useAppStore'

const CreateProjectModal = ({ isOpen, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    moderator_personality: 'Analytical',
    moderator_temperature: 0.7,
    moderator_length_penalty: 0.5
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState({})
  const [showAdvanced, setShowAdvanced] = useState(false)

  const { createProject } = useAppStore()

  // Opciones de personalidad del moderador
  const personalityOptions = [
    { value: 'Analytical', label: 'Analítico', description: 'Enfoque detallado y metódico' },
    { value: 'Creative', label: 'Creativo', description: 'Perspectiva innovadora y fuera de lo común' },
    { value: 'Balanced', label: 'Equilibrado', description: 'Combinación de análisis y creatividad' },
    { value: 'Critical', label: 'Crítico', description: 'Evaluación rigurosa y cuestionamiento' },
    { value: 'Supportive', label: 'Colaborativo', description: 'Enfoque empático y constructivo' }
  ]

  // Validación del formulario
  const validateForm = () => {
    const newErrors = {}

    if (!formData.name.trim()) {
      newErrors.name = 'El nombre del proyecto es requerido'
    } else if (formData.name.trim().length < 3) {
      newErrors.name = 'El nombre debe tener al menos 3 caracteres'
    } else if (formData.name.trim().length > 100) {
      newErrors.name = 'El nombre no puede exceder 100 caracteres'
    }

    if (!formData.description.trim()) {
      newErrors.description = 'La descripción es requerida'
    } else if (formData.description.trim().length < 10) {
      newErrors.description = 'La descripción debe tener al menos 10 caracteres'
    } else if (formData.description.trim().length > 500) {
      newErrors.description = 'La descripción no puede exceder 500 caracteres'
    }

    if (formData.moderator_temperature < 0 || formData.moderator_temperature > 2) {
      newErrors.moderator_temperature = 'La temperatura debe estar entre 0 y 2'
    }

    if (formData.moderator_length_penalty < 0 || formData.moderator_length_penalty > 1) {
      newErrors.moderator_length_penalty = 'La penalización de longitud debe estar entre 0 y 1'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Manejar cambios en el formulario
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    
    // Limpiar error específico cuando el usuario corrige
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  // Enviar formulario
  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)
    
    try {
      const projectData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        moderator_personality: formData.moderator_personality,
        moderator_temperature: parseFloat(formData.moderator_temperature),
        moderator_length_penalty: parseFloat(formData.moderator_length_penalty)
      }

      await createProject(projectData)

      // Resetear formulario y cerrar modal
      setFormData({
        name: '',
        description: '',
        moderator_personality: 'Analytical',
        moderator_temperature: 0.7,
        moderator_length_penalty: 0.5
      })
      setErrors({})
      setShowAdvanced(false)
      onClose()
      
      // Mostrar notificación de éxito
      if (window.showToast) {
        window.showToast.success(`Proyecto "${projectData.name}" creado exitosamente`)
      }
      
    } catch (error) {
      console.error('❌ Error creando proyecto:', error)
      
      // Mostrar notificación de error específico
      const errorMessage = error.response?.data?.detail || 'Error al crear el proyecto. Inténtalo de nuevo.'
      
      if (window.showToast) {
        window.showToast.error(errorMessage)
      }
      
      setErrors({ submit: errorMessage })
    } finally {
      setIsSubmitting(false)
    }
  }

  // Cerrar modal
  const handleClose = () => {
    if (!isSubmitting) {
      setFormData({
        name: '',
        description: '',
        moderator_personality: 'Analytical',
        moderator_temperature: 0.7,
        moderator_length_penalty: 0.5
      })
      setErrors({})
      setShowAdvanced(false)
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center">
            <FolderPlusIcon className="w-6 h-6 text-blue-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">Crear Nuevo Proyecto</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          >
            <XIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Nombre del proyecto */}
          <div>
            <label htmlFor="project-name" className="block text-sm font-medium text-gray-700 mb-2">
              Nombre del Proyecto *
            </label>
            <input
              id="project-name"
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors text-gray-900 placeholder-gray-500 ${
                errors.name ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="Ej: Análisis de Mercado 2024"
              disabled={isSubmitting}
              maxLength={100}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">{formData.name.length}/100 caracteres</p>
          </div>

          {/* Descripción */}
          <div>
            <label htmlFor="project-description" className="block text-sm font-medium text-gray-700 mb-2">
              Descripción *
            </label>
            <textarea
              id="project-description"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              rows={3}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors resize-none text-gray-900 placeholder-gray-500 ${
                errors.description ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              placeholder="Describe el propósito y objetivos de este proyecto..."
              disabled={isSubmitting}
              maxLength={500}
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600">{errors.description}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">{formData.description.length}/500 caracteres</p>
          </div>

          {/* Personalidad del Moderador */}
          <div>
            <label htmlFor="moderator-personality" className="block text-sm font-medium text-gray-700 mb-2">
              Personalidad del Moderador
            </label>
            <select
              id="moderator-personality"
              value={formData.moderator_personality}
              onChange={(e) => handleChange('moderator_personality', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
              disabled={isSubmitting}
            >
              {personalityOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label} - {option.description}
                </option>
              ))}
            </select>
          </div>

          {/* Configuración Avanzada */}
          <div className="border-t border-gray-200 pt-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors"
            >
              <SettingsIcon className="w-4 h-4 mr-2" />
              Configuración Avanzada del Moderador
              <span className="ml-2 text-xs">
                {showAdvanced ? '(Ocultar)' : '(Mostrar)'}
              </span>
            </button>

            {showAdvanced && (
              <div className="mt-4 space-y-4 bg-gray-50 p-4 rounded-md">
                {/* Temperatura */}
                <div>
                  <div className="flex items-center mb-2">
                    <label htmlFor="moderator-temperature" className="block text-sm font-medium text-gray-700">
                      Temperatura ({formData.moderator_temperature})
                    </label>
                    <div className="ml-2 group relative">
                      <InfoIcon className="w-4 h-4 text-gray-400 cursor-help" />
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-black text-white text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity w-48 z-10">
                        Controla la creatividad. 0 = más conservador, 2 = más creativo
                      </div>
                    </div>
                  </div>
                  <input
                    id="moderator-temperature"
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={formData.moderator_temperature}
                    onChange={(e) => handleChange('moderator_temperature', parseFloat(e.target.value))}
                    className="w-full"
                    disabled={isSubmitting}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Conservador (0)</span>
                    <span>Equilibrado (1)</span>
                    <span>Creativo (2)</span>
                  </div>
                  {errors.moderator_temperature && (
                    <p className="mt-1 text-sm text-red-600">{errors.moderator_temperature}</p>
                  )}
                </div>

                {/* Length Penalty */}
                <div>
                  <div className="flex items-center mb-2">
                    <label htmlFor="moderator-length-penalty" className="block text-sm font-medium text-gray-700">
                      Penalización de Longitud ({formData.moderator_length_penalty})
                    </label>
                    <div className="ml-2 group relative">
                      <InfoIcon className="w-4 h-4 text-gray-400 cursor-help" />
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-black text-white text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity w-48 z-10">
                        Controla la longitud de respuestas. 0 = más cortas, 1 = más largas
                      </div>
                    </div>
                  </div>
                  <input
                    id="moderator-length-penalty"
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={formData.moderator_length_penalty}
                    onChange={(e) => handleChange('moderator_length_penalty', parseFloat(e.target.value))}
                    className="w-full"
                    disabled={isSubmitting}
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Cortas (0)</span>
                    <span>Moderadas (0.5)</span>
                    <span>Largas (1)</span>
                  </div>
                  {errors.moderator_length_penalty && (
                    <p className="mt-1 text-sm text-red-600">{errors.moderator_length_penalty}</p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Error de envío */}
          {errors.submit && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-sm text-red-600">{errors.submit}</p>
            </div>
          )}

          {/* Botones */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors disabled:opacity-50 flex items-center"
            >
              {isSubmitting ? (
                <>
                  <LoaderIcon className="w-4 h-4 mr-2 animate-spin" />
                  Creando...
                </>
              ) : (
                <>
                  <FolderPlusIcon className="w-4 h-4 mr-2" />
                  Crear Proyecto
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateProjectModal 