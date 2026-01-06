from datetime import datetime, timezone
from typing import Protocol
import hashlib

from app.config import settings
from app.domain.entities import Project
from app.infra.mongo_client import get_mongo_client


class ProjectRepositoryProtocol(Protocol):
    def save(self, project: Project, api_key: str) -> None: ...
    def slug_exists(self, slug: str) -> bool: ...


def _hash_api_key(api_key: str) -> str:
    """Hash API key usando SHA-256 para almacenamiento seguro"""
    return hashlib.sha256(api_key.encode()).hexdigest()


class ProjectRepository:
    def slug_exists(self, slug: str) -> bool:
        """Verificar si un slug ya está en uso"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        existing = meta_db.projects.find_one({"slug": slug})
        return existing is not None
    
    def save(self, project: Project, api_key: str) -> None:
        client = get_mongo_client()

        meta_db = client[settings.mongo_meta_db]
        meta_db.projects.insert_one(
            {
                "project_id": project.id,
                "user_id": project.user_id,  # Relación con usuario
                "slug": project.slug,  # Identificador legible
                "name": project.name,
                "description": project.description,
                "api_key_hash": _hash_api_key(api_key),
                "database": project.database.name,
                "status": project.status,
                "expires_at": project.expires_at,
                "created_at": datetime.now(timezone.utc),
            }
        )

        # Crear índice único en slug (sparse permite null en docs antiguos)
        meta_db.projects.create_index("slug", unique=True, sparse=True)
        
        # La base de datos efímera se crea automáticamente
        # Las colecciones se crean dinámicamente cuando se insertan documentos

