import { useState, useEffect } from 'react'
import { CheckCircleIcon, XCircleIcon, Info, XIcon } from 'lucide-react'

const Toast = ({ message, type = 'info', duration = 4000, onClose }) => {
  const [isVisible, setIsVisible] = useState(true)
  const [isLeaving, setIsLeaving] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      handleClose()
    }, duration)

    return () => clearTimeout(timer)
  }, [duration])

  const handleClose = () => {
    setIsLeaving(true)
    setTimeout(() => {
      setIsVisible(false)
      onClose()
    }, 300) // Duración de la animación de salida
  }

  if (!isVisible) return null

  const getToastStyles = () => {
    const baseStyles = `fixed top-4 right-4 z-50 min-w-80 max-w-md bg-white border-l-4 rounded-lg shadow-lg p-4 transform transition-all duration-300 ease-in-out`
    
    if (isLeaving) {
      return `${baseStyles} translate-x-full opacity-0`
    }
    
    switch (type) {
      case 'success':
        return `${baseStyles} border-green-500 translate-x-0 opacity-100`
      case 'error':
        return `${baseStyles} border-red-500 translate-x-0 opacity-100`
      case 'warning':
        return `${baseStyles} border-yellow-500 translate-x-0 opacity-100`
      default:
        return `${baseStyles} border-blue-500 translate-x-0 opacity-100`
    }
  }

  const getIcon = () => {
    const iconClass = "w-5 h-5 mr-3 flex-shrink-0"
    
    switch (type) {
      case 'success':
        return <CheckCircleIcon className={`${iconClass} text-green-500`} />
      case 'error':
        return <XCircleIcon className={`${iconClass} text-red-500`} />
      case 'warning':
        return <Info className={`${iconClass} text-yellow-500`} />
      default:
        return <Info className={`${iconClass} text-blue-500`} />
    }
  }

  const getTextColor = () => {
    switch (type) {
      case 'success':
        return 'text-green-800'
      case 'error':
        return 'text-red-800'
      case 'warning':
        return 'text-yellow-800'
      default:
        return 'text-blue-800'
    }
  }

  return (
    <div className={getToastStyles()}>
      <div className="flex items-start">
        {getIcon()}
        <div className="flex-1">
          <p className={`text-sm font-medium ${getTextColor()}`}>
            {message}
          </p>
        </div>
        <button
          onClick={handleClose}
          className="ml-4 text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
        >
          <XIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}

// Hook para manejar las notificaciones
export const useToast = () => {
  const [toasts, setToasts] = useState([])

  const showToast = (message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random()
    const newToast = { id, message, type, duration }
    
    setToasts(prev => [...prev, newToast])
  }

  const removeToast = (id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }

  const success = (message, duration) => showToast(message, 'success', duration)
  const error = (message, duration) => showToast(message, 'error', duration)
  const warning = (message, duration) => showToast(message, 'warning', duration)
  const info = (message, duration) => showToast(message, 'info', duration)

  return {
    toasts,
    showToast,
    removeToast,
    success,
    error,
    warning,
    info
  }
}

// Componente contenedor para renderizar todas las notificaciones
export const ToastContainer = ({ toasts, onRemoveToast }) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => onRemoveToast(toast.id)}
        />
      ))}
    </div>
  )
}

export default Toast 