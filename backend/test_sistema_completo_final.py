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
- Prompts reales del AI Moderator
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
            return await self.guardar_output_archivo()
            
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
5. El AI Moderator genera una síntesis unificada usando prompts v2.0
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
        
        # Prompt para OpenAI (simulado basado en OpenAIAdapter)
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
        
        # Prompt para Anthropic (simulado basado en AnthropicAdapter)
        anthropic_prompt = f"""Human: {resultado_finalizacion['accumulated_context']}

{resultado_finalizacion['final_question']}

Por favor, proporciona una respuesta detallada y específica basándote en el contexto proporcionado."""
        
        panel_anthropic = Panel(
            anthropic_prompt,
            title="🔵 PROMPT PARA ANTHROPIC (CLAUDE)",
            border_style="blue"
        )
        console.print(panel_anthropic)
        
        # Mostrar el prompt del AI Moderator v2.0 (el más importante)
        self.log_and_print("\n🧠 PROMPT DEL AI MODERATOR v2.0:", style="bold red")
        
        moderator_prompt = f"""**System Role:**
Eres un asistente de meta-análisis objetivo, analítico y altamente meticuloso. Tu tarea principal es procesar un conjunto de respuestas de múltiples modelos de IA diversos (`external_ai_responses`) a una consulta específica del investigador (`user_question`). Tu objetivo es generar un reporte estructurado, claro y altamente accionable (objetivo total de salida: aproximadamente 800-1000 tokens) que ayude al investigador a:
    a) Comprender las perspectivas diversas y contribuciones clave de cada IA.
    b) Identificar puntos cruciales de consenso y contradicciones factuales obvias.
    c) Reconocer cobertura temática, énfasis y omisiones notables.
    d) Definir pasos lógicos y accionables para su investigación o consulta.

**INPUT DATA:**

**user_question:** {resultado_finalizacion['final_question']}

**external_ai_responses:**
[AI_Modelo_OPENAI] dice: [Respuesta de OpenAI aquí]

[AI_Modelo_ANTHROPIC] dice: [Respuesta de Anthropic aquí]

Por favor, genera el meta-análisis siguiendo exactamente la estructura especificada en el prompt v2.0."""
        
        panel_moderator = Panel(
            moderator_prompt,
            title="🧠 PROMPT DEL AI MODERATOR v2.0 (META-ANÁLISIS)",
            border_style="red"
        )
        console.print(panel_moderator)
        
        # Mostrar estadísticas finales
        tabla_stats = Table(title="📈 ESTADÍSTICAS DEL SISTEMA")
        tabla_stats.add_column("Métrica", style="cyan")
        tabla_stats.add_column("Valor", style="white")
        
        tabla_stats.add_row("Contexto acumulado (chars)", str(len(resultado_finalizacion['accumulated_context'])))
        tabla_stats.add_row("Pregunta final (chars)", str(len(resultado_finalizacion['final_question'])))
        tabla_stats.add_row("Prompt OpenAI (chars)", str(len(openai_prompt)))
        tabla_stats.add_row("Prompt Anthropic (chars)", str(len(anthropic_prompt)))
        tabla_stats.add_row("Prompt Moderator (chars)", str(len(moderator_prompt)))
        
        console.print(tabla_stats)
    
    async def guardar_output_archivo(self):
        """Guarda toda la salida en un archivo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_output = f"test_output_completo_final_{timestamp}.txt"
        
        # Obtener todo el output de la consola
        output_completo = console.export_text()
        
        # Escribir al archivo
        with open(archivo_output, 'w', encoding='utf-8') as f:
            f.write("🧪 DEMOSTRACIÓN COMPLETA DEL SISTEMA DE CONSTRUCCIÓN DE CONTEXTO\n")
            f.write("=" * 80 + "\n")
            f.write(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(output_completo)
            f.write(f"\n\n" + "=" * 80)
            f.write(f"\nArchivo generado: {archivo_output}")
            f.write(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            f.write("\n" + "=" * 80)
        
        self.log_and_print(f"\n📄 Salida completa guardada en: {archivo_output}", style="bold blue")
        
        return archivo_output


async def main():
    """Función principal."""
    sistema = SistemaContextoCompleto()
    archivo_generado = await sistema.ejecutar_demostracion_completa()
    print(f"\n🎉 ¡Demostración completada! Archivo generado: {archivo_generado}")


if __name__ == "__main__":
    # Ejecutar la demostración completa
    asyncio.run(main()) 