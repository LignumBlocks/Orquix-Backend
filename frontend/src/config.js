// Configuración de la aplicación
export const config = {
  // API Base URL dinámico para desarrollo y producción
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 
                (import.meta.env.PROD 
                  ? 'https://orquix-backend.onrender.com'  // URL de producción en Render
                  : 'http://localhost:8000'                // URL de desarrollo
                ),
    
  APP_NAME: import.meta.env.VITE_APP_NAME || 'Orquix',
  VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  
  // Configuraciones específicas del entorno
  ENVIRONMENT: import.meta.env.MODE,
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD,
  
  // Timeouts y límites
  API_TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT) || 60000, // 60 segundos para consultas de orquestación
  RETRY_ATTEMPTS: parseInt(import.meta.env.VITE_RETRY_ATTEMPTS) || 3,
  
  // Configuración de paginación
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  
  // Configuración del moderador
  MODERATOR: {
    DEFAULT_PERSONALITY: 'Analytical',
    DEFAULT_TEMPERATURE: 0.7,
    DEFAULT_LENGTH: 0.5,
    MIN_TEMPERATURE: 0.0,
    MAX_TEMPERATURE: 2.0,
    MIN_LENGTH: 0.0,
    MAX_LENGTH: 1.0
  },
  
  // Health check intervals
  AI_HEALTH_CHECK_INTERVAL: 30000, // 30 segundos
  SYSTEM_HEALTH_CHECK_INTERVAL: 60000, // 1 minuto
  
  // Configuración de autenticación mock para desarrollo
  ENABLE_MOCK_AUTH: import.meta.env.VITE_ENABLE_MOCK_AUTH === 'true' || import.meta.env.DEV,
  ENABLE_DEBUGGING: import.meta.env.VITE_ENABLE_DEBUGGING === 'true' || import.meta.env.DEV,
  
  // Endpoints principales
  ENDPOINTS: {
    AUTH: '/api/v1/auth',
    PROJECTS: '/api/v1/projects',
    FEEDBACK: '/api/v1/feedback',
    HEALTH: '/api/v1/health',
  },
}; 