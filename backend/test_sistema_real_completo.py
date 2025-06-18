#!/usr/bin/env python3
"""
🧪 PRUEBA COMPLETA DEL SISTEMA DE CONSTRUCCIÓN DE CONTEXTO
=====================================================

Este script ejecuta una demostración completa del nuevo flujo de construcción de contexto
y guarda toda la salida en un archivo para documentación.

Características demostradas:
- Conversación fluida con GPT-3.5
- Identificación automática de preguntas vs información
- Acumulación progresiva de contexto
- Sugerencias inteligentes
- Finalización y preparación para IAs principales
"""

import asyncio
import json
import logging
from datetime import datetime
from uuid import UUID, uuid4
from pathlib import Path

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
console = Console(record=True, width=120)

class SistemaContextoCompleto:
    """Demostración completa del sistema de construcción de contexto."""
    
    def __init__(self):
        self.session_id = None
        self.project_id = "c9cc165a-6fed-4134-bf20-0e5897e3b7c8"  # Proyecto "Caldosa" existente
        self.headers = {
            "Authorization": "Bearer dev-mock-token-12345",
            "Content-Type": "application/json"
        }
        self.output_lines = []
    
    def log_and_print(self, message, style=None):
        """Registra y muestra un mensaje."""
        if style:
            console.print(message, style=style)
        else:
            console.print(message)
        
        # Agregar a output_lines para el archivo final
        self.output_lines.append(str(message))
    
    async def ejecutar_demostracion_completa(self):
        """Ejecuta la demostración completa del sistema."""
        
        # Header principal
        header = "=" * 80 + "\n🧪 PRUEBA COMPLETA DEL FLUJO DE CONSTRUCCIÓN DE CONTEXTO\n" + "=" * 80
        self.log_and_print(header, style="bold blue")
        self.log_and_print("")
        
        try:
            # 1. Verificar backend
            await self.verificar_backend()
            
            # 2. Ejecutar conversación completa
            await self.ejecutar_conversacion_demostracion()
            
            # 3. Mostrar contexto final
            await self.mostrar_contexto_final()
            
            # 4. Finalizar y mostrar prompt para IAs
            await self.finalizar_y_mostrar_prompt()
            
            self.log_and_print("\n✅ PRUEBA COMPLETADA EXITOSAMENTE", style="bold green")
            
            # 5. Guardar output en archivo
            await self.guardar_output_archivo()
            
        except Exception as e:
            self.log_and_print(f"\n❌ ERROR EN LA PRUEBA: {e}", style="bold red")
            raise
    
    async def verificar_backend(self):
        """Verifica que el backend esté funcionando."""
        self.log_and_print("🏥 Verificando salud del backend...", style="yellow")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health/ai-providers")
            
            if response.status_code == 200:
                self.log_and_print("✅ Backend funcionando correctamente", style="green")
            else:
                raise Exception(f"Backend no disponible: {response.status_code}")
    
    async def ejecutar_conversacion_demostracion(self):
        """Ejecuta una conversación de demostración completa."""
        self.log_and_print("\n💬 INICIANDO CONVERSACIÓN DE CONSTRUCCIÓN DE CONTEXTO", style="bold cyan")
        
        # Mensajes de demostración que muestran diferentes tipos de interacciones
        mensajes_demo = [
            "Hola, necesito ayuda con mi startup de delivery de comida",
            "Estamos en etapa de crecimiento, tenemos 1000 usuarios activos", 
            "Nuestro problema principal es la retención de usuarios",
            "Las conversiones del primer pedido al segundo son muy bajas, solo 30%",
            "Operamos en 3 ciudades: Madrid, Barcelona y Valencia"
        ]
        
        for i, mensaje in enumerate(mensajes_demo, 1):
            self.log_and_print(f"\n📝 MENSAJE {i}/5", style="bold white")
            await self.enviar_mensaje_contexto(mensaje, i)
            
            # Pausa para visualización
            await asyncio.sleep(1)
    
    async def enviar_mensaje_contexto(self, mensaje_usuario: str, paso: int):
        """Envía un mensaje al sistema de construcción de contexto."""
        
        # Mostrar mensaje del usuario
        panel_usuario = Panel(
            mensaje_usuario,
            title="👤 USUARIO",
            border_style="blue"
        )
        console.print(panel_usuario)
        
        # Preparar request
        request_data = {
            "user_message": mensaje_usuario,
            "session_id": str(self.session_id) if self.session_id else None
        }
        
        # Mostrar request
        self.mostrar_detalles_request(request_data)
        
        # Enviar request con timeout extendido
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{API_BASE}/context-chat/projects/{self.project_id}/context-chat",
                    json=request_data,
                    headers=self.headers
                )
            except httpx.ReadTimeout:
                self.log_and_print(f"⏱️ TIMEOUT en el mensaje {paso} - El backend tardó más de 60 segundos", style="yellow")
                self.log_and_print("🔄 Reintentando con timeout más largo...", style="yellow")
                
                # Reintentar con timeout aún más largo
                async with httpx.AsyncClient(timeout=120.0) as retry_client:
                    response = await retry_client.post(
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
                await self.mostrar_detalles_respuesta_ia(response_data, paso)
                
            else:
                error_msg = f"❌ Error: {response.status_code} - {response.text}"
                self.log_and_print(error_msg, style="red")
                raise Exception(f"Error en API: {response.status_code}")
    
    def mostrar_detalles_request(self, request_data):
        """Muestra los detalles del request enviado."""
        request_json = json.dumps(request_data, indent=2, ensure_ascii=False)
        syntax = Syntax(request_json, "json", theme="monokai", line_numbers=True)
        
        panel_request = Panel(
            syntax,
            title="📤 REQUEST A LA API",
            border_style="yellow"
        )
        console.print(panel_request)
    
    async def mostrar_detalles_respuesta_ia(self, response_data, paso):
        """Muestra los detalles de la respuesta de la IA."""
        
        # Respuesta de la IA
        panel_ia = Panel(
            response_data["ai_response"],
            title="🤖 RESPUESTA DE GPT-3.5",
            border_style="green"
        )
        console.print(panel_ia)
        
        # Crear tabla con metadatos
        tabla = Table(title=f"📊 METADATOS DEL PASO {paso}")
        tabla.add_column("Campo", style="cyan")
        tabla.add_column("Valor", style="white")
        
        tabla.add_row("Tipo de Mensaje", response_data["message_type"])
        tabla.add_row("Elementos de Contexto", str(response_data["context_elements_count"]))
        tabla.add_row("ID de Sesión", str(response_data["session_id"]))
        
        console.print(tabla)
        
        # Mostrar sugerencias si las hay
        if response_data.get("suggestions"):
            sugerencias_text = "\n".join([f"• {s}" for s in response_data["suggestions"]])
            panel_sugerencias = Panel(
                sugerencias_text,
                title="💡 SUGERENCIAS",
                border_style="magenta"
            )
            console.print(panel_sugerencias)
        
        # Mostrar contexto acumulado si existe
        if response_data.get("accumulated_context"):
            panel_contexto = Panel(
                response_data["accumulated_context"],
                title="📝 CONTEXTO ACUMULADO",
                border_style="cyan"
            )
            console.print(panel_contexto)
        
        # Mostrar respuesta JSON completa
        response_json = json.dumps(response_data, indent=2, ensure_ascii=False)
        syntax = Syntax(response_json, "json", theme="monokai", line_numbers=True)
        
        panel_response_completo = Panel(
            syntax,
            title="📥 RESPUESTA COMPLETA JSON",
            border_style="green",
            expand=False
        )
        console.print(panel_response_completo)
    
    async def mostrar_contexto_final(self):
        """Muestra el contexto final acumulado."""
        self.log_and_print("\n🎯 OBTENIENDO CONTEXTO FINAL", style="bold cyan")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/context-chat/context-sessions/{self.session_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                session_data = response.json()
                
                # Mostrar contexto final
                panel_contexto_final = Panel(
                    session_data["accumulated_context"],
                    title="🎯 CONTEXTO FINAL ACUMULADO",
                    border_style="gold1"
                )
                console.print(panel_contexto_final)
                
                # Mostrar historial conversacional
                self.mostrar_historial_conversacional(session_data["conversation_history"])
                
            else:
                self.log_and_print(f"❌ Error obteniendo sesión: {response.status_code}", style="red")
    
    def mostrar_historial_conversacional(self, historial):
        """Muestra el historial conversacional completo."""
        self.log_and_print("\n📚 HISTORIAL CONVERSACIONAL COMPLETO", style="bold white")
        
        for i, mensaje in enumerate(historial, 1):
            emoji_rol = "👤" if mensaje["role"] == "user" else "🤖"
            estilo_rol = "blue" if mensaje["role"] == "user" else "green"
            
            panel_mensaje = Panel(
                mensaje["content"],
                title=f"{emoji_rol} {mensaje['role'].upper()} - Mensaje {i}",
                border_style=estilo_rol
            )
            console.print(panel_mensaje)
    
    async def finalizar_y_mostrar_prompt(self):
        """Finaliza la construcción de contexto y muestra el prompt para IAs principales."""
        self.log_and_print("\n🏁 FINALIZANDO CONSTRUCCIÓN DE CONTEXTO", style="bold magenta")
        
        pregunta_final = "¿Qué estrategias específicas puedo implementar para mejorar la retención de usuarios y aumentar las conversiones del primer al segundo pedido?"
        
        # Mostrar pregunta final
        panel_pregunta = Panel(
            pregunta_final,
            title="❓ PREGUNTA FINAL PARA LAS IAs PRINCIPALES",
            border_style="red"
        )
        console.print(panel_pregunta)
        
        # Preparar request de finalización
        request_finalizacion = {
            "session_id": str(self.session_id),
            "final_question": pregunta_final
        }
        
        # Mostrar request
        finalize_json = json.dumps(request_finalizacion, indent=2, ensure_ascii=False)
        syntax = Syntax(finalize_json, "json", theme="monokai", line_numbers=True)
        
        panel_finalize = Panel(
            syntax,
            title="📤 REQUEST DE FINALIZACIÓN",
            border_style="yellow"
        )
        console.print(panel_finalize)
        
        # Enviar finalización
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/context-chat/context-sessions/{self.session_id}/finalize",
                json=request_finalizacion,
                headers=self.headers
            )
            
            if response.status_code == 200:
                resultado = response.json()
                
                # Mostrar resultado
                panel_resultado = Panel(
                    f"✅ {resultado['message']}\n\n"
                    f"📝 Contexto: {resultado['accumulated_context'][:200]}...\n\n"
                    f"❓ Pregunta: {resultado['final_question']}\n\n"
                    f"🚀 Listo para IAs: {resultado['ready_for_ai_processing']}",
                    title="🎉 RESULTADO DE FINALIZACIÓN",
                    border_style="green"
                )
                console.print(panel_resultado)
                
                # Mostrar prompt final para IAs principales
                await self.mostrar_prompt_final_ias(resultado)
                
            else:
                self.log_and_print(f"❌ Error en finalización: {response.status_code}", style="red")
    
    async def mostrar_prompt_final_ias(self, resultado_finalizacion):
        """Muestra cómo se construiría el prompt real usando el AI Moderator."""
        self.log_and_print("\n🎯 PROCESO DE ENVÍO A LAS IAs PRINCIPALES", style="bold red")
        
        # Explicar el flujo real
        self.log_and_print("📋 FLUJO REAL DEL SISTEMA:", style="bold white")
        flujo_explicacion = """
1. El contexto acumulado se envía al AI Orchestrator
2. El AI Orchestrator construye requests específicos para cada IA
3. Cada IA recibe su prompt optimizado según su modelo
4. Las respuestas se procesan por el AI Moderator
5. El AI Moderator genera una síntesis unificada
        """.strip()
        
        panel_flujo = Panel(
            flujo_explicacion,
            title="⚙️ ARQUITECTURA DEL SISTEMA",
            border_style="cyan"
        )
        console.print(panel_flujo)
        
        # Mostrar el contexto que se enviaría
        contexto_para_ias = f"""
CONTEXTO ACUMULADO:
{resultado_finalizacion['accumulated_context']}

PREGUNTA FINAL:
{resultado_finalizacion['final_question']}
        """.strip()
        
        panel_contexto = Panel(
            contexto_para_ias,
            title="📝 CONTEXTO QUE SE ENVIARÍA AL AI ORCHESTRATOR",
            border_style="yellow"
        )
        console.print(panel_contexto)
        
        # Simular cómo se construirían los prompts específicos
        self.log_and_print("\n🤖 PROMPTS ESPECÍFICOS POR IA:", style="bold magenta")
        
        # Prompt para OpenAI (simulado)
        openai_prompt = f"""Eres un asistente experto que proporciona respuestas precisas y útiles.

CONTEXTO:
{resultado_finalizacion['accumulated_context']}

CONSULTA:
{resultado_finalizacion['final_question']}

Proporciona una respuesta detallada y específica."""
        
        panel_openai = Panel(
            openai_prompt,
            title="🟢 PROMPT PARA OPENAI (GPT-4)",
            border_style="green"
        )
        console.print(panel_openai)
        
        # USAR EL SERVICIO REAL DE AI MODERATOR
        await self.mostrar_prompt_real_ai_moderator(resultado_finalizacion)
    
    async def mostrar_prompt_real_ai_moderator(self, resultado_finalizacion):
        """Muestra el prompt real que usa el AI Moderator para síntesis."""
        self.log_and_print("\n🤖 PROMPT REAL DEL AI MODERATOR", style="bold red")
        
        try:
            # Importar y crear instancia del AI Moderator
            from app.services.ai_moderator import AIModerator
            moderator = AIModerator()
            
            # Crear respuestas mock para demostración
            from app.schemas.ai_response import StandardAIResponse, AIResponseStatus, AIProviderEnum
            
            mock_responses = [
                StandardAIResponse(
                    response_text="Ejemplo de respuesta de OpenAI para el contexto acumulado",
                    status=AIResponseStatus.SUCCESS,
                    ia_provider_name=AIProviderEnum.OPENAI,
                    response_time_ms=1200,
                    tokens_used=150
                ),
                StandardAIResponse(
                    response_text="Ejemplo de respuesta de Anthropic para el contexto acumulado",
                    status=AIResponseStatus.SUCCESS,
                    ia_provider_name=AIProviderEnum.ANTHROPIC,
                    response_time_ms=1100,
                    tokens_used=140
                )
            ]
            
            # Obtener el prompt real que usa el moderador
            real_prompt = moderator._create_synthesis_prompt(mock_responses)
            
            # Mostrar el prompt real
            panel_prompt_real = Panel(
                real_prompt[:2000] + "..." if len(real_prompt) > 2000 else real_prompt,
                title="🎯 PROMPT REAL DEL AI MODERATOR",
                border_style="red"
            )
            console.print(panel_prompt_real)
            
            self.log_and_print(f"\n📏 Longitud del prompt real: {len(real_prompt)} caracteres", style="yellow")
            
            # Explicar cómo se usa en el flujo real
            explicacion_flujo = """
El prompt mostrado arriba es el que realmente se envía al LLM de síntesis (Claude 3 Haiku o GPT-3.5-Turbo) 
para generar el meta-análisis profesional. Este prompt:

1. Incluye instrucciones detalladas para meta-análisis v2.0
2. Estructura exacta esperada en la respuesta
3. Criterios de validación y calidad
4. Las respuestas reales de las IAs consultadas
5. Auto-validación interna

El resultado es una síntesis estructurada que se devuelve al usuario.
            """.strip()
            
            panel_explicacion = Panel(
                explicacion_flujo,
                title="💡 CÓMO FUNCIONA EL FLUJO REAL",
                border_style="cyan"
            )
            console.print(panel_explicacion)
            
        except Exception as e:
            self.log_and_print(f"❌ Error mostrando prompt real: {e}", style="red")
    
    async def guardar_output_archivo(self):
        """Guarda toda la salida en un archivo para documentación."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_output_completo_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("🧪 PRUEBA COMPLETA DEL SISTEMA DE CONSTRUCCIÓN DE CONTEXTO\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Proyecto: {self.project_id}\n")
                f.write(f"Sesión: {self.session_id}\n\n")
                
                for line in self.output_lines:
                    f.write(line + "\n")
            
            self.log_and_print(f"\n📁 Output guardado en: {filename}", style="green")
            
        except Exception as e:
            self.log_and_print(f"❌ Error guardando archivo: {e}", style="red")


async def main():
    """Función principal del script de prueba."""
    try:
        sistema = SistemaContextoCompleto()
        await sistema.ejecutar_demostracion_completa()
    except KeyboardInterrupt:
        print("\n⚠️ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())