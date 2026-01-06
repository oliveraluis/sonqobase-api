from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class InsertCollectionRequest(BaseModel):
    data: Dict[str, Any]

class CollectionIngestRequest(BaseModel):
    query: str
    top_k: int = 5

class CollectionQueryRequest(BaseModel):
    text: str
    chunk_size: int = 500
    document_id: Optional[str] = None
    metadata: Optional[Dict] = None