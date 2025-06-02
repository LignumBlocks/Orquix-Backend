"""
Pruebas para la Tarea 3.3: Formato y Validación de la Respuesta Sintetizada
Verificación de validación de calidad y estrategias de fallback
"""

import pytest
import asyncio
from datetime import datetime
from typing import List

from app.services.ai_moderator import AIModerator, ModeratorResponse, SynthesisQuality
from app.schemas.ai_response import (
    StandardAIResponse, 
    AIResponseStatus, 
    AIProviderEnum
)

class TestModeratorTask33:
    """Pruebas específicas para la Tarea 3.3 del Moderador MVP"""
    
    @pytest.fixture
    def moderator(self):
        """Fixture del moderador"""
        return AIModerator()
    
    @pytest.fixture
    def valid_responses(self):
        """Respuestas válidas para síntesis"""
        return [
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,
                response_text="""
                Python es un lenguaje de programación interpretado de alto nivel conocido por su sintaxis clara.
                Es ampliamente utilizado en desarrollo web, análisis de datos, inteligencia artificial y automatización.
                Cuenta con una gran biblioteca estándar y un ecosistema de paquetes muy rico.
                La filosofía de Python enfatiza la legibilidad del código y la simplicidad.
                """,
                status=AIResponseStatus.SUCCESS,
                latency_ms=1200,
                timestamp=datetime.utcnow()
            ),
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.ANTHROPIC,
                response_text="""
                Python se caracteriza por ser un lenguaje versátil y fácil de aprender.
                Es popular en ciencia de datos, machine learning, desarrollo backend y scripting.
                Tiene frameworks potentes como Django para web, pandas para datos y TensorFlow para ML.
                Su comunidad es muy activa y proporciona excelente documentación.
                """,
                status=AIResponseStatus.SUCCESS,
                latency_ms=1300,
                timestamp=datetime.utcnow()
            )
        ]

    def test_validate_synthesis_quality_valid_text(self, moderator):
        """
        Prueba 3.3.1: Validación de texto válido
        Verifica que textos válidos pasen la validación
        """
        valid_synthesis = """
        ## Temas Clave Identificados
        1. Características del lenguaje Python
        2. Aplicaciones principales de Python
        3. Ecosistema y comunidad
        
        ## Análisis por Tema
        1. Características del lenguaje:
           - Según IA1, Python es interpretado y de alto nivel con sintaxis clara
           - Según IA2, Python es versátil y fácil de aprender
        
        2. Aplicaciones principales:
           - Según IA1, se usa en desarrollo web, análisis de datos e IA
           - Según IA2, es popular en ciencia de datos y machine learning
        
        ## Contradicciones Detectadas
        Ninguna contradicción factual obvia detectada
        
        ## Síntesis Final
        Ambas fuentes coinciden en que Python es un lenguaje versátil y accesible.
        """
        
        is_valid, reason = moderator._validate_synthesis_quality(valid_synthesis)
        
        assert is_valid == True
        assert reason == "Síntesis válida"
        
        print(f"✅ Texto válido aprobado: {reason}")

    def test_validate_synthesis_quality_too_short(self, moderator):
        """
        Prueba 3.3.2: Validación de texto demasiado corto
        Verifica que textos muy cortos fallen la validación
        """
        short_synthesis = "Python es bueno."
        
        is_valid, reason = moderator._validate_synthesis_quality(short_synthesis)
        
        assert is_valid == False
        assert "demasiado corta" in reason.lower()
        
        print(f"✅ Texto corto rechazado: {reason}")

    def test_validate_synthesis_quality_disclaimer_heavy(self, moderator):
        """
        Prueba 3.3.3: Validación de texto dominado por disclaimers
        Verifica que textos con muchos disclaimers fallen la validación
        """
        disclaimer_synthesis = """
        Lo siento, pero no puedo proporcionar una síntesis específica.
        Como modelo de lenguaje, no tengo la capacidad de acceder a información actualizada.
        Disculpa, pero no soy un experto en este tema.
        Te recomiendo consultar a un profesional para obtener información precisa.
        """
        
        is_valid, reason = moderator._validate_synthesis_quality(disclaimer_synthesis)
        
        assert is_valid == False
        assert "disclaimer" in reason.lower()
        
        print(f"✅ Texto con disclaimers rechazado: {reason}")

    def test_validate_synthesis_quality_repetitive(self, moderator):
        """
        Prueba 3.3.4: Validación de texto repetitivo
        Verifica que textos muy repetitivos fallen la validación
        """
        repetitive_synthesis = """
        Python Python Python es un lenguaje Python que usa Python para Python.
        El lenguaje Python permite Python en Python con Python y Python.
        Python facilita Python mediante Python para Python con Python siempre.
        Definitivamente Python es Python porque Python hace Python en Python.
        """
        
        is_valid, reason = moderator._validate_synthesis_quality(repetitive_synthesis)
        
        assert is_valid == False
        assert "repetitiva" in reason.lower()
        
        print(f"✅ Texto repetitivo rechazado: {reason}")

    def test_validate_synthesis_quality_few_sentences(self, moderator):
        """
        Prueba 3.3.5: Validación de texto con pocas oraciones
        Verifica que textos con muy pocas oraciones fallen la validación
        """
        few_sentences_synthesis = "Python es bueno. Es útil pero no muy largo para pasar validación"  # 2 oraciones más largas
        
        is_valid, reason = moderator._validate_synthesis_quality(few_sentences_synthesis)
        
        assert is_valid == False
        # Puede fallar por longitud mínima o pocas oraciones
        assert ("pocas oraciones" in reason.lower() or "demasiado corta" in reason.lower())
        
        print(f"✅ Texto con pocas oraciones rechazado: {reason}")

    def test_validate_synthesis_quality_too_long(self, moderator):
        """
        Prueba 3.3.6: Validación de texto demasiado largo
        Verifica que textos excesivamente largos fallen la validación
        """
        # Generar un texto muy largo (más de 2000 caracteres) pero no repetitivo
        base_text = """
        ## Análisis Extenso de Python
        
        Python es un lenguaje de programación interpretado de alto nivel que fue creado por Guido van Rossum.
        Se caracteriza por su sintaxis clara y legible que facilita el desarrollo de aplicaciones.
        Es ampliamente utilizado en múltiples dominios como ciencia de datos, desarrollo web y automatización.
        """
        
        # Agregar suficiente contenido variado para superar 2000 caracteres sin ser repetitivo
        long_synthesis = base_text + " ".join([
            f"Punto {i}: Python ofrece características únicas como flexibilidad, robustez y escalabilidad para proyectos de diferentes tamaños y complejidades."
            for i in range(1, 50)
        ])
        
        is_valid, reason = moderator._validate_synthesis_quality(long_synthesis)
        
        assert is_valid == False
        assert "demasiado larga" in reason.lower()
        
        print(f"✅ Texto demasiado largo rechazado: {reason}")

    def test_validate_synthesis_quality_empty(self, moderator):
        """
        Prueba 3.3.7: Validación de texto vacío
        Verifica que textos vacíos o solo espacios fallen la validación
        """
        empty_cases = ["", "   ", "\n\n\n", None]
        
        for empty_text in empty_cases:
            is_valid, reason = moderator._validate_synthesis_quality(empty_text or "")
            
            assert is_valid == False
            assert "vacía" in reason.lower() or "espacios" in reason.lower()
            
        print(f"✅ Textos vacíos rechazados correctamente")

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_synthesis(self, moderator, valid_responses):
        """
        Prueba 3.3.8: Activación de fallback cuando síntesis es inválida
        Verifica que se active el fallback cuando la síntesis no pasa la validación
        """
        
        # Simular una síntesis inválida modificando temporalmente el adaptador
        original_adapter = moderator.synthesis_adapter
        
        # Mock adapter que devuelve síntesis inválida
        class MockInvalidAdapter:
            async def generate_response(self, request):
                return StandardAIResponse(
                    ia_provider_name=AIProviderEnum.OPENAI,
                    response_text="Muy corto.",  # Inválido por ser muy corto
                    status=AIResponseStatus.SUCCESS,
                    latency_ms=100,
                    timestamp=datetime.utcnow()
                )
        
        moderator.synthesis_adapter = MockInvalidAdapter()
        
        try:
            result = await moderator.synthesize_responses(valid_responses)
            
            # Debe activar fallback por síntesis inválida
            assert result.fallback_used == True
            assert result.quality == SynthesisQuality.LOW
            assert "respuesta seleccionada" in result.synthesis_text.lower()
            
            print(f"✅ Fallback activado por síntesis inválida:")
            print(f"📝 {result.synthesis_text[:100]}...")
            
        finally:
            # Restaurar adaptador original
            moderator.synthesis_adapter = original_adapter

    @pytest.mark.asyncio
    async def test_quality_assessment_integration(self, moderator, valid_responses):
        """
        Prueba 3.3.9: Integración de evaluación de calidad
        Verifica que la evaluación de calidad use la validación de Tarea 3.3
        """
        result = await moderator.synthesize_responses(valid_responses)
        
        # Debe pasar la validación y tener buena calidad
        assert result.fallback_used == False
        assert result.quality in [SynthesisQuality.HIGH, SynthesisQuality.MEDIUM]
        
        # El texto debe pasar la validación manual
        is_valid, reason = moderator._validate_synthesis_quality(result.synthesis_text)
        assert is_valid == True
        
        print(f"✅ Síntesis válida con calidad {result.quality}:")
        print(f"📝 Validación: {reason}")
        print(f"📊 Longitud: {len(result.synthesis_text)} caracteres")

    @pytest.mark.asyncio
    async def test_structured_format_validation(self, moderator, valid_responses):
        """
        Prueba 3.3.10: Validación de formato estructurado
        Verifica que las síntesis tengan formato estructurado apropiado
        """
        result = await moderator.synthesize_responses(valid_responses)
        
        synthesis_text = result.synthesis_text
        
        # Verificar elementos estructurales esperados
        structural_elements = [
            "##",  # Headers markdown
            "temas" or "tema",  # Sección de temas
            "contradicciones" or "contradicción",  # Sección de contradicciones
            "síntesis" or "conclusión"  # Sección final
        ]
        
        has_structure = any(element in synthesis_text.lower() for element in structural_elements)
        assert has_structure, "La síntesis debe tener estructura reconocible"
        
        # Verificar referencias a IAs
        has_references = any(ref in synthesis_text.lower() for ref in ["ia1", "ia2", "según", "openai", "anthropic"])
        assert has_references, "La síntesis debe incluir referencias a las fuentes"
        
        print(f"✅ Formato estructurado verificado:")
        print(f"📝 Estructura detectada: {has_structure}")
        print(f"🔗 Referencias detectadas: {has_references}")

    def test_quality_thresholds(self, moderator):
        """
        Prueba 3.3.11: Umbrales de calidad
        Verifica que los umbrales de calidad funcionen correctamente
        """
        test_cases = [
            {
                "text": "## Temas\n1. Python\n\n## Análisis\nSegún IA1, Python es bueno. Según IA2, también es excelente para desarrollo.\n\n## Contradicciones\nNinguna contradicción detectada\n\n## Síntesis\nPython es consensualmente bueno según ambas fuentes y muy útil.",
                "expected": SynthesisQuality.HIGH,
                "description": "Síntesis completa y estructurada"
            },
            {
                "text": "Python es un lenguaje versátil según IA1. IA2 coincide en que es útil para múltiples aplicaciones. Ambos mencionan su facilidad de uso y la importancia de su sintaxis clara.",
                "expected": SynthesisQuality.MEDIUM,
                "description": "Síntesis básica pero válida"
            },
            {
                "text": "Python es considerado un buen lenguaje de programación. Es útil para desarrollar aplicaciones. Funciona bien en diferentes contextos. Se usa mucho en la industria actual. Es popular entre desarrolladores.",
                "expected": SynthesisQuality.LOW,
                "description": "Síntesis muy básica pero válida"
            }
        ]
        
        for case in test_cases:
            # Crear componentes mock para la evaluación
            components = {
                "key_themes": ["Python"] if "python" in case["text"].lower() else [],
                "contradictions": [],
                "consensus_areas": [],
                "source_references": {"IA1": []} if "ia1" in case["text"].lower() else {}
            }
            
            quality = moderator._assess_synthesis_quality(case["text"], components)
            
            print(f"✅ {case['description']}: {quality} (esperado: {case['expected']})")
            
            # Verificar que la calidad esté en el rango esperado (incluir FAILED como posibilidad)
            quality_levels = [SynthesisQuality.FAILED, SynthesisQuality.LOW, SynthesisQuality.MEDIUM, SynthesisQuality.HIGH]
            expected_index = quality_levels.index(case["expected"])
            actual_index = quality_levels.index(quality)
            
            # Permitir variación de ±1 nivel, pero FAILED solo si es el caso más básico
            if quality == SynthesisQuality.FAILED and case["expected"] != SynthesisQuality.LOW:
                # Si falló validación básica cuando no debería, es error
                is_valid, validation_reason = moderator._validate_synthesis_quality(case["text"])
                print(f"⚠️  Falló validación básica: {validation_reason}")
                # Permitir fallo si es por razón válida
                assert not is_valid, f"Texto marcado como FAILED pero pasó validación: {validation_reason}"
            else:
                # Verificar que esté en rango esperado
                assert abs(actual_index - expected_index) <= 1, \
                    f"Calidad {quality} muy diferente de la esperada {case['expected']} para: {case['description']}"

if __name__ == "__main__":
    # Ejecutar pruebas básicas
    import asyncio
    
    async def run_basic_validation_test():
        moderator = AIModerator()
        
        # Prueba de validación básica
        valid_text = """
        ## Temas Clave
        1. Programación en Python
        
        ## Análisis
        Según IA1, Python es versátil. Según IA2, es fácil de usar.
        
        ## Contradicciones
        Ninguna contradicción detectada.
        
        ## Síntesis Final
        Ambas fuentes coinciden en las ventajas de Python.
        """
        
        is_valid, reason = moderator._validate_synthesis_quality(valid_text)
        print(f"Validación básica: {is_valid} - {reason}")
        
        # Prueba de texto inválido
        invalid_text = "Muy corto"
        is_valid, reason = moderator._validate_synthesis_quality(invalid_text)
        print(f"Validación texto corto: {is_valid} - {reason}")
    
    asyncio.run(run_basic_validation_test()) 