from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any



class DatabaseResponse(BaseModel):
    name: str
    expires_at: datetime

class ApiKeyResponse(BaseModel):
    key: str

class ProjectResponse(BaseModel):
    id: str
    slug: str  # Identificador legible
    name: str
    description: str | None
    status: str
    expires_at: datetime
    database: DatabaseResponse
    api_key: ApiKeyResponse


class DocumentResponse(BaseModel):
    id: str
    data: Dict[str, Any]

class ListDocumentsResponse(BaseModel):
    items: List[DocumentResponse]
    limit: int
    offset: int

class CollectionSourceResponse(BaseModel):
    text: str


class CollectionQueryResponse(BaseModel):
    answer: str
    sources: List[CollectionSourceResponse]

