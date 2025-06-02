import asyncio
import logging
from typing import Dict, List
from datetime import datetime, timedelta

from app.schemas.ai_response import (
    ProviderHealthInfo, ProviderHealthStatus, SystemHealthReport, 
    AIProviderEnum
)
from app.services.ai_orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)

class HealthMonitorService:
    """
    Servicio para monitorear la salud del sistema de IAs.
    
    Responsabilidades:
    - Verificar salud de todos los proveedores
    - Generar reportes de salud del sistema
    - Detectar degradaciones de servicio
    - Proporcionar métricas para observabilidad
    """
    
    def __init__(self, orchestrator: AIOrchestrator):
        self.orchestrator = orchestrator
        self._health_history: List[Dict] = []
    
    async def get_system_health(self) -> SystemHealthReport:
        """Genera un reporte completo de salud del sistema"""
        providers_health = []
        
        # Obtener salud de cada proveedor
        for provider in self.orchestrator.get_available_providers():
            adapter = self.orchestrator.adapters.get(provider)
            if adapter:
                health_info = adapter.get_health_info()
                providers_health.append(health_info)
        
        # Determinar salud general del sistema
        overall_status = self._calculate_overall_status(providers_health)
        
        # Generar estadísticas resumidas
        summary = self._generate_summary(providers_health)
        
        report = SystemHealthReport(
            overall_status=overall_status,
            providers=providers_health,
            summary=summary
        )
        
        # Guardar en historial
        self._health_history.append({
            'timestamp': datetime.utcnow(),
            'report': report
        })
        
        # Limpiar historial antiguo (últimas 24 horas)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._health_history = [
            entry for entry in self._health_history 
            if entry['timestamp'] > cutoff
        ]
        
        return report
    
    def _calculate_overall_status(self, providers_health: List[ProviderHealthInfo]) -> ProviderHealthStatus:
        """Calcula el estado general del sistema basado en los proveedores"""
        if not providers_health:
            return ProviderHealthStatus.UNKNOWN
        
        # Contar estados
        status_counts = {}
        for provider in providers_health:
            status = provider.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_providers = len(providers_health)
        healthy_count = status_counts.get(ProviderHealthStatus.HEALTHY, 0)
        degraded_count = status_counts.get(ProviderHealthStatus.DEGRADED, 0)
        unhealthy_count = status_counts.get(ProviderHealthStatus.UNHEALTHY, 0)
        
        # Lógica de determinación del estado general
        if unhealthy_count >= total_providers:
            return ProviderHealthStatus.UNHEALTHY
        elif unhealthy_count > 0 or degraded_count >= total_providers / 2:
            return ProviderHealthStatus.DEGRADED
        elif healthy_count > 0:
            return ProviderHealthStatus.HEALTHY
        else:
            return ProviderHealthStatus.UNKNOWN
    
    def _generate_summary(self, providers_health: List[ProviderHealthInfo]) -> Dict:
        """Genera estadísticas resumidas del sistema"""
        if not providers_health:
            return {
                "total_providers": 0,
                "healthy_providers": 0,
                "degraded_providers": 0,
                "unhealthy_providers": 0,
                "avg_success_rate": 0.0,
                "avg_latency_ms": 0,
                "total_requests_24h": 0,
                "total_errors_24h": 0
            }
        
        # Contadores por estado
        healthy_count = sum(1 for p in providers_health if p.status == ProviderHealthStatus.HEALTHY)
        degraded_count = sum(1 for p in providers_health if p.status == ProviderHealthStatus.DEGRADED)
        unhealthy_count = sum(1 for p in providers_health if p.status == ProviderHealthStatus.UNHEALTHY)
        
        # Métricas agregadas
        success_rates = [p.success_rate_24h for p in providers_health if p.success_rate_24h is not None]
        latencies = [p.avg_latency_ms for p in providers_health if p.avg_latency_ms is not None]
        
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
        avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0
        
        total_requests = sum(p.total_requests_24h for p in providers_health)
        total_errors = sum(p.total_errors_24h for p in providers_health)
        
        return {
            "total_providers": len(providers_health),
            "healthy_providers": healthy_count,
            "degraded_providers": degraded_count,
            "unhealthy_providers": unhealthy_count,
            "avg_success_rate": round(avg_success_rate, 3),
            "avg_latency_ms": avg_latency,
            "total_requests_24h": total_requests,
            "total_errors_24h": total_errors,
            "system_availability": round(avg_success_rate * 100, 1) if avg_success_rate > 0 else 0.0
        }
    
    async def perform_health_checks(self) -> Dict[AIProviderEnum, bool]:
        """Realiza verificaciones activas de salud en todos los proveedores"""
        results = {}
        
        for provider in self.orchestrator.get_available_providers():
            adapter = self.orchestrator.adapters.get(provider)
            if adapter:
                try:
                    is_healthy = await adapter.health_check()
                    results[provider] = is_healthy
                    logger.info(f"Health check {provider}: {'✅' if is_healthy else '❌'}")
                except Exception as e:
                    logger.error(f"Health check falló para {provider}: {e}")
                    results[provider] = False
        
        return results
    
    def get_provider_trends(self, provider: AIProviderEnum, hours: int = 24) -> Dict:
        """Obtiene tendencias de un proveedor específico"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Filtrar historial por proveedor y tiempo
        provider_history = []
        for entry in self._health_history:
            if entry['timestamp'] > cutoff:
                for provider_info in entry['report'].providers:
                    if provider_info.provider == provider:
                        provider_history.append({
                            'timestamp': entry['timestamp'],
                            'health_info': provider_info
                        })
        
        if not provider_history:
            return {"message": "No data available"}
        
        # Calcular tendencias
        success_rates = [h['health_info'].success_rate_24h for h in provider_history if h['health_info'].success_rate_24h is not None]
        latencies = [h['health_info'].avg_latency_ms for h in provider_history if h['health_info'].avg_latency_ms is not None]
        
        return {
            "data_points": len(provider_history),
            "time_range_hours": hours,
            "avg_success_rate": round(sum(success_rates) / len(success_rates), 3) if success_rates else None,
            "avg_latency_ms": int(sum(latencies) / len(latencies)) if latencies else None,
            "latest_status": provider_history[-1]['health_info'].status if provider_history else None,
            "consecutive_failures": provider_history[-1]['health_info'].consecutive_failures if provider_history else 0
        }
    
    def get_system_alerts(self) -> List[Dict]:
        """Genera alertas basadas en el estado actual del sistema"""
        alerts = []
        
        # Obtener último reporte
        if not self._health_history:
            return alerts
        
        latest_report = self._health_history[-1]['report']
        
        # Alertas por proveedor
        for provider_info in latest_report.providers:
            provider_name = provider_info.provider.value
            
            # Alerta por estado no saludable
            if provider_info.status == ProviderHealthStatus.UNHEALTHY:
                alerts.append({
                    "level": "critical",
                    "provider": provider_name,
                    "message": f"Proveedor {provider_name} está no disponible",
                    "consecutive_failures": provider_info.consecutive_failures
                })
            elif provider_info.status == ProviderHealthStatus.DEGRADED:
                alerts.append({
                    "level": "warning", 
                    "provider": provider_name,
                    "message": f"Proveedor {provider_name} tiene rendimiento degradado",
                    "success_rate": provider_info.success_rate_24h
                })
            
            # Alerta por latencia alta
            if provider_info.avg_latency_ms and provider_info.avg_latency_ms > 10000:  # >10 segundos
                alerts.append({
                    "level": "warning",
                    "provider": provider_name,
                    "message": f"Latencia alta en {provider_name}: {provider_info.avg_latency_ms}ms",
                    "avg_latency_ms": provider_info.avg_latency_ms
                })
        
        # Alertas del sistema
        if latest_report.overall_status == ProviderHealthStatus.UNHEALTHY:
            alerts.append({
                "level": "critical",
                "provider": "system",
                "message": "Sistema completo no disponible",
                "healthy_providers": latest_report.summary.get("healthy_providers", 0)
            })
        
        return alerts
    
    async def start_monitoring(self, interval_minutes: int = 5):
        """Inicia monitoreo continuo del sistema"""
        logger.info(f"Iniciando monitoreo de salud cada {interval_minutes} minutos")
        
        while True:
            try:
                # Generar reporte de salud
                health_report = await self.get_system_health()
                
                # Realizar verificaciones activas ocasionalmente (cada 30 minutos)
                if len(self._health_history) % 6 == 0:  # Cada 6 reportes si interval=5min
                    await self.perform_health_checks()
                
                # Verificar alertas
                alerts = self.get_system_alerts()
                if alerts:
                    logger.warning(f"Alertas activas: {len(alerts)}")
                    for alert in alerts:
                        level = alert['level'].upper()
                        logger.log(
                            logging.CRITICAL if level == 'CRITICAL' else logging.WARNING,
                            f"[{level}] {alert['message']}"
                        )
                
                # Log del estado general
                logger.info(f"Estado del sistema: {health_report.overall_status}")
                
            except Exception as e:
                logger.error(f"Error en monitoreo de salud: {e}")
            
            # Esperar hasta el siguiente intervalo
            await asyncio.sleep(interval_minutes * 60) 