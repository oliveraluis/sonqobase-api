from datetime import datetime, timezone
from typing import List
from uuid import uuid4
import asyncio

from pymongo import ASCENDING

from app.domain.embeddings import EmbeddingProvider
from app.infra.mongo_client import get_mongo_client
from app.infra.api_key_repository import ApiKeyRepository
from app.infra.vector_index import ensure_vector_index


def _chunk_text(text: str, size: int) -> List[str]:
    return [
        text[i : i + size]
        for i in range(0, len(text), size)
    ]


class RagIngestService:
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
    ):
        self.embedding_provider = embedding_provider

    async def execute(
        self,
        project: "Project",
        collection: str,
        text: str,
        chunk_size: int,
        document_id: str | None = None,
        metadata: dict | None = None
    ) -> dict:
        
        db_name = project.database.name
        # expires checking handled in dependency...

        chunks = _chunk_text(text, chunk_size)

        client = get_mongo_client()
        db = client[db_name]
        vector_collection_name = f"{collection}__vectors"
        vector_collection = db[vector_collection_name]

        doc_id = document_id or f"doc_{uuid4().hex[:8]}"
        
        # Generar todos los embeddings en paralelo (optimización de performance)
        embeddings = await asyncio.gather(*[
            self.embedding_provider.embed(chunk) for chunk in chunks
        ])
        
        # Preparar documentos para inserción masiva
        documents = [
            {
                "text": chunk,
                "embedding": embedding,
                "document_id": doc_id,
                "metadata": {
                    "chunk": idx,
                    **(metadata or {}),
                },
                "created_at": datetime.now(timezone.utc),
                "expires_at": project.expires_at,
            }
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        # Inserción masiva (mucho más eficiente)
        if documents:
            vector_collection.insert_many(documents)
        
        # Crear índice TTL para auto-limpieza
        try:
            vector_collection.create_index(
                [("expires_at", ASCENDING)],
                expireAfterSeconds=0,
                name="ttl_expires_at",
            )
        except Exception:
            # Índice ya existe
            pass
        
        # Crear índice vectorial para búsqueda
        ensure_vector_index(db, vector_collection_name)

        return {
            "document_id": doc_id,
            "chunks_inserted": len(documents),
            "collection": vector_collection_name,
        }

