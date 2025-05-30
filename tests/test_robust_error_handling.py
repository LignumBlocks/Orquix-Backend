#!/usr/bin/env python3
"""
Script de prueba para verificar el manejo robusto de errores y timeouts
en el sistema de orquestación de IAs.

Pruebas incluidas:
1. Timeouts individuales por proveedor
2. Continuación con respuestas parciales
3. Manejo de errores específicos (auth, rate limit, etc.)
4. Métricas y logging detallado
5. Monitoreo de salud del sistema
"""

import asyncio
import logging
import time
from typing import List
from uuid import uuid4

from app.schemas.query import QueryRequest, QueryType, ContextConfig
from app.schemas.ai_response import AIProviderEnum
from app.services.query_service import QueryService
from app.services.health_monitor import HealthMonitorService
from app.core.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustErrorHandlingTester:
    """Tester para verificar manejo robusto de errores"""
    
    def __init__(self):
        self.query_service = QueryService()
        self.health_monitor = HealthMonitorService(self.query_service.ai_orchestrator)
        self.test_results = []
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas de manejo de errores"""
        logger.info("🚀 Iniciando pruebas de manejo robusto de errores")
        
        tests = [
            ("Consulta básica exitosa", self.test_successful_query),
            ("Consulta con contexto", self.test_context_aware_query),
            ("Manejo de timeouts", self.test_timeout_handling),
            ("Continuación con respuestas parciales", self.test_partial_responses),
            ("Monitoreo de salud del sistema", self.test_health_monitoring),
            ("Análisis de métricas detalladas", self.test_detailed_metrics),
            ("Prueba de estrés con múltiples consultas", self.test_stress_multiple_queries)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 Ejecutando: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                start_time = time.time()
                result = await test_func()
                duration = time.time() - start_time
                
                self.test_results.append({
                    'test': test_name,
                    'status': 'PASS' if result else 'FAIL',
                    'duration_ms': int(duration * 1000),
                    'details': result
                })
                
                status_emoji = "✅" if result else "❌"
                logger.info(f"{status_emoji} {test_name}: {'PASS' if result else 'FAIL'} ({duration:.2f}s)")
                
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
                self.test_results.append({
                    'test': test_name,
                    'status': 'ERROR',
                    'duration_ms': 0,
                    'error': str(e)
                })
        
        # Resumen final
        await self.print_test_summary()
    
    async def test_successful_query(self) -> bool:
        """Prueba una consulta básica exitosa"""
        query = QueryRequest(
            user_question="¿Qué es la inteligencia artificial?",
            query_type=QueryType.SIMPLE,
            project_id=uuid4(),
            user_id=uuid4(),
            max_tokens=100,
            temperature=0.7
        )
        
        response = await self.query_service.process_query(query)
        
        # Verificaciones
        checks = [
            response.ai_responses is not None,
            len(response.ai_responses) > 0,
            response.processing_time_ms > 0,
            response.metadata is not None,
            any(r.status.value == "success" for r in response.ai_responses)
        ]
        
        logger.info(f"Respuestas recibidas: {len(response.ai_responses)}")
        logger.info(f"Tiempo de procesamiento: {response.processing_time_ms}ms")
        logger.info(f"Proveedores exitosos: {response.metadata.get('successful_responses', 0)}")
        
        return all(checks)
    
    async def test_context_aware_query(self) -> bool:
        """Prueba consulta con búsqueda de contexto"""
        query = QueryRequest(
            user_question="¿Cómo funciona FastAPI?",
            query_type=QueryType.CONTEXT_AWARE,
            project_id=uuid4(),
            user_id=uuid4(),
            context_config=ContextConfig(
                top_k=3,
                similarity_threshold=0.3,
                max_context_length=1000
            ),
            max_tokens=150
        )
        
        response = await self.query_service.process_query(query)
        
        # Verificaciones
        checks = [
            response.ai_responses is not None,
            response.processing_time_ms > 0,
            response.metadata.get('has_context') == True,
            # El contexto puede o no encontrarse, pero no debe fallar
            True
        ]
        
        logger.info(f"Contexto encontrado: {response.context_info is not None}")
        if response.context_info:
            logger.info(f"Chunks de contexto: {response.context_info.total_chunks}")
            logger.info(f"Similitud promedio: {response.context_info.avg_similarity:.3f}")
        
        return all(checks)
    
    async def test_timeout_handling(self) -> bool:
        """Prueba manejo de timeouts"""
        # Configurar timeout muy bajo para forzar timeouts
        original_timeout = settings.DEFAULT_AI_TIMEOUT
        settings.DEFAULT_AI_TIMEOUT = 1  # 1 segundo
        
        try:
            query = QueryRequest(
                user_question="Explica detalladamente la teoría de la relatividad de Einstein, incluyendo todos los conceptos matemáticos y físicos involucrados.",
                query_type=QueryType.SIMPLE,
                project_id=uuid4(),
                user_id=uuid4(),
                max_tokens=2000,  # Respuesta larga para aumentar probabilidad de timeout
                temperature=0.7
            )
            
            response = await self.query_service.process_query(query)
            
            # Verificar que el sistema manejó timeouts correctamente
            timeout_responses = [r for r in response.ai_responses if r.status.value == "timeout"]
            successful_responses = [r for r in response.ai_responses if r.status.value == "success"]
            
            logger.info(f"Respuestas con timeout: {len(timeout_responses)}")
            logger.info(f"Respuestas exitosas: {len(successful_responses)}")
            logger.info(f"Total de respuestas: {len(response.ai_responses)}")
            
            # El sistema debe continuar funcionando incluso con timeouts
            checks = [
                len(response.ai_responses) > 0,
                response.processing_time_ms > 0,
                response.metadata is not None,
                # Al menos debe intentar con todos los proveedores
                len(response.ai_responses) >= len(response.providers_used)
            ]
            
            return all(checks)
            
        finally:
            # Restaurar timeout original
            settings.DEFAULT_AI_TIMEOUT = original_timeout
    
    async def test_partial_responses(self) -> bool:
        """Prueba continuación con respuestas parciales"""
        query = QueryRequest(
            user_question="¿Cuáles son las mejores prácticas de programación?",
            query_type=QueryType.SIMPLE,
            project_id=uuid4(),
            user_id=uuid4(),
            ai_providers=[AIProviderEnum.OPENAI, AIProviderEnum.ANTHROPIC],  # Especificar ambos
            max_tokens=100
        )
        
        response = await self.query_service.process_query(query)
        
        # Analizar respuestas
        successful = [r for r in response.ai_responses if r.status.value == "success"]
        failed = [r for r in response.ai_responses if r.status.value != "success"]
        
        logger.info(f"Respuestas exitosas: {len(successful)}")
        logger.info(f"Respuestas fallidas: {len(failed)}")
        
        # Verificar que el sistema funciona incluso con fallos parciales
        checks = [
            len(response.ai_responses) > 0,
            response.metadata.get('success_rate') is not None,
            response.metadata.get('error_analysis') is not None,
            # El sistema debe reportar métricas incluso con fallos
            True
        ]
        
        # Log de análisis de errores
        if response.metadata.get('error_analysis'):
            logger.info(f"Análisis de errores: {response.metadata['error_analysis']}")
        
        return all(checks)
    
    async def test_health_monitoring(self) -> bool:
        """Prueba el sistema de monitoreo de salud"""
        # Generar reporte de salud
        health_report = await self.health_monitor.get_system_health()
        
        logger.info(f"Estado general del sistema: {health_report.overall_status}")
        logger.info(f"Proveedores monitoreados: {len(health_report.providers)}")
        
        for provider_health in health_report.providers:
            logger.info(f"  {provider_health.provider.value}: {provider_health.status.value}")
            if provider_health.avg_latency_ms:
                logger.info(f"    Latencia promedio: {provider_health.avg_latency_ms}ms")
            if provider_health.success_rate_24h is not None:
                logger.info(f"    Tasa de éxito 24h: {provider_health.success_rate_24h:.1%}")
        
        # Realizar health checks activos
        health_checks = await self.health_monitor.perform_health_checks()
        
        logger.info("Health checks activos:")
        for provider, is_healthy in health_checks.items():
            status = "✅ HEALTHY" if is_healthy else "❌ UNHEALTHY"
            logger.info(f"  {provider.value}: {status}")
        
        # Verificar alertas
        alerts = self.health_monitor.get_system_alerts()
        if alerts:
            logger.warning(f"Alertas activas: {len(alerts)}")
            for alert in alerts:
                logger.warning(f"  [{alert['level'].upper()}] {alert['message']}")
        else:
            logger.info("No hay alertas activas")
        
        # Verificaciones
        checks = [
            health_report.overall_status is not None,
            len(health_report.providers) > 0,
            health_report.summary is not None,
            isinstance(health_checks, dict),
            len(health_checks) > 0
        ]
        
        return all(checks)
    
    async def test_detailed_metrics(self) -> bool:
        """Prueba métricas detalladas en respuestas"""
        query = QueryRequest(
            user_question="¿Qué es machine learning?",
            query_type=QueryType.SIMPLE,
            project_id=uuid4(),
            user_id=uuid4(),
            max_tokens=100
        )
        
        response = await self.query_service.process_query(query)
        
        # Verificar métricas detalladas
        metadata = response.metadata
        
        logger.info("Métricas detalladas:")
        logger.info(f"  Tasa de éxito: {metadata.get('success_rate', 0):.1%}")
        logger.info(f"  Proveedores intentados: {metadata.get('providers_attempted', [])}")
        logger.info(f"  Respuestas exitosas: {metadata.get('successful_responses', 0)}")
        logger.info(f"  Respuestas fallidas: {metadata.get('failed_responses', 0)}")
        
        if metadata.get('latency_stats'):
            stats = metadata['latency_stats']
            logger.info(f"  Latencia mín/prom/máx: {stats.get('min_latency_ms', 0)}/{stats.get('avg_latency_ms', 0)}/{stats.get('max_latency_ms', 0)}ms")
        
        if metadata.get('retry_info'):
            logger.info(f"  Información de reintentos: {metadata['retry_info']}")
        
        # Verificaciones
        required_fields = [
            'total_providers', 'successful_responses', 'failed_responses',
            'success_rate', 'providers_attempted'
        ]
        
        checks = [
            all(field in metadata for field in required_fields),
            isinstance(metadata.get('success_rate'), (int, float)),
            isinstance(metadata.get('providers_attempted'), list),
            metadata.get('total_providers', 0) >= 0
        ]
        
        return all(checks)
    
    async def test_stress_multiple_queries(self) -> bool:
        """Prueba de estrés con múltiples consultas concurrentes"""
        logger.info("Ejecutando 5 consultas concurrentes...")
        
        queries = [
            QueryRequest(
                user_question=f"Pregunta de prueba número {i+1}: ¿Qué es la programación?",
                query_type=QueryType.SIMPLE,
                project_id=uuid4(),
                user_id=uuid4(),
                max_tokens=50
            )
            for i in range(5)
        ]
        
        # Ejecutar consultas en paralelo
        start_time = time.time()
        responses = await asyncio.gather(
            *[self.query_service.process_query(q) for q in queries],
            return_exceptions=True
        )
        total_time = time.time() - start_time
        
        # Analizar resultados
        successful_queries = 0
        total_ai_responses = 0
        total_successful_ai_responses = 0
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Consulta {i+1} falló: {response}")
            else:
                successful_queries += 1
                total_ai_responses += len(response.ai_responses)
                total_successful_ai_responses += response.metadata.get('successful_responses', 0)
        
        logger.info(f"Consultas exitosas: {successful_queries}/5")
        logger.info(f"Tiempo total: {total_time:.2f}s")
        logger.info(f"Respuestas de IA totales: {total_ai_responses}")
        logger.info(f"Respuestas de IA exitosas: {total_successful_ai_responses}")
        
        # Verificaciones
        checks = [
            successful_queries > 0,  # Al menos una consulta debe ser exitosa
            total_time < 60,  # No debe tomar más de 1 minuto
            total_ai_responses > 0
        ]
        
        return all(checks)
    
    async def print_test_summary(self):
        """Imprime resumen de todas las pruebas"""
        logger.info(f"\n{'='*80}")
        logger.info("📊 RESUMEN DE PRUEBAS DE MANEJO ROBUSTO DE ERRORES")
        logger.info(f"{'='*80}")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        logger.info(f"Total de pruebas: {total_tests}")
        logger.info(f"✅ Exitosas: {passed_tests}")
        logger.info(f"❌ Fallidas: {failed_tests}")
        logger.info(f"💥 Errores: {error_tests}")
        logger.info(f"📈 Tasa de éxito: {passed_tests/total_tests:.1%}")
        
        logger.info(f"\nDetalle de pruebas:")
        for result in self.test_results:
            status_emoji = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}[result['status']]
            logger.info(f"  {status_emoji} {result['test']}: {result['status']} ({result['duration_ms']}ms)")
        
        # Cerrar recursos
        await self.query_service.close()

async def main():
    """Función principal"""
    tester = RobustErrorHandlingTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 