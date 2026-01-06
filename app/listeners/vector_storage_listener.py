"""
Listener para almacenamiento de vectores en MongoDB.
Escucha EmbeddingsGeneratedEvent e inserta en la colección vectorial.
"""
import logging
from datetime import datetime, timezone

from pymongo import MongoClient, ASCENDING

from app.infra.event_bus import get_event_bus
from app.domain.events import EmbeddingsGeneratedEvent, PdfIngestCompletedEvent, PdfIngestFailedEvent
from app.infra.job_repository import JobRepository
from app.infra.pdf_storage import PdfStorage
from app.infra.vector_index import ensure_vector_index
from app.config import settings

logger = logging.getLogger(__name__)

# Obtener event bus global
event_bus = get_event_bus()

# Inicializar dependencias
client = MongoClient(settings.mongo_uri)
meta_db = client[settings.mongo_meta_db]
job_repo = JobRepository(meta_db)
pdf_storage = PdfStorage(meta_db)


@event_bus.subscribe(EmbeddingsGeneratedEvent)
async def on_embeddings_generated(event: EmbeddingsGeneratedEvent):
    """
    Listener que almacena embeddings en la colección vectorial.
    
    Pipeline: EmbeddingsGeneratedEvent → Insertar en MongoDB → PdfIngestCompletedEvent
    """
    job_id = event.job_id
    
    try:
        logger.info(f"💾 Starting vector storage: job_id={job_id}, vectors={len(event.embeddings)}")
        
        # 1. Actualizar estado del job
        job_repo.update_status(job_id, "storing", progress=95)
        
        # 2. Obtener job para información del proyecto
        job = job_repo.get(job_id)
        project_id = job['project_id']
        
        # 3. Obtener información del proyecto (incluyendo expires_at)
        project = meta_db.projects.find_one({"project_id": project_id})
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        # MongoDB devuelve datetimes naive, convertir a aware
        expires_at = project["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        # 4. Conectar a la base de datos efímera del proyecto
        ephemeral_db_name = project["database"]
        ephemeral_db = client[ephemeral_db_name]
        
        # 5. Colección vectorial: {collection}_vectors
        vector_collection_name = f"{event.collection}_vectors"
        vector_collection = ephemeral_db[vector_collection_name]
        
        # 6. Preparar documentos para inserción
        documents = []
        for i, (chunk, embedding, metadata) in enumerate(zip(event.chunks, event.embeddings, event.metadata)):
            doc = {
                "text": chunk,
                "embedding": embedding,
                "metadata": {
                    **metadata,
                    "source_type": "pdf",
                    "job_id": job_id,
                },
                "created_at": datetime.now(timezone.utc),
                "expires_at": expires_at,
            }
            documents.append(doc)
        
        # Validar que hay documentos
        if not documents:
            raise ValueError(
                f"No documents to insert. "
                f"chunks={len(event.chunks)}, embeddings={len(event.embeddings)}, metadata={len(event.metadata)}"
            )
        
        # 7. Insertar en batch
        result = vector_collection.insert_many(documents)
        inserted_count = len(result.inserted_ids)
        
        logger.info(f"✅ Vectors stored: job_id={job_id}, inserted={inserted_count}")
        
        # 8. Crear índice TTL para auto-limpieza
        try:
            vector_collection.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_expires_at",
            )
        except Exception:
            # Índice ya existe
            pass
        
        # 9. Crear índice vectorial si no existe (para MongoDB Atlas Vector Search)
        ensure_vector_index(ephemeral_db, vector_collection_name, num_dimensions=768)
        
        # 10. Actualizar job como completado
        job_repo.update_status(
            job_id,
            "completed",
            progress=100,
            result={
                "pages_processed": event.metadata[0].get('pdf_pages', 0) if event.metadata else 0,
                "chunks_created": len(event.chunks),
                "embeddings_generated": len(event.embeddings),
                "vectors_stored": inserted_count
            }
        )
        
        # 11. Publicar evento de ingesta completada
        # Calcular tiempo total desde creación del job
        job_created_at = job['created_at']
        
        # Asegurar que job_created_at tenga timezone
        if job_created_at.tzinfo is None:
            job_created_at = job_created_at.replace(tzinfo=timezone.utc)
        
        processing_time_ms = int((datetime.now(timezone.utc) - job_created_at).total_seconds() * 1000)
        
        await event_bus.publish(PdfIngestCompletedEvent(
            user_id=event.user_id,
            project_id=event.project_id,
            collection=event.collection,
            job_id=job_id,
            pages_processed=event.metadata[0].get('pdf_pages', 0) if event.metadata else 0,
            chunks_created=len(event.chunks),
            processing_time_ms=processing_time_ms,
        ))
        
        logger.info(f"🎉 PDF ingest completed: job_id={job_id}, time={processing_time_ms}ms")
        
    except Exception as e:
        logger.error(f"❌ Vector storage failed: job_id={job_id}, error={e}", exc_info=True)
        
        # Actualizar job como fallido
        job_repo.update_status(
            job_id,
            "failed",
            error=f"Vector storage failed: {str(e)}"
        )
        
        # Publicar evento de fallo
        await event_bus.publish(PdfIngestFailedEvent(
            user_id=event.user_id,
            project_id=event.project_id,
            collection=event.collection,
            job_id=job_id,
            stage="storage",
            error_message=str(e),
        ))
