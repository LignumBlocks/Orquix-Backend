// Configuración de la aplicación
export const config = {
  // Temporalmente usar URL completa para debugging
  API_BASE_URL: 'http://localhost:8000',
    
  APP_NAME: 'Orquix',
  VERSION: '1.0.0',
  
  // Configuraciones específicas del entorno
  ENVIRONMENT: import.meta.env.MODE,
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD,
  
  // Timeouts y límites
  API_TIMEOUT: 60000, // 60 segundos para consultas de orquestación
  RETRY_ATTEMPTS: 3,
  
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
  
  // Endpoints principales
  ENDPOINTS: {
    AUTH: '/api/v1/auth',
    PROJECTS: '/api/v1/projects',
    FEEDBACK: '/api/v1/feedback',
    HEALTH: '/api/v1/health',
  },
}; 