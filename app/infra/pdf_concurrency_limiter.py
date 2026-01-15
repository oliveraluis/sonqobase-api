"""
Rate limiter para controlar concurrencia de procesamiento de PDFs por plan.
"""
import asyncio
import logging
from typing import Dict
from app.domain.entities import Plan

logger = logging.getLogger(__name__)


class PdfConcurrencyLimiter:
    """
    Limita la cantidad de PDFs que se pueden procesar concurrentemente según el plan.
    
    Límites:
    - Free: 1 PDF a la vez (47MB RAM)
    - Starter: 2 PDFs a la vez (94MB RAM)
    - Pro: 5 PDFs a la vez (235MB RAM)
    """
    
    # Límites de concurrencia por plan
    LIMITS = {
        "Free": 1,
        "Starter": 2,
        "Pro": 5
    }
    
    def __init__(self):
        # Semaphores por plan
        self._semaphores: Dict[str, asyncio.Semaphore] = {
            plan_name: asyncio.Semaphore(limit)
            for plan_name, limit in self.LIMITS.items()
        }
        
        # Contadores actuales (para logging)
        self._current_counts: Dict[str, int] = {
            plan_name: 0
            for plan_name in self.LIMITS.keys()
        }
        
        logger.info(f"✅ PDF Concurrency Limiter initialized: {self.LIMITS}")
    
    def get_semaphore(self, plan_name: str) -> asyncio.Semaphore:
        """Obtener semaphore para un plan específico"""
        # Normalizar a title case (Pro, Free, Starter)
        normalized = plan_name.title()
        return self._semaphores.get(normalized, self._semaphores["Free"])
    
    def get_limit(self, plan_name: str) -> int:
        """Obtener límite de concurrencia para un plan"""
        normalized = plan_name.title()
        return self.LIMITS.get(normalized, 1)
    
    async def acquire(self, plan_name: str, job_id: str):
        """
        Adquirir permiso para procesar un PDF.
        
        Args:
            plan_name: Nombre del plan del usuario
            job_id: ID del job
        
        Raises:
            asyncio.TimeoutError: Si no se puede adquirir en tiempo razonable
        """
        # Normalizar a title case
        normalized = plan_name.title()
        
        semaphore = self.get_semaphore(normalized)
        limit = self.get_limit(normalized)
        
        # Intentar adquirir con timeout
        try:
            acquired = await asyncio.wait_for(
                semaphore.acquire(),
                timeout=0.1  # 100ms timeout
            )
            
            if acquired:
                self._current_counts[normalized] = self._current_counts.get(normalized, 0) + 1
                current = self._current_counts[normalized]
                
                logger.info(
                    f"📊 PDF processing slot acquired: "
                    f"plan={normalized}, current={current}/{limit}, job_id={job_id}"
                )
                return True
                
        except asyncio.TimeoutError:
            current = limit  # Asumimos que está al máximo
            logger.warning(
                f"⚠️  Límite de procesamiento de PDF alcanzado: "
                f"plan={normalized}, limit={limit}, job_id={job_id}"
            )
            raise ValueError(
                f"Demasiadas cargas de PDF concurrentes. "
                f"El plan '{normalized}' permite un máximo de {limit} cargas simultáneas. "
                f"Por favor espera a que se completen las cargas actuales o actualiza tu plan."
            )
    
    def release(self, plan_name: str, job_id: str):
        """
        Liberar permiso después de procesar un PDF.
        
        Args:
            plan_name: Nombre del plan del usuario
            job_id: ID del job
        """
        # Normalizar a title case
        normalized = plan_name.title()
        
        semaphore = self.get_semaphore(normalized)
        semaphore.release()
        
        self._current_counts[normalized] = max(0, self._current_counts.get(normalized, 0) - 1)
        current = self._current_counts[normalized]
        limit = self.get_limit(normalized)
        
        logger.info(
            f"✅ PDF processing slot released: "
            f"plan={normalized}, current={current}/{limit}, job_id={job_id}"
        )
    
    def get_stats(self) -> Dict[str, Dict]:
        """Obtener estadísticas de uso"""
        return {
            plan_name: {
                "limit": self.LIMITS[plan_name],
                "current": self._current_counts[plan_name],
                "available": self.LIMITS[plan_name] - self._current_counts[plan_name]
            }
            for plan_name in self.LIMITS.keys()
        }


# Instancia global singleton
_concurrency_limiter = None

def get_concurrency_limiter() -> PdfConcurrencyLimiter:
    """Obtener instancia global del limiter"""
    global _concurrency_limiter
    if _concurrency_limiter is None:
        _concurrency_limiter = PdfConcurrencyLimiter()
    return _concurrency_limiter
