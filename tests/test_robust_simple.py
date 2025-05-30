#!/usr/bin/env python3
"""
Prueba simple para verificar el manejo robusto de errores
"""

import asyncio
import logging
from uuid import uuid4

from app.schemas.query import QueryRequest, QueryType
from app.services.query_service import QueryService
from app.services.health_monitor import HealthMonitorService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_functionality():
    """Prueba básica de funcionalidad"""
    logger.info("🧪 Iniciando prueba básica de manejo robusto de errores")
    
    query_service = QueryService()
    health_monitor = HealthMonitorService(query_service.ai_orchestrator)
    
    try:
        # 1. Prueba consulta simple
        logger.info("1️⃣ Probando consulta simple...")
        query = QueryRequest(
            user_question="¿Qué es Python?",
            query_type=QueryType.SIMPLE,
            project_id=uuid4(),
            user_id=uuid4(),
            max_tokens=50
        )
        
        response = await query_service.process_query(query)
        
        logger.info(f"✅ Consulta completada:")
        logger.info(f"   - Respuestas recibidas: {len(response.ai_responses)}")
        logger.info(f"   - Tiempo de procesamiento: {response.processing_time_ms}ms")
        logger.info(f"   - Proveedores exitosos: {response.metadata.get('successful_responses', 0)}")
        
        # 2. Prueba monitoreo de salud
        logger.info("\n2️⃣ Probando monitoreo de salud...")
        health_report = await health_monitor.get_system_health()
        
        logger.info(f"✅ Monitoreo de salud:")
        logger.info(f"   - Estado general: {health_report.overall_status}")
        logger.info(f"   - Proveedores monitoreados: {len(health_report.providers)}")
        
        for provider_health in health_report.providers:
            logger.info(f"   - {provider_health.provider.value}: {provider_health.status.value}")
        
        # 3. Verificar métricas detalladas
        logger.info("\n3️⃣ Verificando métricas detalladas...")
        metadata = response.metadata
        
        logger.info(f"✅ Métricas:")
        logger.info(f"   - Tasa de éxito: {metadata.get('success_rate', 0):.1%}")
        logger.info(f"   - Análisis de errores: {metadata.get('error_analysis', {})}")
        
        if metadata.get('latency_stats'):
            stats = metadata['latency_stats']
            logger.info(f"   - Latencia promedio: {stats.get('avg_latency_ms', 0)}ms")
        
        logger.info("\n🎉 ¡Todas las pruebas básicas completadas exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error en pruebas: {e}")
        raise
    finally:
        await query_service.close()

if __name__ == "__main__":
    asyncio.run(test_basic_functionality()) 