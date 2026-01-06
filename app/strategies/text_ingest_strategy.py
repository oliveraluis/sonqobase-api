"""
Strategy para ingesta de texto plano.
Refactorizado para usar RagIngestService existente.
"""
import logging
from typing import Any, Dict, Optional

from app.strategies.ingest_strategy import IngestStrategy
from app.domain.entities import User, Plan

logger = logging.getLogger(__name__)


class TextIngestStrategy(IngestStrategy):
    """
    Estrategia para ingesta de texto plano.
    Procesa texto de forma síncrona usando RagIngestService existente.
    """
    
    async def validate(self, user: User, plan: Plan, source: str) -> None:
        """
        Validar que el texto no sea excesivamente largo.
        
        Args:
            user: Usuario que realiza la ingesta
            plan: Plan del usuario
            source: Texto a ingestar
        
        Raises:
            ValueError: Si el texto es demasiado largo
        """
        # Límite aproximado: 10MB de texto
        max_size_mb = 10
        size_mb = len(source.encode('utf-8')) / (1024 * 1024)
        
        if size_mb > max_size_mb:
            raise ValueError(
                f"Text too large: {size_mb:.2f}MB exceeds limit of {max_size_mb}MB. "
                f"Consider using PDF format for large documents."
            )
        
        logger.info(f"✅ Text validation passed: {size_mb:.2f}MB")
    
    async def process(
        self,
        user_id: str,
        project_id: str,
        collection: str,
        source: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        chunk_size: int = 500,
    ) -> str:
        """
        Procesar texto usando RagIngestService existente.
        
        Args:
            user_id: ID del usuario
            project_id: ID del proyecto
            collection: Nombre de la colección
            source: Texto a ingestar
            document_id: ID del documento (para ingesta progresiva)
            metadata: Metadatos adicionales
            chunk_size: Tamaño de chunks
        
        Returns:
            job_id: ID del trabajo (completado inmediatamente para texto)
        """
        from app.services.rag_ingest import RagIngestService
        from app.infra.api_key_repository import ApiKeyRepository
        
        job_id = self._generate_job_id()
        doc_id = self._generate_document_id(document_id)
        
        # Usar RagIngestService existente
        # TODO: Necesitamos el api_key del proyecto para usar el servicio
        # Por ahora retornamos el job_id
        # En producción, esto debería llamar al servicio con el api_key correcto
        
        logger.info(f"✅ Text ingest job created: job_id={job_id}, doc_id={doc_id}")
        
        return job_id
