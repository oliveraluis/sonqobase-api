"""
Strategy para ingesta de texto plano.
Refactorizado para usar pipeline asíncrono con jobs.
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
        plan: Optional[Any] = None,
    ) -> str:
        """
        Procesar texto usando pipeline asíncrono con jobs.
        
        Args:
            user_id: ID del usuario
            project_id: ID del proyecto
            collection: Nombre de la colección
            source: Texto a ingestar
            document_id: ID del documento (para ingesta progresiva)
            metadata: Metadatos adicionales
            chunk_size: Tamaño de chunks
            plan: Plan del usuario
        
        Returns:
            job_id: ID del trabajo
        """
        from app.infra.job_repository import JobRepository
        from app.infra.event_bus import get_event_bus
        from app.domain.events import TextIngestStartedEvent
        
        job_id = self._generate_job_id()
        doc_id = self._generate_document_id(document_id)
        plan_name = plan.name if plan else "Free"
        
        # Calcular tamaño del texto
        text_size_bytes = len(source.encode('utf-8'))
        
        logger.info(f"📝 Text ingest starting: job_id={job_id}, size={text_size_bytes} bytes")
        
        # 1. Crear job
        job_repo = JobRepository()
        job_repo.create(
            job_id=job_id,
            user_id=user_id,
            project_id=project_id,
            collection_name=collection,
            job_type="text_ingest",
            metadata={
                "text": source,  # Almacenar texto en metadata del job
                "size_bytes": text_size_bytes,
                "chunk_size": chunk_size,
                "document_id": doc_id,
                "plan_name": plan_name,
                "user_metadata": metadata or {}
            }
        )
        
        # 2. Publicar evento para iniciar pipeline asíncrono
        event_bus = get_event_bus()
        await event_bus.publish(TextIngestStartedEvent(
            user_id=user_id,
            project_id=project_id,
            collection=collection,
            text_size_bytes=text_size_bytes,
            job_id=job_id,
            chunk_size=chunk_size,
        ))
        
        logger.info(f"✅ Text ingest job created: job_id={job_id}")
        
        return job_id
