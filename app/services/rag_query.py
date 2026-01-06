from datetime import datetime, timezone
from typing import Dict, Any, List

from app.domain.embeddings import EmbeddingProvider

from app.domain.llm import LLMProvider
from app.infra.api_key_repository import ApiKeyRepository
from app.infra.mongo_client import get_mongo_client


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
        vector_collection = db[f"{collection}__vectors"]

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

        prompt = f"""
        You are an AI assistant.
        Answer the question using ONLY the context below.
        
        Context:
        {context}
        
        Question:
        {query}
        """

        answer: str = await self.llm_provider.generate(prompt)

        return {
            "answer": answer,
            "sources": results,
        }
