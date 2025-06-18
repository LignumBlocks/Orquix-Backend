#!/usr/bin/env python3
"""
🔍 SCRIPT DE DIAGNÓSTICO PARA TIMEOUT EN CONTEXT-CHAT
====================================================

Este script envía mensajes uno por uno para identificar exactamente
dónde se produce el timeout y por qué.
"""

import asyncio
import json
import time
from uuid import UUID

import httpx
from rich.console import Console
from rich.panel import Panel

# Configuración
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

console = Console()

class DiagnosticoTimeout:
    def __init__(self):
        self.session_id = None
        self.project_id = "c9cc165a-6fed-4134-bf20-0e5897e3b7c8"
        self.headers = {
            "Authorization": "Bearer dev-mock-token-12345",
            "Content-Type": "application/json"
        }
    
    async def probar_mensaje_individual(self, mensaje: str, timeout: int = 60):
        """Prueba un mensaje individual con diagnóstico detallado."""
        
        console.print(f"\n🧪 PROBANDO MENSAJE: {mensaje[:50]}...", style="bold cyan")
        console.print(f"⏱️ Timeout configurado: {timeout} segundos", style="yellow")
        
        request_data = {
            "user_message": mensaje,
            "session_id": str(self.session_id) if self.session_id else None
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                console.print("📤 Enviando request...", style="blue")
                
                response = await client.post(
                    f"{API_BASE}/context-chat/projects/{self.project_id}/context-chat",
                    json=request_data,
                    headers=self.headers
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                console.print(f"✅ RESPUESTA RECIBIDA en {duration:.2f} segundos", style="green")
                console.print(f"📊 Status Code: {response.status_code}", style="white")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Guardar session_id para siguientes mensajes
                    if not self.session_id:
                        self.session_id = UUID(data["session_id"])
                        console.print(f"🆔 Session ID guardado: {self.session_id}", style="cyan")
                    
                    # Mostrar respuesta resumida
                    panel = Panel(
                        f"Tipo: {data['message_type']}\n"
                        f"Elementos: {data['context_elements_count']}\n"
                        f"Respuesta: {data['ai_response'][:200]}..."
                    )
                    console.print(panel)
                    
                    return True
                else:
                    console.print(f"❌ Error: {response.status_code} - {response.text}", style="red")
                    return False
                    
        except httpx.ReadTimeout:
            end_time = time.time()
            duration = end_time - start_time
            console.print(f"⏱️ TIMEOUT después de {duration:.2f} segundos", style="red")
            return False
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            console.print(f"❌ ERROR después de {duration:.2f} segundos: {e}", style="red")
            return False
    
    async def diagnosticar_problema(self):
        """Ejecuta el diagnóstico completo."""
        
        console.print("🔍 DIAGNÓSTICO DE TIMEOUT EN CONTEXT-CHAT", style="bold red")
        console.print("=" * 60, style="bold")
        
        # Verificar backend
        console.print("\n1️⃣ Verificando backend...", style="bold")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API_BASE}/health/ai-providers")
                if response.status_code == 200:
                    console.print("✅ Backend funcionando", style="green")
                else:
                    console.print(f"❌ Backend error: {response.status_code}", style="red")
                    return
        except Exception as e:
            console.print(f"❌ No se puede conectar al backend: {e}", style="red")
            return
        
        # Probar mensajes progresivamente
        mensajes_prueba = [
            "Hola, necesito ayuda con mi startup",
            "Estamos en etapa de crecimiento",
            "Nuestro problema principal es la retención de usuarios",  # Este es el que falla
            "Las conversiones son bajas",
            "Operamos en 3 ciudades"
        ]
        
        console.print("\n2️⃣ Probando mensajes progresivamente...", style="bold")
        
        for i, mensaje in enumerate(mensajes_prueba, 1):
            console.print(f"\n--- MENSAJE {i}/{len(mensajes_prueba)} ---", style="bold white")
            
            exito = await self.probar_mensaje_individual(mensaje, timeout=90)
            
            if not exito:
                console.print(f"\n🚨 PROBLEMA IDENTIFICADO EN MENSAJE {i}", style="bold red")
                console.print(f"Mensaje problemático: {mensaje}", style="red")
                
                # Intentar con timeout más largo
                console.print("\n🔄 Reintentando con timeout de 180 segundos...", style="yellow")
                exito_retry = await self.probar_mensaje_individual(mensaje, timeout=180)
                
                if exito_retry:
                    console.print("✅ Funcionó con timeout más largo", style="green")
                    console.print("💡 Problema: El backend/API tarda mucho en responder", style="yellow")
                else:
                    console.print("❌ Sigue fallando incluso con timeout largo", style="red")
                    break
            
            # Pausa entre mensajes
            await asyncio.sleep(2)
        
        console.print("\n3️⃣ Diagnóstico completo", style="bold green")

async def main():
    """Función principal."""
    try:
        diagnostico = DiagnosticoTimeout()
        await diagnostico.diagnosticar_problema()
    except KeyboardInterrupt:
        console.print("\n⚠️ Diagnóstico interrumpido por el usuario", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Error fatal: {e}", style="red")

if __name__ == "__main__":
    asyncio.run(main()) 