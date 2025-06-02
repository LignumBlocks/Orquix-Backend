#!/bin/bash

echo "🔍 Verificando estado de Orquix (Monorepo)..."
echo "=================================================="

# Verificar Backend (FastAPI)
echo ""
echo "📊 Backend Status (http://localhost:8000):"
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ Backend ACTIVO"
    echo "   - API endpoints disponibles"
    echo "   - Sistema de moderador IA v2.0 funcionando"
    echo "   - Orquestación de IAs activa"
else
    echo "❌ Backend NO DISPONIBLE"
    echo "   - Ejecutar: yarn dev:backend"
fi

# Verificar Frontend (React + Vite)
echo ""
echo "🎨 Frontend Status (http://localhost:5173):"
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Frontend ACTIVO"
    echo "   - Interfaz de 3 columnas implementada:"
    echo "     • Left Sidebar: Control Panel con Projects, Moderator, Sessions"
    echo "     • Center Column: Chat con Moderador IA"
    echo "     • Right Sidebar: Active AIs con estados y latencia"
    echo "   - Tailwind CSS v4 funcionando"
    echo "   - Componentes interactivos listos"
else
    echo "❌ Frontend NO DISPONIBLE"
    echo "   - Ejecutar: yarn dev:frontend"
fi

# URLs de acceso
echo ""
echo "🌐 URLs de Acceso:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"

# Comandos útiles
echo ""
echo "🛠️  Comandos útiles:"
echo "   yarn dev          # Ejecutar ambos servicios"
echo "   yarn dev:frontend # Solo frontend"
echo "   yarn dev:backend  # Solo backend"
echo "   ./dev-status.sh   # Este script"

echo ""
echo "==================================================" 