import json
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from app.models.pre_analysis import (
    ClarificationSession, 
    ConversationTurn, 
    PreAnalysisResult,
    ClarificationRequest,
    ClarificationResponse
)
from app.services.pre_analyst import pre_analyst_service

class ClarificationManager:
    """
    Gestor de sesiones de clarificación iterativa con el PreAnalyst.
    
    Maneja el flujo conversacional cuando el PreAnalyst detecta que necesita
    más información del usuario para refinar una consulta.
    """
    
    def __init__(self):
        # Almacenamiento en memoria de sesiones activas
        # TODO: En producción esto debería usar Redis o base de datos
        self._active_sessions: Dict[UUID, ClarificationSession] = {}
        self._session_timeout_minutes = 30  # Timeout de sesiones
    
    async def start_clarification_session(
        self,
        project_id: UUID,
        user_id: UUID,
        initial_prompt: str
    ) -> ClarificationResponse:
        """
        Inicia una nueva sesión de clarificación con el PreAnalyst.
        
        Args:
            project_id: ID del proyecto
            user_id: ID del usuario
            initial_prompt: Prompt inicial del usuario
            
        Returns:
            ClarificationResponse con la sesión iniciada
        """
        session_id = uuid4()
        now = datetime.utcnow().isoformat()
        
        # Ejecutar análisis inicial
        analysis_result = await pre_analyst_service.analyze_prompt(initial_prompt)
        
        # Crear turno inicial del usuario
        user_turn = ConversationTurn(
            role="user",
            content=initial_prompt,
            timestamp=now
        )
        
        # Crear sesión
        session = ClarificationSession(
            session_id=session_id,
            project_id=project_id,
            user_id=user_id,
            conversation_history=[user_turn],
            current_analysis=analysis_result,
            is_complete=not bool(analysis_result.clarification_questions),
            final_refined_prompt=analysis_result.refined_prompt_candidate,
            created_at=now,
            updated_at=now
        )
        
        # Almacenar sesión
        self._active_sessions[session_id] = session
        
        # Si ya está completa, no necesita más clarificación
        if session.is_complete:
            # Agregar turno del asistente indicando que está listo
            assistant_turn = ConversationTurn(
                role="assistant",
                content=f"Entiendo que {analysis_result.interpreted_intent}. Procederé con tu consulta.",
                timestamp=now
            )
            session.conversation_history.append(assistant_turn)
        else:
            # Agregar turno del asistente con preguntas
            questions_text = "\n".join([f"• {q}" for q in analysis_result.clarification_questions])
            assistant_turn = ConversationTurn(
                role="assistant",
                content=f"Entiendo que {analysis_result.interpreted_intent}.\n\nPara ayudarte mejor, necesito aclarar algunos puntos:\n\n{questions_text}",
                timestamp=now
            )
            session.conversation_history.append(assistant_turn)
        
        return ClarificationResponse(
            session_id=session_id,
            analysis_result=analysis_result,
            conversation_history=session.conversation_history,
            is_complete=session.is_complete,
            final_refined_prompt=session.final_refined_prompt,
            next_questions=analysis_result.clarification_questions
        )
    
    async def continue_clarification_session(
        self,
        session_id: UUID,
        user_response: str
    ) -> ClarificationResponse:
        """
        Continúa una sesión de clarificación existente.
        
        Args:
            session_id: ID de la sesión
            user_response: Respuesta del usuario a las preguntas
            
        Returns:
            ClarificationResponse actualizada
            
        Raises:
            ValueError: Si la sesión no existe o ya está completa
        """
        # Obtener sesión existente
        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Sesión {session_id} no encontrada o expirada")
        
        if session.is_complete:
            raise ValueError(f"La sesión {session_id} ya está completa")
        
        now = datetime.utcnow().isoformat()
        
        # Agregar respuesta del usuario al historial
        user_turn = ConversationTurn(
            role="user",
            content=user_response,
            timestamp=now
        )
        session.conversation_history.append(user_turn)
        
        # Construir contexto conversacional para el análisis
        conversation_context = self._build_conversation_context(session.conversation_history)
        
        # Ejecutar nuevo análisis con contexto conversacional
        analysis_result = await pre_analyst_service.analyze_prompt(conversation_context)
        
        # Actualizar sesión
        session.current_analysis = analysis_result
        session.is_complete = not bool(analysis_result.clarification_questions)
        session.final_refined_prompt = analysis_result.refined_prompt_candidate
        session.updated_at = now
        
        # Agregar respuesta del asistente
        if session.is_complete:
            if analysis_result.refined_prompt_candidate:
                assistant_content = f"Perfecto, ahora tengo toda la información necesaria.\n\nConsulta refinada: {analysis_result.refined_prompt_candidate}"
            else:
                assistant_content = "Entendido. Procederé con tu consulta basándome en la información proporcionada."
        else:
            questions_text = "\n".join([f"• {q}" for q in analysis_result.clarification_questions])
            assistant_content = f"Gracias por la información adicional.\n\nAún necesito aclarar algunos puntos:\n\n{questions_text}"
        
        assistant_turn = ConversationTurn(
            role="assistant",
            content=assistant_content,
            timestamp=now
        )
        session.conversation_history.append(assistant_turn)
        
        return ClarificationResponse(
            session_id=session_id,
            analysis_result=analysis_result,
            conversation_history=session.conversation_history,
            is_complete=session.is_complete,
            final_refined_prompt=session.final_refined_prompt,
            next_questions=analysis_result.clarification_questions
        )
    
    def get_session(self, session_id: UUID) -> Optional[ClarificationSession]:
        """Obtiene una sesión por su ID."""
        return self._active_sessions.get(session_id)
    
    def force_proceed_session(self, session_id: UUID) -> Optional[ClarificationResponse]:
        """
        Fuerza el avance de una sesión saltando las preguntas de clarificación.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            ClarificationResponse con la sesión completada forzadamente
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return None
        
        now = datetime.utcnow().isoformat()
        
        # Marcar sesión como completa y forzada
        session.is_complete = True
        session.force_proceed = True
        session.updated_at = now
        
        # Agregar turno del asistente indicando que se procede sin clarificación
        assistant_turn = ConversationTurn(
            role="assistant",
            content="Entendido. Procederé con la consulta usando la información disponible.",
            timestamp=now
        )
        session.conversation_history.append(assistant_turn)
        
        return ClarificationResponse(
            session_id=session_id,
            analysis_result=session.current_analysis,
            conversation_history=session.conversation_history,
            is_complete=True,
            final_refined_prompt=session.final_refined_prompt,
            next_questions=[],
            can_force_proceed=False  # Ya no se puede forzar más
        )
    
    def complete_session(self, session_id: UUID) -> Optional[str]:
        """
        Marca una sesión como completa y retorna el prompt refinado final.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Prompt refinado final o None si no está disponible
        """
        session = self._active_sessions.get(session_id)
        if not session:
            return None
        
        session.is_complete = True
        return session.final_refined_prompt
    
    def cleanup_expired_sessions(self):
        """Limpia sesiones expiradas (opcional, para evitar memory leaks)."""
        # TODO: Implementar lógica de expiración basada en timestamp
        pass
    
    def _build_conversation_context(self, conversation_history: list[ConversationTurn]) -> str:
        """
        Construye un contexto conversacional para el análisis del PreAnalyst.
        
        Args:
            conversation_history: Historial de la conversación
            
        Returns:
            Contexto formateado para el análisis
        """
        context_parts = []
        
        for turn in conversation_history:
            if turn.role == "user":
                context_parts.append(f"Usuario: {turn.content}")
            # No incluimos las respuestas del asistente en el contexto para el análisis
        
        # Agregar instrucción específica para análisis iterativo
        context = "\n".join(context_parts)
        context += "\n\nBasándote en toda la información proporcionada por el usuario, analiza si ya tienes suficiente información para generar una consulta refinada específica."
        
        return context

# Instancia global del gestor
clarification_manager = ClarificationManager() 