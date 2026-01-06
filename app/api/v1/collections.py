import logging

from fastapi import APIRouter, Header, HTTPException, status, Depends, Query

from app.config import settings
from app.infra.gemini_embeddings import GeminiEmbeddingProvider
from app.infra.gemini_llm import GeminiLLMProvider
from app.models.requests import InsertCollectionRequest, CollectionQueryRequest, CollectionIngestRequest
from app.services.insert_collection import InsertCollectionService
from app.services.upsert_document import UpsertDocumentService
from app.services.delete_document import DeleteDocumentService
from app.services.get_document import GetDocumentService
from app.infra.api_key_repository import ApiKeyRepository
from app.services.get_collection import GetCollectionService
from app.models.responses import ListDocumentsResponse, CollectionQueryResponse
from app.services.rag_ingest import RagIngestService
from app.services.rag_query import RagQueryService

router = APIRouter()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_insert_collection_service() -> InsertCollectionService:
    return InsertCollectionService(ApiKeyRepository())

def get_get_collection_service() -> GetCollectionService:
    return GetCollectionService(ApiKeyRepository())

def get_upsert_document_service() -> UpsertDocumentService:
    return UpsertDocumentService(ApiKeyRepository())

def get_delete_document_service() -> DeleteDocumentService:
    return DeleteDocumentService(ApiKeyRepository())

def get_get_document_service() -> GetDocumentService:
    return GetDocumentService(ApiKeyRepository())

@router.post(
    "/{collection}",
    status_code=status.HTTP_201_CREATED
)
def insert_collection(
    collection: str,
    payload: InsertCollectionRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: InsertCollectionService = Depends(get_insert_collection_service),
):
    try:
        return service.execute(
            api_key=x_api_key,
            collection=collection,
            payload=payload.data,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

@router.get(
    "/{collection}",
    response_model=ListDocumentsResponse,
)
def get_collection(
    collection: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: GetCollectionService = Depends(get_get_collection_service),
):
    try:
        return service.execute(
            api_key=x_api_key,
            collection=collection,
            limit=limit,
            offset=offset,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    except RuntimeError:
        raise HTTPException(status_code=410, detail="Project expired")


@router.get("/{collection}/{document_id}")
def get_document(
    collection: str,
    document_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: GetDocumentService = Depends(get_get_document_service),
):
    """Obtener un documento específico por ID"""
    try:
        return service.execute(
            api_key=x_api_key,
            collection=collection,
            document_id=document_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=410, detail="Project expired")


@router.put("/{collection}/{document_id}")
def upsert_document(
    collection: str,
    document_id: str,
    payload: InsertCollectionRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: UpsertDocumentService = Depends(get_upsert_document_service),
):
    """
    Upsert estilo Firebase: crea si no existe, actualiza si existe.
    Similar a Firebase's set() con merge.
    """
    try:
        return service.execute(
            api_key=x_api_key,
            collection=collection,
            document_id=document_id,
            payload=payload.data,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    except RuntimeError:
        raise HTTPException(status_code=410, detail="Project expired")


@router.delete("/{collection}/{document_id}")
def delete_document(
    collection: str,
    document_id: str,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: DeleteDocumentService = Depends(get_delete_document_service),
):
    """Eliminar un documento por ID"""
    try:
        return service.execute(
            api_key=x_api_key,
            collection=collection,
            document_id=document_id,
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=410, detail="Project expired")


def get_rag_ingest_service() -> RagIngestService:
    return RagIngestService(
        embedding_provider=GeminiEmbeddingProvider(settings.gemini_api_key),
        api_key_repo=ApiKeyRepository(),
    )

def get_rag_query_service() -> RagQueryService:
    return RagQueryService(
        embedding_provider=GeminiEmbeddingProvider(settings.gemini_api_key),
        llm_provider=GeminiLLMProvider(settings.gemini_api_key),
        api_key_repo=ApiKeyRepository(),
    )

@router.post("/{collection}/ingest")
async def collection_ingest(
    collection: str,
    payload: CollectionQueryRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: RagIngestService = Depends(get_rag_ingest_service),
):
    logger.info(f"RAG ingest requested for collection '{collection}' by API key")
    logger.debug(f"Payload: {payload.model_dump_json()}")

    try:
        result = await service.execute(
            api_key=x_api_key,
            collection=collection,
            text=payload.text,
            chunk_size=payload.chunk_size,
            document_id=getattr(payload, "document_id", None),
            metadata=getattr(payload, "metadata", None)
        )
        logger.info(f"RAG ingest completed: {result['chunks_inserted']} chunks inserted.")
        return result
    except ValueError:
        logger.warning("Invalid API Key")
        raise HTTPException(status_code=401, detail="Invalid API Key")
    except RuntimeError:
        logger.warning("Project expired")
        raise HTTPException(status_code=410, detail="Project expired")
    except Exception as e:
        logger.error(f"Unexpected error during RAG ingest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{collection}/query", response_model=CollectionQueryResponse)
async def collection_query(
    collection: str,
    payload: CollectionIngestRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    service: RagQueryService = Depends(get_rag_query_service),
):
    logger.info(f"RAG query requested for collection '{collection}' by API key")
    logger.debug(f"Query Payload: {payload.model_dump_json()}")

    try:
        result = await service.execute(
            api_key=x_api_key,
            collection=collection,
            query=payload.query,
            top_k=payload.top_k,
        )
        logger.info(f"RAG query completed, {len(result['sources'])} documents retrieved.")
        return result
    except ValueError as e:
        logger.warning(f"Invalid API Key: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        logger.warning(f"Project expired: {e}")
        raise HTTPException(status_code=410, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))