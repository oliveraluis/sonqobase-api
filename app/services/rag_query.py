from datetime import datetime, timezone
from typing import Dict, Any, List
import time

from app.domain.embeddings import EmbeddingProvider

from app.domain.llm import LLMProvider
from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client
from app.infra.event_bus import get_event_bus
from app.domain.events import RagQueryExecutedEvent


class RagQueryService:
    def __init__(
            self,
            embedding_provider: EmbeddingProvider,
            llm_provider: LLMProvider,
            api_key_repo: ApiKeyRepository,
    ):
        self.embedding_provider = embedding_provider
        self.llm_provider = llm_provider
        self.api_key_repo = api_key_repo

    async def execute(
            self,
            api_key: str,
            collection: str,
            query: str,
            top_k: int = 5,
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        project = self.api_key_repo.get_project_by_key(api_key)

        if not project:
            raise ValueError("Invalid API key")

        # MongoDB devuelve datetimes naive, convertir a aware
        expires_at = project["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < datetime.now(timezone.utc):
            raise RuntimeError("Project expired")

        query_embedding: List[float] = await self.embedding_provider.embed(query)

        client = get_mongo_client()
        db = client[project["database"]]
        vector_collection = db[f"{collection}_vectors"]

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "default_vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                    "exact": False,
                    # "filter": {...},                      # si quieres filtrar por metadata/document_id
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "document_id": 1,
                    "metadata": 1
                }
            },
        ]
        results = list(vector_collection.aggregate(pipeline))

        if not results:
            return {
                "answer": "No relevant information found.",
                "sources": [],
            }

        context = "\n\n".join(
            f"- {doc['text']}" for doc in results
        )

        prompt = f"""Eres un asistente de IA experto en analizar documentos y responder preguntas de manera clara, concisa y NEUTRAL.

INSTRUCCIONES:
1. Responde ÚNICAMENTE basándote en el contexto proporcionado
2. Si la información no está en el contexto, di claramente "No encontré información sobre esto en los documentos"
3. Sé conciso pero completo - máximo 3-4 párrafos
4. Usa formato markdown para mejorar la legibilidad:
   - Usa **negritas** para conceptos clave
   - Usa listas con viñetas (•) para enumerar puntos
   - Separa ideas en párrafos cortos
5. Responde en español de manera profesional y directa
6. Si hay múltiples aspectos en la pregunta, organiza la respuesta por secciones

NEUTRALIDAD OBLIGATORIA:
- Mantén una postura COMPLETAMENTE NEUTRAL e IMPARCIAL
- NO expreses opiniones personales ni juicios de valor
- En temas políticos, religiosos o controversiales: presenta SOLO los hechos del contexto sin sesgo
- Si el contexto presenta múltiples perspectivas, menciónalas todas de manera equilibrada
- Evita lenguaje emotivo o cargado - usa términos objetivos y descriptivos

CONTEXTO:
{context}

PREGUNTA:
{query}

RESPUESTA:"""

        answer: str = await self.llm_provider.generate(prompt)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Emit event for audit tracking
        event_bus = get_event_bus()
        await event_bus.publish(RagQueryExecutedEvent(
            user_id=project["user_id"],
            project_id=project["project_id"],
            collection=collection,
            query=query,
            results_count=len(results),
            response_time_ms=response_time_ms,
        ))

        # Audit log: guardar la consulta RAG en historial (2 días de retención)
        try:
            queries_history = db["queries_history"]
            
            # Crear índices si no existen (solo se ejecuta una vez)
            try:
                queries_history.create_index("project_id")
                queries_history.create_index("timestamp")
                queries_history.create_index([("project_id", 1), ("timestamp", -1)])
                # TTL index: eliminar automáticamente después de 2 días
                queries_history.create_index("timestamp", expireAfterSeconds=172800)  # 2 días = 172800 segundos
            except Exception:
                # Índices ya existen, ignorar
                pass
            
            queries_history.insert_one({
                "project_id": project["project_id"],
                "collection": collection,
                "query": query,
                "answer": answer,
                "sources_count": len(results),
                "timestamp": datetime.now(timezone.utc),
                "response_time_ms": response_time_ms,
            })
        except Exception as e:
            # No fallar si el audit log falla
            logger.warning(f"Failed to save query history: {e}")
        
        return RagQueryResponse(
            answer=answer,
            sources=[
                RagSource(
                    text=r["text"],
                    score=r["score"],
                    document_id=r["document_id"],
                    metadata=r.get("metadata", {})
                )
                for r in results
            ]
        )
