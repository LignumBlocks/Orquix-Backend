// Mock de autenticación para testing y desarrollo
export const mockAuth = {
  // Token mock para desarrollo
  MOCK_TOKEN: 'dev-mock-token-12345',
  
  // Configurar autenticación mock
  setupMockAuth() {
    // Solo en desarrollo
    if (import.meta.env.DEV) {
      localStorage.setItem('auth_token', this.MOCK_TOKEN)
      console.log('🔐 Mock auth configurado para desarrollo')
      return true
    }
    return false
  },

  // Verificar si tenemos autenticación mock
  hasMockAuth() {
    return localStorage.getItem('auth_token') === this.MOCK_TOKEN
  },

  // Limpiar autenticación mock
  clearMockAuth() {
    localStorage.removeItem('auth_token')
    console.log('🔐 Mock auth limpiado')
  },

  // Usuario mock
  getMockUser() {
    return {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'dev@orquix.com',
      name: 'Developer User',
      created_at: new Date().toISOString()
    }
  }
}

// Función de utilidad para inicializar en desarrollo
export const initMockAuthIfNeeded = () => {
  if (import.meta.env.DEV && !localStorage.getItem('auth_token')) {
    mockAuth.setupMockAuth()
    return true
  }
  return false
} 