#!/usr/bin/env python3
"""
🧪 PRUEBA COMPLETA DEL FLUJO DE CONSTRUCCIÓN DE CONTEXTO

Este script demuestra el nuevo flujo simplificado:
1. Usuario inicia construcción de contexto
2. Conversación fluida con GPT-3.5
3. Acumulación progresiva de contexto
4. Finalización y envío a IAs principales

Muestra todos los prompts, respuestas y decisiones del sistema.
"""

import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID, uuid4

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich import print as rprint

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Rich console para output bonito
console = Console()

class ContextBuilderTester:
    """Tester para el flujo de construcción de contexto."""
    
    def __init__(self):
        self.session_id = None
        self.project_id = "c9cc165a-6fed-4134-bf20-0e5897e3b7c8"  # Proyecto "Caldosa" existente
        self.headers = {
            "Authorization": "Bearer dev-mock-token-12345",
            "Content-Type": "application/json"
        }
    
    async def run_complete_test(self):
        """Ejecuta la prueba completa del flujo."""
        console.print("\n" + "="*80)
        console.print("🧪 PRUEBA COMPLETA DEL FLUJO DE CONSTRUCCIÓN DE CONTEXTO", style="bold blue")
        console.print("="*80 + "\n")
        
        try:
            # 1. Verificar que el backend está funcionando
            await self.check_backend_health()
            
            # 2. Simular conversación de construcción de contexto
            await self.simulate_context_building_conversation()
            
            # 3. Mostrar contexto final acumulado
            await self.show_final_context()
            
            # 4. Simular finalización y envío a IAs
            await self.simulate_finalization()
            
            console.print("\n✅ PRUEBA COMPLETADA EXITOSAMENTE", style="bold green")
            
        except Exception as e:
            console.print(f"\n❌ ERROR EN LA PRUEBA: {e}", style="bold red")
            raise
    
    async def check_backend_health(self):
        """Verifica que el backend esté funcionando."""
        console.print("🏥 Verificando salud del backend...", style="yellow")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health/ai-providers")
            
            if response.status_code == 200:
                console.print("✅ Backend funcionando correctamente", style="green")
            else:
                raise Exception(f"Backend no disponible: {response.status_code}")
    
    async def simulate_context_building_conversation(self):
        """Simula una conversación completa de construcción de contexto."""
        console.print("\n💬 INICIANDO CONVERSACIÓN DE CONSTRUCCIÓN DE CONTEXTO", style="bold cyan")
        
        # Mensajes de prueba que simulan un usuario real
        messages = [
            "Hola, necesito ayuda con mi startup de delivery de comida",
            "Estamos en etapa de crecimiento, tenemos 1000 usuarios activos",
            "Nuestro problema principal es la retención de usuarios",
            "Las conversiones del primer pedido al segundo son muy bajas, solo 30%",
            "Operamos en 3 ciudades: Madrid, Barcelona y Valencia"
        ]
        
        for i, message in enumerate(messages, 1):
            console.print(f"\n📝 MENSAJE {i}/5", style="bold white")
            await self.send_context_message(message, i)
            
            # Pausa dramática para ver el proceso
            await asyncio.sleep(1)
    
    async def send_context_message(self, user_message: str, step: int):
        """Envía un mensaje al endpoint de construcción de contexto."""
        
        # Mostrar mensaje del usuario
        user_panel = Panel(
            user_message,
            title="👤 USUARIO",
            border_style="blue"
        )
        console.print(user_panel)
        
        # Preparar request
        request_data = {
            "user_message": user_message,
            "session_id": str(self.session_id) if self.session_id else None
        }
        
        # Mostrar request
        self.show_request_details(request_data)
        
        # Enviar request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/context-chat/projects/{self.project_id}/context-chat",
                json=request_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Guardar session_id para siguientes mensajes
                if not self.session_id:
                    self.session_id = UUID(response_data["session_id"])
                
                # Mostrar respuesta detallada
                await self.show_ai_response_details(response_data, step)
                
            else:
                console.print(f"❌ Error: {response.status_code} - {response.text}", style="red")
                raise Exception(f"Error en API: {response.status_code}")
    
    def show_request_details(self, request_data):
        """Muestra los detalles del request enviado."""
        request_json = json.dumps(request_data, indent=2, ensure_ascii=False)
        syntax = Syntax(request_json, "json", theme="monokai", line_numbers=True)
        
        request_panel = Panel(
            syntax,
            title="📤 REQUEST A LA API",
            border_style="yellow"
        )
        console.print(request_panel)
    
    async def show_ai_response_details(self, response_data, step):
        """Muestra los detalles de la respuesta de la IA."""
        
        # Respuesta de la IA
        ai_panel = Panel(
            response_data["ai_response"],
            title="🤖 RESPUESTA DE GPT-3.5",
            border_style="green"
        )
        console.print(ai_panel)
        
        # Crear tabla con metadatos
        table = Table(title=f"📊 METADATOS DEL PASO {step}")
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")
        
        table.add_row("Tipo de Mensaje", response_data["message_type"])
        table.add_row("Elementos de Contexto", str(response_data["context_elements_count"]))
        table.add_row("ID de Sesión", str(response_data["session_id"]))
        
        console.print(table)
        
        # Mostrar sugerencias si las hay
        if response_data.get("suggestions"):
            suggestions_text = "\n".join([f"• {s}" for s in response_data["suggestions"]])
            suggestions_panel = Panel(
                suggestions_text,
                title="💡 SUGERENCIAS",
                border_style="magenta"
            )
            console.print(suggestions_panel)
        
        # Mostrar contexto acumulado
        if response_data.get("accumulated_context"):
            context_panel = Panel(
                response_data["accumulated_context"],
                title="📝 CONTEXTO ACUMULADO",
                border_style="cyan"
            )
            console.print(context_panel)
        
        # Mostrar respuesta JSON completa
        response_json = json.dumps(response_data, indent=2, ensure_ascii=False)
        syntax = Syntax(response_json, "json", theme="monokai", line_numbers=True)
        
        full_response_panel = Panel(
            syntax,
            title="📥 RESPUESTA COMPLETA JSON",
            border_style="green",
            expand=False
        )
        console.print(full_response_panel)
    
    async def show_final_context(self):
        """Muestra el contexto final acumulado."""
        console.print("\n🎯 OBTENIENDO CONTEXTO FINAL", style="bold cyan")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/context-chat/context-sessions/{self.session_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                session_data = response.json()
                
                # Mostrar contexto final
                final_context_panel = Panel(
                    session_data["accumulated_context"],
                    title="🎯 CONTEXTO FINAL ACUMULADO",
                    border_style="gold1"
                )
                console.print(final_context_panel)
                
                # Mostrar historial conversacional
                self.show_conversation_history(session_data["conversation_history"])
                
            else:
                console.print(f"❌ Error obteniendo sesión: {response.status_code}", style="red")
    
    def show_conversation_history(self, history):
        """Muestra el historial conversacional completo."""
        console.print("\n📚 HISTORIAL CONVERSACIONAL COMPLETO", style="bold white")
        
        for i, message in enumerate(history, 1):
            role_emoji = "👤" if message["role"] == "user" else "🤖"
            role_style = "blue" if message["role"] == "user" else "green"
            
            message_panel = Panel(
                message["content"],
                title=f"{role_emoji} {message['role'].upper()} - Mensaje {i}",
                border_style=role_style
            )
            console.print(message_panel)
    
    async def simulate_finalization(self):
        """Simula la finalización y envío a IAs principales."""
        console.print("\n🏁 FINALIZANDO CONSTRUCCIÓN DE CONTEXTO", style="bold magenta")
        
        final_question = "¿Qué estrategias específicas puedo implementar para mejorar la retención de usuarios y aumentar las conversiones del primer al segundo pedido?"
        
        # Mostrar pregunta final
        question_panel = Panel(
            final_question,
            title="❓ PREGUNTA FINAL PARA LAS IAs PRINCIPALES",
            border_style="red"
        )
        console.print(question_panel)
        
        # Preparar request de finalización
        finalize_request = {
            "session_id": str(self.session_id),
            "final_question": final_question
        }
        
        # Mostrar request
        finalize_json = json.dumps(finalize_request, indent=2, ensure_ascii=False)
        syntax = Syntax(finalize_json, "json", theme="monokai", line_numbers=True)
        
        finalize_panel = Panel(
            syntax,
            title="📤 REQUEST DE FINALIZACIÓN",
            border_style="yellow"
        )
        console.print(finalize_panel)
        
        # Enviar finalización
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/context-chat/context-sessions/{self.session_id}/finalize",
                json=finalize_request,
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Mostrar resultado
                result_panel = Panel(
                    f"✅ {result['message']}\n\n"
                    f"📝 Contexto: {result['accumulated_context'][:200]}...\n\n"
                    f"❓ Pregunta: {result['final_question']}\n\n"
                    f"🚀 Listo para IAs: {result['ready_for_ai_processing']}",
                    title="🎉 RESULTADO DE FINALIZACIÓN",
                    border_style="green"
                )
                console.print(result_panel)
                
                # Aquí mostraríamos cómo se enviaría a las IAs principales
                await self.show_final_prompt_for_ais(result)
                
            else:
                console.print(f"❌ Error en finalización: {response.status_code}", style="red")
    
    async def show_final_prompt_for_ais(self, finalization_result):
        """Muestra cómo se construiría el prompt final para las IAs principales."""
        console.print("\n🎯 PROMPT FINAL PARA LAS IAs PRINCIPALES", style="bold red")
        
        # Simular el prompt que se enviaría a OpenAI y Anthropic
        final_prompt = f"""
CONTEXTO DEL PROYECTO:
{finalization_result['accumulated_context']}

CONSULTA DEL USUARIO:
{finalization_result['final_question']}

Por favor, proporciona una respuesta detallada y específica basándote en el contexto proporcionado.
        """.strip()
        
        prompt_panel = Panel(
            final_prompt,
            title="📋 PROMPT COMPLETO PARA OPENAI & ANTHROPIC",
            border_style="red"
        )
        console.print(prompt_panel)
        
        # Mostrar metadatos del prompt
        prompt_stats = Table(title="📈 ESTADÍSTICAS DEL PROMPT FINAL")
        prompt_stats.add_column("Métrica", style="cyan")
        prompt_stats.add_column("Valor", style="white")
        
        prompt_stats.add_row("Caracteres totales", str(len(final_prompt)))
        prompt_stats.add_row("Palabras aproximadas", str(len(final_prompt.split())))
        prompt_stats.add_row("Líneas de contexto", str(finalization_result['accumulated_context'].count('\n') + 1))
        
        console.print(prompt_stats)


async def main():
    """Función principal."""
    tester = ContextBuilderTester()
    await tester.run_complete_test()


if __name__ == "__main__":
    # Ejecutar la prueba
    asyncio.run(main()) 