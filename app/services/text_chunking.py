"""
Servicio para chunking de texto plano.
"""
import logging
from typing import List, Dict, Any

from app.infra.job_repository import JobRepository
from app.infra.event_bus import get_event_bus
from app.domain.events import TextChunkedEvent, PdfIngestFailedEvent

logger = logging.getLogger(__name__)


def _chunk_text(text: str, size: int) -> List[str]:
    """Divide texto en chunks de tamaño fijo"""
    return [
        text[i : i + size]
        for i in range(0, len(text), size)
    ]


class TextChunkingService:
    """Servicio para dividir texto plano en chunks"""
    
    def __init__(
        self,
        job_repo: JobRepository,
    ):
        self.job_repo = job_repo
        self.event_bus = get_event_bus()
    
    async def execute(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        collection: str,
        text: str,
        chunk_size: int = 500,
    ) -> None:
        """
        Dividir texto en chunks.
        
        Args:
            job_id: ID del job
            user_id: ID del usuario
            project_id: ID del proyecto
            collection: Nombre de la colección
            text: Texto completo a dividir
            chunk_size: Tamaño de cada chunk
        
        Raises:
            Exception: Si falla el chunking
        """
        try:
            logger.info(f"📦 Starting text chunking: job_id={job_id}, text_length={len(text)}")
            
            # Actualizar estado del job
            self.job_repo.update_status(job_id, "chunking", progress=30)
            
            # Dividir texto en chunks
            chunks = _chunk_text(text, chunk_size)
            
            logger.info(f"✅ Text chunked: job_id={job_id}, chunks={len(chunks)}")
            
            # Validar que hay chunks
            if not chunks:
                raise ValueError("No se pudieron crear chunks del texto")
            
            # Crear metadata para cada chunk
            chunk_metadata = []
            for i, chunk in enumerate(chunks):
                chunk_metadata.append({
                    "chunk_index": i,
                    "chunk_size": len(chunk),
                    "source_type": "text",
                })
            
            # Publicar evento de chunks
            await self.event_bus.publish(TextChunkedEvent(
                job_id=job_id,
                user_id=user_id,
                project_id=project_id,
                collection=collection,
                chunks=chunks,
                chunk_metadata=chunk_metadata,
            ))
            
            # Actualizar progreso
            self.job_repo.update_status(
                job_id,
                "chunking",
                progress=50,
                result={
                    "chunks_created": len(chunks)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Text chunking failed: job_id={job_id}, error={e}", exc_info=True)
            self.job_repo.update_status(job_id, "failed", error=f"Chunking failed: {str(e)}")
            
            await self.event_bus.publish(PdfIngestFailedEvent(
                user_id=user_id,
                project_id=project_id,
                collection=collection,
                job_id=job_id,
                stage="chunking",
                error_message=str(e),
            ))
            
            raise
