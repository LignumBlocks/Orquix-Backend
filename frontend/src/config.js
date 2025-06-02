// Configuración de la aplicación
export const config = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  APP_NAME: import.meta.env.VITE_APP_NAME || 'Orquix',
  APP_VERSION: import.meta.env.VITE_APP_VERSION || '1.0.0',
  
  // Endpoints principales
  ENDPOINTS: {
    AUTH: '/api/v1/auth',
    PROJECTS: '/api/v1/projects',
    FEEDBACK: '/api/v1/feedback',
    HEALTH: '/api/v1/health',
  },
  
  // Configuración de desarrollo
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD,
}; 