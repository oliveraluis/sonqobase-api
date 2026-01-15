from datetime import datetime, timezone
from typing import Dict, Any, List
import time
import logging

from app.domain.embeddings import EmbeddingProvider

from app.domain.llm import LLMProvider
from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client
from app.infra.event_bus import get_event_bus
from app.domain.events import RagQueryExecutedEvent

logger = logging.getLogger(__name__)


class RagQueryService:
    def __init__(
            self,
            embedding_provider: EmbeddingProvider,
            llm_provider: LLMProvider,
    ):
        self.embedding_provider = embedding_provider
        self.llm_provider = llm_provider

    async def execute(
            self,
            project: "Project",
            collection: str,
            query: str,
            top_k: int = 5,
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        db_name = project.database.name
        # expired check handled in dependency

        query_embedding: List[float] = await self.embedding_provider.embed(query)

        client = get_mongo_client()
        db = client[db_name]
        vector_collection = db[f"{collection}"] # Fixed typo: should match ingest collection name

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "default_vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                    "exact": False,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "text": 1,
                    "document_id": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"}
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
            user_id=project.user_id,
            project_id=project.id,
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
                "project_id": project.id,
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
        
        
        # Convert markdown to plain text for API consumers who don't want formatting
        answer_plain = self._markdown_to_plain(answer)
        
        return {
            "answer": {
                "markdown": answer,  # Formatted with markdown (for dashboard)
                "plain": answer_plain,  # Plain text version (for API consumers)
            },
            "format_legend": {
                "available_formats": ["markdown", "plain"],
                "syntax": {
                    "**text**": "Texto en negrita (conceptos clave)",
                    "• item": "Lista con viñetas",
                    "\n\n": "Separación de párrafos"
                },
                "usage": {
                    "dashboard": "Use answer.markdown para formato enriquecido",
                    "api": "Use answer.plain para integración simple"
                }
            },
            "sources": [
                {
                   "text": r["text"],
                   "score": r.get("score"),
                   "document_id": r.get("document_id"),
                   "metadata": r.get("metadata", {})
                }
                for r in results
            ]
        }
    
    def _markdown_to_plain(self, markdown_text: str) -> str:
        """
        Convert markdown formatted text to plain text.
        Removes markdown syntax while preserving readability.
        """
        import re
        
        # Remove bold markers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', markdown_text)
        
        # Convert bullet points to simple dashes
        text = re.sub(r'•\s*', '- ', text)
        
        # Keep paragraph breaks
        text = text.strip()
        
        return text
