from datetime import datetime, timezone
from typing import Protocol, List, Optional
import hashlib

from app.config import settings
from app.domain.entities import Project, Database, ProjectStats
from app.infra.mongo_client import get_mongo_client
from app.utils.encryption import encrypt_api_key, decrypt_api_key


class ProjectRepositoryProtocol(Protocol):
    def save(self, project: Project, api_key: str) -> None: ...
    def slug_exists(self, slug: str) -> bool: ...


def _hash_api_key(api_key: str) -> str:
    """Hash API key usando SHA-256 para almacenamiento seguro"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def _project_from_doc(doc: dict) -> Project:
    """Convertir documento de MongoDB a entidad Project"""
    # Manejar stats (puede no existir en proyectos antiguos)
    stats_data = doc.get("stats", {})
    stats = ProjectStats(
        reads_count=stats_data.get("reads_count", 0),
        writes_count=stats_data.get("writes_count", 0),
        rag_queries_count=stats_data.get("rag_queries_count", 0),
        last_activity=stats_data.get("last_activity"),
    )
    
    return Project(
        id=doc["project_id"],
        user_id=doc["user_id"],
        slug=doc.get("slug", ""),
        name=doc["name"],
        description=doc.get("description"),
        status=doc["status"],
        expires_at=doc["expires_at"],
        database=Database(
            name=doc["database"],
            expires_at=doc["expires_at"],
        ),
        stats=stats,
    )


class ProjectRepository:
    def slug_exists(self, slug: str) -> bool:
        """Verificar si un slug ya está en uso"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        existing = meta_db.projects.find_one({"slug": slug})
        return existing is not None
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Obtener proyecto por ID"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        doc = meta_db.projects.find_one({"project_id": project_id})
        if not doc:
            return None
        
        return _project_from_doc(doc)
    
    def get_by_user(self, user_id: str) -> List[Project]:
        """Obtener todos los proyectos de un usuario"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        docs = meta_db.projects.find({"user_id": user_id}).sort("created_at", -1)
        return [_project_from_doc(doc) for doc in docs]
    
    def get_by_api_key(self, api_key: str) -> Optional[Project]:
        """Obtener proyecto por API key"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        api_key_hash = _hash_api_key(api_key)
        doc = meta_db.projects.find_one({"api_key_hash": api_key_hash})
        
        if not doc:
            return None
        
        return _project_from_doc(doc)
    
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
                "api_key_hash": _hash_api_key(api_key),  # Para validación
                "api_key_encrypted": encrypt_api_key(api_key),  # Para recuperación
                "database": project.database.name,
                "status": project.status,
                "expires_at": project.expires_at,
                "created_at": datetime.now(timezone.utc),
                # Inicializar stats
                "stats": {
                    "reads_count": 0,
                    "writes_count": 0,
                    "rag_queries_count": 0,
                    "last_activity": None,
                },
            }
        )

        # Crear índice único en slug (sparse permite null en docs antiguos)
        meta_db.projects.create_index("slug", unique=True, sparse=True)
        
        # La base de datos efímera se crea automáticamente
        # Las colecciones se crean dinámicamente cuando se insertan documentos

    
    def increment_reads(self, project_id: str, count: int = 1) -> None:
        """Incrementar contador de reads del proyecto"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        meta_db.projects.update_one(
            {"project_id": project_id},
            {
                "$inc": {"stats.reads_count": count},
                "$set": {"stats.last_activity": datetime.now(timezone.utc)}
            }
        )
    
    def increment_writes(self, project_id: str, count: int = 1) -> None:
        """Incrementar contador de writes del proyecto"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        meta_db.projects.update_one(
            {"project_id": project_id},
            {
                "$inc": {"stats.writes_count": count},
                "$set": {"stats.last_activity": datetime.now(timezone.utc)}
            }
        )
    
    def increment_rag_queries(self, project_id: str, count: int = 1) -> None:
        """Incrementar contador de RAG queries del proyecto"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        meta_db.projects.update_one(
            {"project_id": project_id},
            {
                "$inc": {"stats.rag_queries_count": count},
                "$set": {"stats.last_activity": datetime.now(timezone.utc)}
            }
        )
    
    def get_api_key(self, project_id: str) -> Optional[str]:
        """
        Obtener la API key desencriptada de un proyecto.
        Solo debe usarse para mostrar al usuario.
        
        Args:
            project_id: ID del proyecto
        
        Returns:
            API key en texto plano, o None si no existe
        """
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        doc = meta_db.projects.find_one(
            {"project_id": project_id},
            {"api_key_encrypted": 1}
        )
        
        if not doc or "api_key_encrypted" not in doc:
            return None
        
        try:
            return decrypt_api_key(doc["api_key_encrypted"])
        except Exception:
            # Si falla la desencriptación, retornar None
            return None
