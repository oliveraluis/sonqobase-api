import logging

from fastapi import APIRouter, Header, HTTPException, status, Depends, Query, UploadFile, File, Form, Request
from typing import Optional
import json

from app.config import settings
from app.infra.gemini_embeddings import GeminiEmbeddingProvider
from app.infra.gemini_llm import GeminiLLMProvider
from app.models.requests import InsertCollectionRequest, CollectionQueryRequest, CollectionIngestRequest
from app.services.insert_collection import InsertCollectionService
from app.services.upsert_document import UpsertDocumentService
from app.services.delete_document import DeleteDocumentService
from app.services.get_document import GetDocumentService
from app.services.get_collection import GetCollectionService
from app.models.responses import ListDocumentsResponse, CollectionQueryResponse
from app.services.rag_ingest import RagIngestService
from app.services.rag_query import RagQueryService
from app.strategies.pdf_ingest_strategy import PdfIngestStrategy
from app.strategies.text_ingest_strategy import TextIngestStrategy
from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository
from app.dependencies.project import get_project_context
from app.domain.entities import Project

router = APIRouter()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_insert_collection_service() -> InsertCollectionService:
    return InsertCollectionService()

def get_get_collection_service() -> GetCollectionService:
    return GetCollectionService()

def get_upsert_document_service() -> UpsertDocumentService:
    return UpsertDocumentService()

def get_delete_document_service() -> DeleteDocumentService:
    return DeleteDocumentService()

def get_get_document_service() -> GetDocumentService:
    return GetDocumentService()

@router.post(
    "/{collection}",
    status_code=status.HTTP_201_CREATED
)
def insert_collection(
    collection: str,
    payload: InsertCollectionRequest,
    project: Project = Depends(get_project_context),
    service: InsertCollectionService = Depends(get_insert_collection_service),
):
    try:
        return service.execute(
            project=project,
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
    project: Project = Depends(get_project_context),
    service: GetCollectionService = Depends(get_get_collection_service),
):
    try:
        return service.execute(
            project=project,
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
    project: Project = Depends(get_project_context),
    service: GetDocumentService = Depends(get_get_document_service),
):
    """Obtener un documento específico por ID"""
    try:
        return service.execute(
            project=project,
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
    project: Project = Depends(get_project_context),
    service: UpsertDocumentService = Depends(get_upsert_document_service),
):
    """
    Upsert estilo Firebase: crea si no existe, actualiza si existe.
    Similar a Firebase's set() con merge.
    """
    try:
        return service.execute(
            project=project,
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
    project: Project = Depends(get_project_context),
    service: DeleteDocumentService = Depends(get_delete_document_service),
):
    """Eliminar un documento por ID"""
    try:
        return service.execute(
            project=project,
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
    )

def get_rag_query_service() -> RagQueryService:
    return RagQueryService(
        embedding_provider=GeminiEmbeddingProvider(settings.gemini_api_key),
        llm_provider=GeminiLLMProvider(settings.gemini_api_key),
    )

@router.post("/{collection}/ingest")
async def collection_ingest(
    collection: str,
    payload: CollectionQueryRequest,
    project: Project = Depends(get_project_context),
    service: RagIngestService = Depends(get_rag_ingest_service),
):
    logger.info(f"RAG ingest requested for collection '{collection}'")
    logger.debug(f"Payload: {payload.model_dump_json()}")

    try:
        result = await service.execute(
            project=project,
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

# Nuevo endpoint para ingesta de archivos (PDFs)
@router.post(
    "/{collection}/ingest/files",
    status_code=status.HTTP_202_ACCEPTED
)
async def ingest_files(
    collection: str,
    request: Request,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
    chunk_size: int = Form(500),
):
    """
    Ingesta de archivos (PDFs).
    
    Parámetros:
    - file: Archivo PDF
    - metadata: Metadatos en formato JSON string
    - document_id: ID del documento (para ingesta progresiva)
    - chunk_size: Tamaño de chunks (default: 500)
    
    Requiere Project API Key o JWT + Project Context.
    """
    # Obtener información del middleware
    # CONTEXT REF: Hemos migrado a get_project_context, pero este endpoint es complejo
    # porque usa UploadFile y Form, lo que complica usar validación de header estandar.
    # Sin embargo, el Request ya tiene state.project_id si se usó Key en middleware?
    # NO. Middleware solo verifica, no inyecta dependencia.
    
    # Vamos a usar manualmente el dependency para resolver el proyecto
    project = await get_project_context(request)
    
    project_id = project.id
    user_id = project.user_id
    # user = request.state.user ?? No, get_project_context guarantees project access
    
    # Necesitamos el User entity para el rate limit. 
    # Project entity tiene user_id. 
    user_repo = UserRepository()
    user = user_repo.get_by_id(user_id)
    
    # Obtener plan del usuario
    plan_repo = PlanRepository()
    plan = plan_repo.get_by_name(user.plan_name)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plan configuration not found"
        )
    
    # Validar extensión
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported. Filename must end with .pdf"
        )
    
    # Parsear metadata
    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata JSON"
            )
    
    # Usar PdfIngestStrategy
    strategy = PdfIngestStrategy()
    
    try:
        # Validar según límites del plan
        await strategy.validate(user, plan, file)
        
        # Procesar PDF (pasar plan para metadata)
        job_id = await strategy.process(
            user_id=user_id,
            project_id=project_id,
            collection=collection,
            source=file,
            document_id=document_id,
            metadata=parsed_metadata,
            chunk_size=chunk_size,
            plan=plan,  # Pasar plan para rate limiting
        )
        
        logger.info(f"📄 PDF ingest started: job_id={job_id}, file={file.filename}")
        
        # Response con información para polling
        return {
            "job_id": job_id,
            "status": "processing",
            "collection": collection,
            "filename": file.filename,
            "message": "PDF is being processed. This may take a few minutes.",
            "check_status_url": f"/api/v1/jobs/{job_id}",
            "estimated_time_seconds": 45
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in PDF ingest: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during PDF ingestion"
        )

@router.post("/{collection}/query", response_model=CollectionQueryResponse)
async def collection_query(
    collection: str,
    payload: CollectionIngestRequest, # Note: This type hint seems wrong in original code (IngestRequest vs QueryRequest), but keeping as is to avoid side effects
    project: Project = Depends(get_project_context),
    service: RagQueryService = Depends(get_rag_query_service),
):
    logger.info(f"RAG query requested for collection '{collection}'")
    logger.debug(f"Query Payload: {payload.model_dump_json()}")

    try:
        result = await service.execute(
            project=project,
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