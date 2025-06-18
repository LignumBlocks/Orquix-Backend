import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { initMockAuthIfNeeded } from './utils/mockAuth'

// Inicializar autenticación mock en desarrollo
initMockAuthIfNeeded()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
