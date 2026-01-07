"""
Servicio para generación de embeddings.
"""
import logging
from typing import List, Dict, Any

from app.infra.gemini_embeddings import GeminiEmbeddingProvider
from app.infra.job_repository import JobRepository
from app.infra.event_bus import get_event_bus
from app.domain.events import EmbeddingsGeneratedEvent, PdfIngestFailedEvent

logger = logging.getLogger(__name__)


class EmbeddingGenerationService:
    """Servicio para generar embeddings de chunks de texto"""
    
    def __init__(
        self,
        embedding_provider: GeminiEmbeddingProvider,
        job_repo: JobRepository,
    ):
        self.embedding_provider = embedding_provider
        self.job_repo = job_repo
        self.event_bus = get_event_bus()
    
    async def execute(
        self,
        job_id: str,
        user_id: str,
        project_id: str,
        collection: str,
        chunks: List[str],
        chunk_metadata: List[Dict[str, Any]],
    ) -> None:
        """
        Generar embeddings para chunks de texto.
        
        Args:
            job_id: ID del job
            user_id: ID del usuario
            project_id: ID del proyecto
            collection: Nombre de la colección
            chunks: Lista de chunks de texto
            chunk_metadata: Metadata de cada chunk
        
        Raises:
            Exception: Si falla la generación de embeddings
        """
        try:
            logger.info(f"🔢 Starting embedding generation: job_id={job_id}, chunks={len(chunks)}")
            
            # 1. Actualizar estado del job
            self.job_repo.update_status(job_id, "generating_embeddings", progress=60)
            
            # 2. Generar embeddings en lotes (batch de 10 para optimizar)
            batch_size = 10
            all_embeddings = []
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                # Generar embeddings para el batch
                batch_embeddings = await self.embedding_provider.embed_batch(batch)
                all_embeddings.extend(batch_embeddings)
                
                # Actualizar progreso
                progress = 60 + int((i / len(chunks)) * 30)  # 60% a 90%
                self.job_repo.update_status(
                    job_id,
                    "generating_embeddings",
                    progress=progress,
                    result={
                        "pages_processed": chunk_metadata[0].get('pdf_pages', 0) if chunk_metadata else 0,
                        "chunks_created": len(chunks),
                        "embeddings_generated": len(all_embeddings)
                    }
                )
                
                logger.info(f"📊 Embeddings progress: {len(all_embeddings)}/{len(chunks)} ({progress}%)")
            
            logger.info(f"✅ Embeddings generated: job_id={job_id}, count={len(all_embeddings)}")
            
            # 3. Actualizar job
            self.job_repo.update_status(
                job_id,
                "generating_embeddings",
                progress=90,
                result={
                    "pages_processed": chunk_metadata[0].get('pdf_pages', 0) if chunk_metadata else 0,
                    "chunks_created": len(chunks),
                    "embeddings_generated": len(all_embeddings)
                }
            )
            
            # 4. Publicar evento de embeddings generados
            await self.event_bus.publish(EmbeddingsGeneratedEvent(
                job_id=job_id,
                user_id=user_id,
                project_id=project_id,
                collection=collection,
                embeddings=all_embeddings,
                chunks=chunks,
                metadata=chunk_metadata,
            ))
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: job_id={job_id}, error={e}", exc_info=True)
            
            # Actualizar job como fallido
            self.job_repo.update_status(
                job_id,
                "failed",
                error=f"Embedding generation failed: {str(e)}"
            )
            
            # Publicar evento de fallo
            await self.event_bus.publish(PdfIngestFailedEvent(
                user_id=user_id,
                project_id=project_id,
                collection=collection,
                job_id=job_id,
                stage="embedding",
                error_message=str(e),
            ))
            
            raise
