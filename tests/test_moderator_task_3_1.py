"""
Pruebas para la Tarea 3.1: Implementación de la Estrategia de Síntesis MVP
Verificación de síntesis extractiva mejorada usando LLM económico
"""

import pytest
import asyncio
from datetime import datetime
from typing import List

from app.services.ai_moderator import AIModerator, ModeratorResponse, SynthesisQuality
from app.schemas.ai_response import (
    StandardAIResponse, 
    AIResponseStatus, 
    AIProviderEnum,
    ErrorDetail,
    ErrorCategory
)

class TestModeratorTask31:
    """Pruebas específicas para la Tarea 3.1 del Moderador MVP"""
    
    @pytest.fixture
    def moderator(self):
        """Fixture del moderador"""
        return AIModerator()
    
    @pytest.fixture
    def sample_responses_multiple(self):
        """Respuestas de muestra con múltiples IAs para síntesis"""
        return [
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,
                response_text="""
                El cambio climático es causado principalmente por las emisiones de gases de efecto invernadero.
                Las principales fuentes incluyen la quema de combustibles fósiles, la deforestación y la agricultura.
                Los efectos incluyen el aumento de temperaturas, derretimiento de glaciares y eventos climáticos extremos.
                Es necesario reducir las emisiones en un 45% para 2030 según el IPCC.
                """,
                status=AIResponseStatus.SUCCESS,
                latency_ms=1200,
                timestamp=datetime.utcnow()
            ),
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.ANTHROPIC,
                response_text="""
                El calentamiento global se debe a actividades humanas que aumentan los gases de efecto invernadero.
                Los sectores más contaminantes son energía, transporte e industria.
                Las consecuencias incluyen subida del nivel del mar, sequías y pérdida de biodiversidad.
                Se requiere una transición energética hacia renovables y políticas de carbono neutral.
                """,
                status=AIResponseStatus.SUCCESS,
                latency_ms=1500,
                timestamp=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def sample_responses_contradictory(self):
        """Respuestas con contradicciones para probar detección"""
        return [
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,
                response_text="""
                La temperatura global ha aumentado 1.1°C desde la era preindustrial.
                El Acuerdo de París busca limitar el calentamiento a 1.5°C.
                Las energías renovables son más baratas que los combustibles fósiles.
                """,
                status=AIResponseStatus.SUCCESS,
                latency_ms=1000,
                timestamp=datetime.utcnow()
            ),
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.ANTHROPIC,
                response_text="""
                El aumento de temperatura es de 1.5°C desde 1850.
                El objetivo del Acuerdo de París es mantener el calentamiento bajo 2°C.
                Los combustibles fósiles siguen siendo más económicos que las renovables.
                """,
                status=AIResponseStatus.SUCCESS,
                latency_ms=1200,
                timestamp=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def sample_responses_single(self):
        """Una sola respuesta exitosa"""
        return [
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,
                response_text="La inteligencia artificial está transformando múltiples industrias.",
                status=AIResponseStatus.SUCCESS,
                latency_ms=800,
                timestamp=datetime.utcnow()
            )
        ]
    
    @pytest.fixture
    def sample_responses_failed(self):
        """Respuestas fallidas para probar fallback"""
        return [
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,
                response_text=None,
                status=AIResponseStatus.ERROR,
                error_message="API key invalid",
                latency_ms=100,
                timestamp=datetime.utcnow()
            ),
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.ANTHROPIC,
                response_text=None,
                status=AIResponseStatus.TIMEOUT,
                error_message="Request timeout",
                latency_ms=30000,
                timestamp=datetime.utcnow()
            )
        ]

    @pytest.mark.asyncio
    async def test_synthesis_with_multiple_responses(self, moderator, sample_responses_multiple):
        """
        Prueba 3.1.1: Síntesis con múltiples respuestas exitosas
        Verifica que el moderador puede sintetizar respuestas de múltiples IAs
        """
        result = await moderator.synthesize_responses(sample_responses_multiple)
        
        # Verificaciones básicas
        assert isinstance(result, ModeratorResponse)
        assert result.synthesis_text is not None
        assert len(result.synthesis_text) > 0
        assert result.original_responses_count == 2
        assert result.successful_responses_count == 2
        assert result.fallback_used == False
        
        # Verificar que la síntesis no es demasiado corta
        assert len(result.synthesis_text) >= 100, "La síntesis debe tener al menos 100 caracteres"
        
        # Verificar que se identificaron temas clave
        assert len(result.key_themes) >= 1, "Debe identificar al menos 1 tema clave"
        
        # Verificar calidad
        assert result.quality in [SynthesisQuality.HIGH, SynthesisQuality.MEDIUM]
        
        print(f"✅ Síntesis generada ({result.quality}):")
        print(f"📝 Texto: {result.synthesis_text[:200]}...")
        print(f"🎯 Temas: {result.key_themes}")
        print(f"⚠️ Contradicciones: {result.contradictions}")

    @pytest.mark.asyncio
    async def test_contradiction_detection(self, moderator, sample_responses_contradictory):
        """
        Prueba 3.1.2: Detección de contradicciones
        Verifica que el moderador puede detectar contradicciones factuales
        """
        result = await moderator.synthesize_responses(sample_responses_contradictory)
        
        assert isinstance(result, ModeratorResponse)
        assert result.successful_responses_count == 2
        
        # Verificar que se detectaron contradicciones o al menos se mencionan diferencias
        synthesis_lower = result.synthesis_text.lower()
        contradiction_indicators = [
            "contradicción", "diferencia", "discrepancia", "diverge", 
            "mientras que", "sin embargo", "por otro lado"
        ]
        
        has_contradiction_mention = any(
            indicator in synthesis_lower for indicator in contradiction_indicators
        )
        
        assert has_contradiction_mention or len(result.contradictions) > 0, \
            "Debe detectar o mencionar las contradicciones entre respuestas"
        
        print(f"✅ Contradicciones detectadas: {result.contradictions}")
        print(f"📝 Síntesis: {result.synthesis_text[:300]}...")

    @pytest.mark.asyncio
    async def test_source_references(self, moderator, sample_responses_multiple):
        """
        Prueba 3.1.3: Referencias a fuentes
        Verifica que el moderador intenta referenciar las IAs fuente
        """
        result = await moderator.synthesize_responses(sample_responses_multiple)
        
        assert isinstance(result, ModeratorResponse)
        
        # Verificar referencias en el texto o en metadatos
        synthesis_text = result.synthesis_text.lower()
        has_references = (
            "ia1" in synthesis_text or "ia2" in synthesis_text or
            "openai" in synthesis_text or "anthropic" in synthesis_text or
            "según" in synthesis_text or
            len(result.source_references) > 0
        )
        
        assert has_references, "Debe incluir referencias a las IAs fuente"
        
        print(f"✅ Referencias encontradas: {result.source_references}")
        print(f"📝 Texto con referencias: {result.synthesis_text[:200]}...")

    @pytest.mark.asyncio
    async def test_single_response_handling(self, moderator, sample_responses_single):
        """
        Prueba 3.1.4: Manejo de respuesta única
        Verifica el comportamiento con una sola respuesta exitosa
        """
        result = await moderator.synthesize_responses(sample_responses_single)
        
        assert isinstance(result, ModeratorResponse)
        assert result.successful_responses_count == 1
        assert result.original_responses_count == 1
        assert result.synthesis_text is not None
        assert len(result.synthesis_text) > 0
        
        # Con una sola respuesta, debe ser calidad media y mencionar que es única
        assert result.quality == SynthesisQuality.MEDIUM
        assert "única" in result.synthesis_text.lower() or "openai" in result.synthesis_text.lower()
        
        print(f"✅ Respuesta única manejada correctamente:")
        print(f"📝 {result.synthesis_text}")

    @pytest.mark.asyncio
    async def test_fallback_strategy(self, moderator, sample_responses_failed):
        """
        Prueba 3.1.5: Estrategia de fallback
        Verifica el manejo cuando no hay respuestas útiles
        """
        result = await moderator.synthesize_responses(sample_responses_failed)
        
        assert isinstance(result, ModeratorResponse)
        assert result.successful_responses_count == 0
        assert result.original_responses_count == 2
        assert result.fallback_used == True
        assert result.quality == SynthesisQuality.LOW
        
        # Debe tener un mensaje explicativo
        assert "no se pudieron obtener" in result.synthesis_text.lower() or \
               "no hay respuestas" in result.synthesis_text.lower()
        
        print(f"✅ Fallback activado correctamente:")
        print(f"📝 {result.synthesis_text}")

    @pytest.mark.asyncio
    async def test_empty_responses(self, moderator):
        """
        Prueba 3.1.6: Lista vacía de respuestas
        Verifica el manejo de entrada vacía
        """
        result = await moderator.synthesize_responses([])
        
        assert isinstance(result, ModeratorResponse)
        assert result.original_responses_count == 0
        assert result.successful_responses_count == 0
        assert result.fallback_used == True
        assert result.quality == SynthesisQuality.FAILED
        assert "no se recibieron respuestas" in result.synthesis_text.lower()
        
        print(f"✅ Lista vacía manejada correctamente:")
        print(f"📝 {result.synthesis_text}")

    @pytest.mark.asyncio
    async def test_synthesis_performance(self, moderator, sample_responses_multiple):
        """
        Prueba 3.1.7: Rendimiento de síntesis
        Verifica que la síntesis se complete en tiempo razonable
        """
        start_time = datetime.utcnow()
        result = await moderator.synthesize_responses(sample_responses_multiple)
        end_time = datetime.utcnow()
        
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        
        assert isinstance(result, ModeratorResponse)
        assert result.processing_time_ms > 0
        assert total_time_ms < 30000, "La síntesis debe completarse en menos de 30 segundos"
        
        print(f"✅ Síntesis completada en {result.processing_time_ms}ms")
        print(f"⏱️ Tiempo total medido: {total_time_ms:.0f}ms")

    @pytest.mark.asyncio
    async def test_synthesis_word_limit(self, moderator, sample_responses_multiple):
        """
        Prueba 3.1.8: Límite de palabras
        Verifica que la síntesis respete el límite de ~250 palabras
        """
        result = await moderator.synthesize_responses(sample_responses_multiple)
        
        assert isinstance(result, ModeratorResponse)
        
        # Contar palabras aproximadamente
        word_count = len(result.synthesis_text.split())
        
        # Debe ser sustancial pero no excesivo (permitir cierta flexibilidad)
        assert word_count >= 50, "La síntesis debe tener al menos 50 palabras"
        assert word_count <= 400, "La síntesis no debe exceder 400 palabras (objetivo: ~250)"
        
        print(f"✅ Síntesis con {word_count} palabras (objetivo: ~250)")
        print(f"📝 Calidad: {result.quality}")

    def test_moderator_initialization(self, moderator):
        """
        Prueba 3.1.9: Inicialización del moderador
        Verifica que el moderador se inicializa correctamente con LLM económico
        """
        assert moderator is not None
        assert moderator.synthesis_adapter is not None
        
        # Verificar que usa un modelo económico
        adapter = moderator.synthesis_adapter
        if hasattr(adapter, 'model'):
            model_name = adapter.model.lower()
            economic_models = ["gpt-3.5-turbo", "claude-3-haiku", "claude-instant"]
            assert any(econ_model in model_name for econ_model in economic_models), \
                f"Debe usar un modelo económico, encontrado: {model_name}"
        
        print(f"✅ Moderador inicializado con adaptador: {type(adapter).__name__}")

    @pytest.mark.asyncio
    async def test_comprehensive_synthesis_flow(self, moderator):
        """
        Prueba 3.1.10: Flujo completo de síntesis
        Prueba integral que simula el flujo completo desde el orquestador
        """
        # Simular respuestas del orquestador (output de Tarea 2.3)
        orchestrator_responses = [
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,
                response_text="""
                Python es un lenguaje de programación interpretado y de alto nivel.
                Es conocido por su sintaxis clara y legible.
                Se usa ampliamente en ciencia de datos, desarrollo web y automatización.
                Tiene una gran comunidad y ecosistema de librerías.
                """,
                status=AIResponseStatus.SUCCESS,
                latency_ms=1100,
                timestamp=datetime.utcnow()
            ),
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.ANTHROPIC,
                response_text="""
                Python es un lenguaje versátil y fácil de aprender.
                Su filosofía enfatiza la legibilidad del código.
                Es popular en machine learning, análisis de datos y desarrollo backend.
                Cuenta con frameworks como Django, Flask y FastAPI.
                """,
                status=AIResponseStatus.SUCCESS,
                latency_ms=1300,
                timestamp=datetime.utcnow()
            )
        ]
        
        # Ejecutar síntesis
        result = await moderator.synthesize_responses(orchestrator_responses)
        
        # Verificaciones completas
        assert isinstance(result, ModeratorResponse)
        assert result.successful_responses_count == 2
        assert result.fallback_used == False
        assert result.quality in [SynthesisQuality.HIGH, SynthesisQuality.MEDIUM]
        
        # Verificar estructura de la síntesis
        synthesis = result.synthesis_text.lower()
        
        # Debe mencionar temas clave
        assert "python" in synthesis
        assert any(term in synthesis for term in ["legibilidad", "versatil", "popular"])
        
        # Debe tener estructura organizada
        assert len(result.key_themes) >= 2
        
        # Verificar metadatos
        assert result.processing_time_ms > 0
        assert result.timestamp is not None
        
        print(f"✅ Flujo completo exitoso:")
        print(f"📊 Calidad: {result.quality}")
        print(f"🎯 Temas: {result.key_themes}")
        print(f"⏱️ Tiempo: {result.processing_time_ms}ms")
        print(f"📝 Síntesis: {result.synthesis_text[:300]}...")

if __name__ == "__main__":
    # Ejecutar pruebas básicas
    import asyncio
    
    async def run_basic_test():
        moderator = AIModerator()
        
        # Prueba básica
        responses = [
            StandardAIResponse(
                ia_provider_name=AIProviderEnum.OPENAI,
                response_text="El machine learning es una rama de la inteligencia artificial.",
                status=AIResponseStatus.SUCCESS,
                latency_ms=1000,
                timestamp=datetime.utcnow()
            )
        ]
        
        result = await moderator.synthesize_responses(responses)
        print(f"Prueba básica completada: {result.quality}")
        print(f"Síntesis: {result.synthesis_text}")
    
    asyncio.run(run_basic_test()) 