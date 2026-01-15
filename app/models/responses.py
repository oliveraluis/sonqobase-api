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


class AnswerFormats(BaseModel):
    """Answer in multiple formats"""
    markdown: str
    plain: str


class FormatLegend(BaseModel):
    """Documentation about available formats"""
    available_formats: List[str]
    syntax: Dict[str, str]
    usage: Dict[str, str]


class CollectionQueryResponse(BaseModel):
    answer: AnswerFormats
    format_legend: FormatLegend
    sources: List[CollectionSourceResponse]

