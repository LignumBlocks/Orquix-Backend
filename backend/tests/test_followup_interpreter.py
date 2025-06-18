import pytest
import asyncio
from uuid import uuid4, UUID
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from sqlmodel import Session, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.followup_interpreter import (
    FollowUpInterpreter, 
    ContinuityAnalysis, 
    InteractionContext,
    create_followup_interpreter
)
from app.schemas.query import QueryRequest, QueryType
from app.models.models import InteractionEvent, ModeratedSynthesis, User, Project
from app.core.config import settings


# Configuración de fixtures y datos de prueba
@pytest.fixture(scope="session")
def engine():
    """Engine de base de datos para pruebas."""
    database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return create_engine(database_url, echo=False)


@pytest.fixture
async def db_session():
    """Mock de sesión de base de datos para pruebas."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
async def followup_interpreter(db_session):
    """Fixture que proporciona una instancia de FollowUpInterpreter."""
    return FollowUpInterpreter(db_session)


@pytest.fixture
def sample_interaction_data():
    """Datos de ejemplo para pruebas."""
    project_id = uuid4()
    user_id = uuid4()
    interaction_id = uuid4()
    
    return {
        "project_id": project_id,
        "user_id": user_id,
        "interaction_id": interaction_id,
        "previous_prompt": "Necesito ayuda para planear un viaje de 5 días a Cuba con mi esposa",
        "previous_synthesis": "Para un viaje de 5 días a Cuba en pareja, te recomiendo visitar La Habana (2 días), Viñales (1 día) y Varadero (2 días). El presupuesto estimado es de $1,200-1,500 USD incluyendo vuelos, hoteles y comidas. Los mejores meses son noviembre a abril para evitar la temporada de huracanes.",
        "followup_prompt": "¿Y si fuéramos con niños?",
        "new_topic_prompt": "Ahora quiero información sobre programación en Python"
    }


class TestFollowUpInterpreter:
    """Tests para el servicio FollowUpInterpreter."""
    
    @pytest.mark.asyncio
    async def test_followup_reference_is_continuation(self, followup_interpreter, sample_interaction_data):
        """
        Prueba que detecta correctamente una referencia de continuidad.
        
        Test obligatorio según especificaciones.
        """
        # Arrange: Configurar mock de la base de datos
        mock_interaction = InteractionEvent(
            id=sample_interaction_data["interaction_id"],
            project_id=sample_interaction_data["project_id"],
            user_id=sample_interaction_data["user_id"],
            user_prompt_text=sample_interaction_data["previous_prompt"],
            ai_responses_json='{"refined_prompt": "' + sample_interaction_data["previous_prompt"] + '"}',
            created_at=datetime.now(timezone.utc)
        )
        
        mock_synthesis = ModeratedSynthesis(
            id=uuid4(),
            synthesis_text=sample_interaction_data["previous_synthesis"]
        )
        
        # Mock de la consulta de base de datos
        mock_result = Mock()
        mock_result.first.return_value = (mock_interaction, mock_synthesis)
        mock_result.all.return_value = [(mock_interaction, mock_synthesis)]
        
        followup_interpreter.db.exec = AsyncMock(return_value=mock_result)
        
        # Mock del análisis LLM para casos ambiguos
        with patch.object(followup_interpreter, '_analyze_with_llm') as mock_llm:
            mock_llm.return_value = {
                "is_continuation": True,
                "reference_type": "anaphoric",
                "confidence": 0.9,
                "keywords": ["si", "fuéramos"]
            }
            
            # Act: Procesar la consulta de seguimiento
            result = await followup_interpreter.handle_followup(
                user_prompt=sample_interaction_data["followup_prompt"],
                project_id=sample_interaction_data["project_id"],
                user_id=sample_interaction_data["user_id"]
            )
        
        # Assert: Verificar que detecta continuidad correctamente
        assert isinstance(result, QueryRequest)
        assert result.query_type == QueryType.FOLLOW_UP
        assert "CONTEXTO PREVIO" in result.user_question
        assert sample_interaction_data["previous_prompt"] in result.user_question
        assert sample_interaction_data["followup_prompt"] in result.user_question
        assert result.project_id == sample_interaction_data["project_id"]
        assert result.user_id == sample_interaction_data["user_id"]
    
    @pytest.mark.asyncio
    async def test_followup_reference_new_topic(self, followup_interpreter, sample_interaction_data):
        """
        Prueba que detecta correctamente un tema nuevo (no continuación).
        
        Test obligatorio según especificaciones.
        """
        # Arrange: Configurar mock de la base de datos para tema anterior
        mock_interaction = InteractionEvent(
            id=sample_interaction_data["interaction_id"],
            project_id=sample_interaction_data["project_id"],
            user_id=sample_interaction_data["user_id"],
            user_prompt_text=sample_interaction_data["previous_prompt"],
            ai_responses_json='{"refined_prompt": "' + sample_interaction_data["previous_prompt"] + '"}',
            created_at=datetime.now(timezone.utc)
        )
        
        mock_synthesis = ModeratedSynthesis(
            id=uuid4(),
            synthesis_text=sample_interaction_data["previous_synthesis"]
        )
        
        # Mock de la consulta de base de datos
        mock_result = Mock()
        mock_result.first.return_value = (mock_interaction, mock_synthesis)
        mock_result.all.return_value = [(mock_interaction, mock_synthesis)]
        
        followup_interpreter.db.exec = AsyncMock(return_value=mock_result)
        
        # Mock del análisis LLM que detecta tema nuevo
        with patch.object(followup_interpreter, '_analyze_with_llm') as mock_llm:
            mock_llm.return_value = {
                "is_continuation": False,
                "reference_type": "new_topic",
                "confidence": 0.95,
                "keywords": ["programación", "Python"]
            }
            
            # Act: Procesar consulta de tema nuevo
            result = await followup_interpreter.handle_followup(
                user_prompt=sample_interaction_data["new_topic_prompt"],
                project_id=sample_interaction_data["project_id"],
                user_id=sample_interaction_data["user_id"]
            )
        
        # Assert: Verificar que NO detecta continuidad
        assert isinstance(result, QueryRequest)
        assert result.query_type == QueryType.CONTEXT_AWARE  # No es FOLLOW_UP
        assert result.user_question == sample_interaction_data["new_topic_prompt"]  # Prompt original sin modificar
        assert "CONTEXTO PREVIO" not in result.user_question  # Sin enriquecimiento
        assert result.project_id == sample_interaction_data["project_id"]
        assert result.user_id == sample_interaction_data["user_id"]
    
    @pytest.mark.asyncio
    async def test_heuristic_pattern_detection_strong_continuation(self, followup_interpreter):
        """Prueba la detección heurística de patrones fuertes de continuidad."""
        test_cases = [
            "Dame más detalles sobre eso",
            "¿Y si consideramos también esto?",
            "Mejora la respuesta anterior",
            "Amplía lo que dijiste",
            "Los últimos 3 resultados"
        ]
        
        for prompt in test_cases:
            result = followup_interpreter._analyze_heuristic_patterns(prompt)
            assert result["is_continuation"] == True
            assert result["confidence"] >= 0.8  # Alta confianza
            assert result["reference_type"] in ["anaphoric", "topic_expansion"]
    
    @pytest.mark.asyncio
    async def test_heuristic_pattern_detection_new_topic(self, followup_interpreter):
        """Prueba la detección heurística de tema nuevo."""
        test_cases = [
            "Nueva consulta sobre algo diferente",
            "Ahora quiero hablar de otro tema",
            "Cambio de tema: necesito ayuda con...",
            "Por otro lado, me interesa..."
        ]
        
        for prompt in test_cases:
            result = followup_interpreter._analyze_heuristic_patterns(prompt)
            assert result["is_continuation"] == False
            assert result["confidence"] >= 0.8  # Alta confianza
            assert result["reference_type"] == "new_topic"
    
    @pytest.mark.asyncio
    async def test_enrich_prompt_with_history(self, followup_interpreter, sample_interaction_data):
        """Prueba el enriquecimiento de prompt con historial."""
        current_prompt = sample_interaction_data["followup_prompt"]
        previous_prompt = sample_interaction_data["previous_prompt"]
        previous_synthesis = sample_interaction_data["previous_synthesis"]
        
        enriched = followup_interpreter.enrich_prompt_with_history(
            current_prompt, previous_prompt, previous_synthesis
        )
        
        # Verificar que contiene los elementos esperados
        assert "CONTEXTO PREVIO" in enriched
        assert "NUEVA CONSULTA" in enriched
        assert "INSTRUCCIÓN" in enriched
        assert previous_prompt in enriched
        assert current_prompt in enriched
        assert previous_synthesis[:800] in enriched  # Truncado si es muy largo
    
    @pytest.mark.asyncio
    async def test_get_recent_interaction_context(self, followup_interpreter, sample_interaction_data):
        """Prueba la recuperación de contexto de interacción reciente."""
        # Arrange: Mock de interacción en BD
        mock_interaction = InteractionEvent(
            id=sample_interaction_data["interaction_id"],
            project_id=sample_interaction_data["project_id"],
            user_id=sample_interaction_data["user_id"],
            user_prompt_text=sample_interaction_data["previous_prompt"],
            ai_responses_json='{"refined_prompt": "' + sample_interaction_data["previous_prompt"] + '"}',
            created_at=datetime.now(timezone.utc)
        )
        
        mock_synthesis = ModeratedSynthesis(
            id=uuid4(),
            synthesis_text=sample_interaction_data["previous_synthesis"]
        )
        
        mock_result = Mock()
        mock_result.first.return_value = (mock_interaction, mock_synthesis)
        
        followup_interpreter.db.exec = AsyncMock(return_value=mock_result)
        
        # Act: Recuperar contexto
        context = await followup_interpreter.get_recent_interaction_context(
            project_id=sample_interaction_data["project_id"],
            user_id=sample_interaction_data["user_id"],
            interaction_id=sample_interaction_data["interaction_id"]
        )
        
        # Assert: Verificar resultado
        assert context is not None
        assert isinstance(context, InteractionContext)
        assert context.interaction_id == sample_interaction_data["interaction_id"]
        assert context.user_prompt == sample_interaction_data["previous_prompt"]
        assert context.synthesis_text == sample_interaction_data["previous_synthesis"]
    
    @pytest.mark.asyncio
    async def test_no_previous_interaction(self, followup_interpreter, sample_interaction_data):
        """Prueba el comportamiento cuando no hay interacciones previas."""
        # Arrange: Mock que no devuelve resultados
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_result.all.return_value = []
        
        followup_interpreter.db.exec = AsyncMock(return_value=mock_result)
        
        # Act: Procesar consulta sin historial
        result = await followup_interpreter.handle_followup(
            user_prompt="Primera consulta del usuario",
            project_id=sample_interaction_data["project_id"],
            user_id=sample_interaction_data["user_id"]
        )
        
        # Assert: Debe devolver consulta original
        assert isinstance(result, QueryRequest)
        assert result.query_type == QueryType.CONTEXT_AWARE
        assert result.user_question == "Primera consulta del usuario"
        assert "CONTEXTO PREVIO" not in result.user_question
    
    @pytest.mark.asyncio
    async def test_analyze_query_continuity_integration(self, followup_interpreter, sample_interaction_data):
        """Prueba de integración del análisis de continuidad."""
        # Arrange: Mock de interacción previa
        mock_interaction = InteractionEvent(
            id=sample_interaction_data["interaction_id"],
            project_id=sample_interaction_data["project_id"],
            user_id=sample_interaction_data["user_id"],
            user_prompt_text=sample_interaction_data["previous_prompt"],
            ai_responses_json='{}',
            created_at=datetime.now(timezone.utc)
        )
        
        mock_synthesis = ModeratedSynthesis(
            id=uuid4(),
            synthesis_text=sample_interaction_data["previous_synthesis"]
        )
        
        mock_result = Mock()
        mock_result.first.return_value = (mock_interaction, mock_synthesis)
        mock_result.all.return_value = [(mock_interaction, mock_synthesis)]
        
        followup_interpreter.db.exec = AsyncMock(return_value=mock_result)
        
        # Act: Analizar continuidad con prompt anafórico
        analysis = await followup_interpreter.analyze_query_continuity(
            user_prompt="Dame más detalles sobre eso",  # Patrón fuerte
            project_id=sample_interaction_data["project_id"],
            user_id=sample_interaction_data["user_id"]
        )
        
        # Assert: Debe detectar continuidad con alta confianza
        assert isinstance(analysis, ContinuityAnalysis)
        assert analysis.is_continuation == True
        assert analysis.confidence_score >= 0.8  # Alta confianza por patrón heurístico
        assert analysis.reference_type == "anaphoric"
        assert analysis.previous_interaction_id == sample_interaction_data["interaction_id"]
    
    def test_create_followup_interpreter_factory(self, db_session):
        """Prueba la función factory de creación del servicio."""
        interpreter = create_followup_interpreter(db_session)
        
        assert isinstance(interpreter, FollowUpInterpreter)
        assert interpreter.db == db_session
        assert interpreter.model == "gpt-3.5-turbo-1106"
        assert interpreter.temperature == 0.2


if __name__ == "__main__":
    # Ejecutar tests específicos
    pytest.main([__file__, "-v"])