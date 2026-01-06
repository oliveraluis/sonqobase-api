from datetime import datetime, timezone
from typing import Protocol
import hashlib

from app.config import settings
from app.domain.entities import Project
from app.infra.mongo_client import get_mongo_client


class ProjectRepositoryProtocol(Protocol):
    def save(self, project: Project, api_key: str) -> None: ...


def _hash_api_key(api_key: str) -> str:
    """Hash API key usando SHA-256 para almacenamiento seguro"""
    return hashlib.sha256(api_key.encode()).hexdigest()


class ProjectRepository:
    def save(self, project: Project, api_key: str) -> None:
        client = get_mongo_client()

        meta_db = client[settings.mongo_meta_db]
        meta_db.projects.insert_one(
            {
                "project_id": project.id,
                "name": project.name,
                "description": project.description,
                "api_key_hash": _hash_api_key(api_key),  # Almacenar hash, no texto plano
                "database": project.database.name,
                "status": project.status,
                "expires_at": project.expires_at,
                "created_at": datetime.now(timezone.utc),
            }
        )

        # La base de datos efímera se crea automáticamente
        # Las colecciones se crean dinámicamente cuando se insertan documentos

