"""
Listener para generación de embeddings.
Escucha PdfChunkedEvent y genera embeddings para cada chunk.
"""
import logging

from app.infra.event_bus import get_event_bus
from app.domain.events import PdfChunkedEvent, EmbeddingsGeneratedEvent, PdfIngestFailedEvent
from app.infra.gemini_embeddings import GeminiEmbeddingProvider
from app.infra.job_repository import JobRepository
from app.config import settings
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# Obtener event bus global
event_bus = get_event_bus()

# Inicializar dependencias
client = MongoClient(settings.mongo_uri)
meta_db = client[settings.mongo_meta_db]
embedding_provider = GeminiEmbeddingProvider(settings.gemini_api_key)
job_repo = JobRepository(meta_db)


@event_bus.subscribe(PdfChunkedEvent)
async def on_pdf_chunked(event: PdfChunkedEvent):
    """
    Listener que genera embeddings para los chunks.
    
    Pipeline: PdfChunkedEvent → Generar embeddings → EmbeddingsGeneratedEvent
    """
    job_id = event.job_id
    
    try:
        logger.info(f"🔢 Starting embedding generation: job_id={job_id}, chunks={len(event.chunks)}")
        
        # 1. Actualizar estado del job
        job_repo.update_status(job_id, "generating_embeddings", progress=60)
        
        # 2. Generar embeddings en lotes (batch de 10 para optimizar)
        batch_size = 10
        all_embeddings = []
        
        for i in range(0, len(event.chunks), batch_size):
            batch = event.chunks[i:i + batch_size]
            
            # Generar embeddings para el batch
            batch_embeddings = await embedding_provider.embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            
            # Actualizar progreso
            progress = 60 + int((i / len(event.chunks)) * 30)  # 60% a 90%
            job_repo.update_status(
                job_id,
                "generating_embeddings",
                progress=progress,
                result={
                    "pages_processed": event.chunk_metadata[0].get('pdf_pages', 0) if event.chunk_metadata else 0,
                    "chunks_created": len(event.chunks),
                    "embeddings_generated": len(all_embeddings)
                }
            )
            
            logger.info(f"📊 Embeddings progress: {len(all_embeddings)}/{len(event.chunks)} ({progress}%)")
        
        logger.info(f"✅ Embeddings generated: job_id={job_id}, count={len(all_embeddings)}")
        
        # 3. Actualizar job
        job_repo.update_status(
            job_id,
            "generating_embeddings",
            progress=90,
            result={
                "pages_processed": event.chunk_metadata[0].get('pdf_pages', 0) if event.chunk_metadata else 0,
                "chunks_created": len(event.chunks),
                "embeddings_generated": len(all_embeddings)
            }
        )
        
        # 4. Publicar evento de embeddings generados
        await event_bus.publish(EmbeddingsGeneratedEvent(
            job_id=job_id,
            user_id=event.user_id,
            project_id=event.project_id,
            collection=event.collection,
            embeddings=all_embeddings,
            chunks=event.chunks,
            metadata=event.chunk_metadata,
        ))
        
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: job_id={job_id}, error={e}", exc_info=True)
        
        # Actualizar job como fallido
        job_repo.update_status(
            job_id,
            "failed",
            error=f"Embedding generation failed: {str(e)}"
        )
        
        # Publicar evento de fallo
        await event_bus.publish(PdfIngestFailedEvent(
            user_id=event.user_id,
            project_id=event.project_id,
            collection=event.collection,
            job_id=job_id,
            stage="embedding",
            error_message=str(e),
        ))
