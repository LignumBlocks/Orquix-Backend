#!/usr/bin/env python3
"""
Script de prueba para demostrar el funcionamiento del clasificador multilingüe
del ContextBuilderService refactorizado.
"""

import asyncio
import json
import logging
from typing import Tuple
import openai
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Funciones helper (copias de las implementadas en context_builder.py)
async def classify_message_llm(
    client: openai.AsyncOpenAI,
    user_message: str,
    model: str = "gpt-3.5-turbo"
) -> Tuple[str, float]:
    """
    Clasifica un mensaje usando LLM de forma agnóstica al idioma.
    """
    prompt = (
        "You are a language-agnostic classifier. "
        "Return ONLY valid JSON with keys: "
        "message_type ('question' or 'information') and confidence (0-1). "
        f"Text: «{user_message.strip()}»"
    )
    try:
        chat = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50,
            response_format={"type": "json_object"}
        )
        data = json.loads(chat.choices[0].message.content)
        if data["message_type"] in ("question", "information"):
            return data["message_type"], float(data["confidence"])
    except Exception as e:
        logger.debug(f"LLM classify failed → fallback: {e}")
    return _fallback_heuristic(user_message)

def _fallback_heuristic(msg: str) -> Tuple[str, float]:
    """
    Heurística universal de fallback para clasificación.
    """
    text = msg.strip()
    if text.endswith("?") or (text.count("?") == 1 and len(text) < 80):
        return "question", 0.6
    if len(text.split()) > 15:
        return "information", 0.6
    return "question", 0.5

class SmartClassifyTester:
    """Tester para el clasificador multilingüe."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"
    
    async def _smart_classify(self, user_message: str) -> Tuple[str, float]:
        """Método de clasificación inteligente."""
        return await classify_message_llm(self.client, user_message, self.model)
    
    async def test_multilingual_classification(self):
        """Prueba la clasificación en múltiples idiomas."""
        
        # Casos de prueba multilingües
        test_cases = [
            # Español - Preguntas
            ("¿Cómo puedo mejorar mi negocio?", "question"),
            ("¿Qué estrategias me recomiendas?", "question"),
            ("Necesito ayuda con mi startup", "question"),
            
            # Español - Información
            ("Tengo una empresa de tecnología que desarrolla aplicaciones móviles", "information"),
            ("Mi startup está en el sector fintech y operamos desde hace 2 años", "information"),
            ("Somos una empresa B2B que vende software a grandes corporaciones", "information"),
            
            # Inglés - Preguntas
            ("How can I improve my business?", "question"),
            ("What strategies do you recommend?", "question"),
            ("I need help with my startup", "question"),
            
            # Inglés - Información
            ("I have a technology company that develops mobile applications", "information"),
            ("My startup is in the fintech sector and we've been operating for 2 years", "information"),
            ("We are a B2B company that sells software to large corporations", "information"),
            
            # Portugués - Preguntas
            ("Como posso melhorar meu negócio?", "question"),
            ("Que estratégias você recomenda?", "question"),
            ("Preciso de ajuda com minha startup", "question"),
            
            # Portugués - Información
            ("Tenho uma empresa de tecnologia que desenvolve aplicativos móveis", "information"),
            ("Minha startup está no setor fintech e operamos há 2 anos", "information"),
            
            # Francés - Preguntas
            ("Comment puis-je améliorer mon entreprise?", "question"),
            ("Quelles stratégies recommandez-vous?", "question"),
            
            # Francés - Información
            ("J'ai une entreprise de technologie qui développe des applications mobiles", "information"),
            ("Ma startup est dans le secteur fintech et nous opérons depuis 2 ans", "information"),
            
            # Casos edge
            ("Hola", "question"),  # Mensaje muy corto
            ("?", "question"),  # Solo signo de interrogación
            ("Esta es una descripción muy larga de mi empresa que se dedica a desarrollar software para el sector bancario, tenemos más de 100 empleados y operamos en 5 países diferentes de América Latina ofreciendo servicios de consultoría y desarrollo de aplicaciones", "information"),  # Mensaje muy largo
        ]
        
        print("\n🚀 PRUEBA DEL CLASIFICADOR MULTILINGÜE")
        print("=" * 60)
        
        correct_predictions = 0
        total_tests = len(test_cases)
        
        for i, (message, expected_type) in enumerate(test_cases, 1):
            try:
                print(f"\n📝 Test {i:2d}: {message[:50]}{'...' if len(message) > 50 else ''}")
                
                # Clasificar con LLM
                predicted_type, confidence = await self._smart_classify(message)
                
                # Verificar predicción
                is_correct = predicted_type == expected_type
                if is_correct:
                    correct_predictions += 1
                
                # Mostrar resultado
                status = "✅ CORRECTO" if is_correct else "❌ INCORRECTO"
                print(f"   Esperado: {expected_type:11} | Predicho: {predicted_type:11} | Confianza: {confidence:.2f} | {status}")
                
                # Mostrar fallback si la confianza es baja
                if confidence < 0.55:
                    print(f"   ⚠️  Confianza baja ({confidence:.2f}) - Se usaría mensaje de aclaración")
                
            except Exception as e:
                print(f"   🔥 ERROR: {e}")
                # Probar fallback heurístico
                fallback_type, fallback_conf = _fallback_heuristic(message)
                print(f"   🔄 Fallback: {fallback_type} (confianza: {fallback_conf:.2f})")
        
        # Mostrar estadísticas finales
        accuracy = (correct_predictions / total_tests) * 100
        print(f"\n📊 RESULTADOS FINALES")
        print("=" * 60)
        print(f"Total de pruebas: {total_tests}")
        print(f"Predicciones correctas: {correct_predictions}")
        print(f"Precisión: {accuracy:.1f}%")
        
        if accuracy >= 80:
            print("🎉 ¡Excelente! El clasificador funciona muy bien")
        elif accuracy >= 70:
            print("👍 Buen rendimiento del clasificador")
        else:
            print("⚠️  El clasificador necesita mejoras")
    
    async def test_confidence_handling(self):
        """Prueba el manejo de casos de baja confianza."""
        
        print("\n🎯 PRUEBA DE MANEJO DE CONFIANZA")
        print("=" * 60)
        
        # Casos ambiguos que deberían dar baja confianza
        ambiguous_cases = [
            "OK",
            "Sí",
            "Entiendo",
            "Tal vez",
            "No sé",
            "...",
            "Mmm",
            "Bien",
        ]
        
        for message in ambiguous_cases:
            try:
                predicted_type, confidence = await self._smart_classify(message)
                print(f"📝 '{message:15}' → {predicted_type:11} (confianza: {confidence:.2f})")
                
                if confidence < 0.55:
                    print(f"   💬 Se activaría: 'No estoy seguro de si eso es una pregunta o información. ¿Podrías aclararlo?'")
                
            except Exception as e:
                print(f"🔥 Error con '{message}': {e}")
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas."""
        try:
            await self.test_multilingual_classification()
            await self.test_confidence_handling()
            
            print(f"\n✨ FUNCIONAMIENTO DEL SISTEMA")
            print("=" * 60)
            print("1. 🧠 LLM Multilingüe: Usa GPT-3.5 para clasificar en cualquier idioma")
            print("2. 🔄 Fallback Universal: Si falla el LLM, usa heurística simple")
            print("3. 🎯 Control de Confianza: Si confianza < 0.55, pide aclaración")
            print("4. 🌍 Agnóstico al idioma: Funciona en ES, EN, PT, FR, etc.")
            print("5. 🛡️  Robusto: Nunca falla, siempre retorna una clasificación")
            
        except Exception as e:
            print(f"🔥 Error en las pruebas: {e}")

async def main():
    """Función principal."""
    print("🚀 INICIANDO PRUEBAS DEL CLASIFICADOR MULTILINGÜE")
    print("=" * 60)
    
    # Verificar API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY no está configurada")
        print("Por favor, configura tu API key de OpenAI en el archivo .env")
        return
    
    tester = SmartClassifyTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 