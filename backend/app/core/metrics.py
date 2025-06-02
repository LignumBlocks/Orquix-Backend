from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import asyncio
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
import threading

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationMetrics:
    """Métricas de una orquestación individual"""
    interaction_id: UUID
    project_id: UUID
    user_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Métricas de tiempo por paso
    context_retrieval_time_ms: Optional[int] = None
    ai_orchestration_time_ms: Optional[int] = None
    moderator_synthesis_time_ms: Optional[int] = None
    background_save_time_ms: Optional[int] = None
    total_processing_time_ms: Optional[int] = None
    
    # Métricas de calidad
    context_chunks_found: int = 0
    ai_responses_count: int = 0
    ai_failures_count: int = 0
    moderator_quality: Optional[str] = None
    fallback_used: bool = False
    
    # Métricas de errores
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    
    def mark_completed(self):
        """Marcar la orquestación como completada"""
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.total_processing_time_ms = int(
                (self.end_time - self.start_time).total_seconds() * 1000
            )
    
    def add_error(self, error: str, step: str):
        """Agregar un error a las métricas"""
        self.errors.append({
            "error": error,
            "step": step,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def add_warning(self, warning: str, step: str):
        """Agregar una advertencia a las métricas"""
        self.warnings.append({
            "warning": warning,
            "step": step,
            "timestamp": datetime.utcnow().isoformat()
        })


class OrchestrationMetricsCollector:
    """Recolector de métricas de orquestación con almacenamiento en memoria"""
    
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self._metrics: Dict[UUID, OrchestrationMetrics] = {}
        self._completed_metrics = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        
        # Estadísticas agregadas
        self._daily_stats = defaultdict(lambda: {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_processing_time": 0,
            "total_processing_time": 0
        })
    
    def start_orchestration(
        self, 
        interaction_id: UUID, 
        project_id: UUID, 
        user_id: UUID
    ) -> OrchestrationMetrics:
        """Iniciar el seguimiento de una nueva orquestación"""
        with self._lock:
            metrics = OrchestrationMetrics(
                interaction_id=interaction_id,
                project_id=project_id,
                user_id=user_id,
                start_time=datetime.utcnow()
            )
            self._metrics[interaction_id] = metrics
            
            logger.debug(f"📊 Iniciando métricas para orquestación {interaction_id}")
            return metrics
    
    def complete_orchestration(
        self, 
        interaction_id: UUID, 
        success: bool = True
    ) -> Optional[OrchestrationMetrics]:
        """Marcar una orquestación como completada y mover a historial"""
        with self._lock:
            metrics = self._metrics.pop(interaction_id, None)
            if not metrics:
                logger.warning(f"📊 No se encontraron métricas para {interaction_id}")
                return None
            
            metrics.mark_completed()
            self._completed_metrics.append(metrics)
            
            # Actualizar estadísticas diarias
            today = datetime.utcnow().date().isoformat()
            stats = self._daily_stats[today]
            stats["total_requests"] += 1
            
            if success and not metrics.errors:
                stats["successful_requests"] += 1
            else:
                stats["failed_requests"] += 1
            
            if metrics.total_processing_time_ms:
                stats["total_processing_time"] += metrics.total_processing_time_ms
                stats["avg_processing_time"] = (
                    stats["total_processing_time"] / stats["total_requests"]
                )
            
            logger.info(f"📊 Orquestación {interaction_id} completada: {metrics.total_processing_time_ms}ms")
            return metrics
    
    def update_step_metrics(
        self, 
        interaction_id: UUID, 
        step: str, 
        duration_ms: int,
        **kwargs
    ):
        """Actualizar métricas de un paso específico"""
        with self._lock:
            metrics = self._metrics.get(interaction_id)
            if not metrics:
                return
            
            # Actualizar tiempo del paso
            if step == "context_retrieval":
                metrics.context_retrieval_time_ms = duration_ms
                metrics.context_chunks_found = kwargs.get("chunks_found", 0)
            elif step == "ai_orchestration":
                metrics.ai_orchestration_time_ms = duration_ms
                metrics.ai_responses_count = kwargs.get("responses_count", 0)
                metrics.ai_failures_count = kwargs.get("failures_count", 0)
            elif step == "moderator_synthesis":
                metrics.moderator_synthesis_time_ms = duration_ms
                metrics.moderator_quality = kwargs.get("quality")
                metrics.fallback_used = kwargs.get("fallback_used", False)
            elif step == "background_save":
                metrics.background_save_time_ms = duration_ms
            
            logger.debug(f"📊 Actualizado paso {step}: {duration_ms}ms para {interaction_id}")
    
    def add_error(self, interaction_id: UUID, error: str, step: str):
        """Agregar error a las métricas"""
        with self._lock:
            metrics = self._metrics.get(interaction_id)
            if metrics:
                metrics.add_error(error, step)
                logger.error(f"📊 Error en {step} para {interaction_id}: {error}")
    
    def add_warning(self, interaction_id: UUID, warning: str, step: str):
        """Agregar advertencia a las métricas"""
        with self._lock:
            metrics = self._metrics.get(interaction_id)
            if metrics:
                metrics.add_warning(warning, step)
                logger.warning(f"📊 Advertencia en {step} para {interaction_id}: {warning}")
    
    def get_current_metrics(self, interaction_id: UUID) -> Optional[OrchestrationMetrics]:
        """Obtener métricas actuales de una orquestación"""
        with self._lock:
            return self._metrics.get(interaction_id)
    
    def get_completed_metrics(self, limit: int = 100) -> list:
        """Obtener métricas de orquestaciones completadas"""
        with self._lock:
            return list(self._completed_metrics)[-limit:]
    
    def get_daily_stats(self, days: int = 7) -> Dict[str, Any]:
        """Obtener estadísticas diarias"""
        with self._lock:
            end_date = datetime.utcnow().date()
            stats = {}
            
            for i in range(days):
                date = (end_date - timedelta(days=i)).isoformat()
                stats[date] = self._daily_stats.get(date, {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "avg_processing_time": 0,
                    "total_processing_time": 0
                })
            
            return stats
    
    def get_system_health_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de salud del sistema"""
        with self._lock:
            active_orchestrations = len(self._metrics)
            completed_today = 0
            failed_today = 0
            avg_processing_time = 0
            
            today = datetime.utcnow().date().isoformat()
            today_stats = self._daily_stats.get(today, {})
            
            if today_stats:
                completed_today = today_stats.get("successful_requests", 0)
                failed_today = today_stats.get("failed_requests", 0)
                avg_processing_time = today_stats.get("avg_processing_time", 0)
            
            # Calcular tasa de éxito
            total_today = completed_today + failed_today
            success_rate = (completed_today / total_today * 100) if total_today > 0 else 100
            
            return {
                "active_orchestrations": active_orchestrations,
                "completed_today": completed_today,
                "failed_today": failed_today,
                "success_rate_percent": round(success_rate, 2),
                "avg_processing_time_ms": round(avg_processing_time, 2),
                "total_completed_requests": len(self._completed_metrics),
                "memory_usage_entries": len(self._completed_metrics) + active_orchestrations
            }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Limpiar datos antiguos para evitar uso excesivo de memoria"""
        with self._lock:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).date().isoformat()
            
            # Limpiar estadísticas diarias antiguas
            keys_to_remove = [
                date for date in self._daily_stats.keys() 
                if date < cutoff_date
            ]
            
            for key in keys_to_remove:
                del self._daily_stats[key]
            
            logger.info(f"📊 Limpieza de métricas: eliminadas {len(keys_to_remove)} entradas")


# Instancia global del recolector de métricas
metrics_collector = OrchestrationMetricsCollector()


# Contexto manager para medición automática de tiempo
class MetricsTimer:
    """Context manager para medir tiempo de ejecución de pasos"""
    
    def __init__(self, interaction_id: UUID, step_name: str, **kwargs):
        self.interaction_id = interaction_id
        self.step_name = step_name
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = int((datetime.utcnow() - self.start_time).total_seconds() * 1000)
            
            if exc_type:
                # Si hubo una excepción, registrarla como error
                metrics_collector.add_error(
                    self.interaction_id, 
                    str(exc_val), 
                    self.step_name
                )
            else:
                # Actualizar métricas del paso
                metrics_collector.update_step_metrics(
                    self.interaction_id,
                    self.step_name,
                    duration_ms,
                    **self.kwargs
                )


# Funciones de conveniencia para usar en la orquestación
def start_orchestration_metrics(interaction_id: UUID, project_id: UUID, user_id: UUID) -> OrchestrationMetrics:
    """Iniciar métricas de orquestación"""
    return metrics_collector.start_orchestration(interaction_id, project_id, user_id)


def complete_orchestration_metrics(interaction_id: UUID, success: bool = True) -> Optional[OrchestrationMetrics]:
    """Completar métricas de orquestación"""
    return metrics_collector.complete_orchestration(interaction_id, success)


def time_step(interaction_id: UUID, step_name: str, **kwargs) -> MetricsTimer:
    """Crear timer para medir un paso de la orquestación"""
    return MetricsTimer(interaction_id, step_name, **kwargs) 