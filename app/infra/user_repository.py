"""
Repositorio para gestión de usuarios de SonqoBase.
"""
from datetime import datetime, timezone
from typing import Optional
import hashlib

from app.domain.entities import User, UsageStats
from app.infra.mongo_client import get_mongo_client
from app.config import settings


def _hash_api_key(api_key: str) -> str:
    """Hashear API key con SHA-256"""
    return hashlib.sha256(api_key.encode()).hexdigest()


class UserRepository:
    """Repositorio para operaciones CRUD de usuarios"""
    
    def save(self, user: User, plain_api_key: str) -> None:
        """
        Guardar usuario en base de datos.
        
        Args:
            user: Entidad User
            plain_api_key: API key en texto plano (solo se guarda el hash)
        """
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        meta_db.users.insert_one({
            "user_id": user.id,
            "email": user.email,
            "api_key_hash": _hash_api_key(plain_api_key),
            "plan_name": user.plan_name,
            "status": user.status,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "usage": {
                "projects_count": user.usage.projects_count,
                "reads_count": user.usage.reads_count,
                "writes_count": user.usage.writes_count,
                "rag_queries_count": user.usage.rag_queries_count,
                "period_start": user.usage.period_start,
                "period_end": user.usage.period_end,
            },
            "webhook_url": user.webhook_url,
        })
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Obtener usuario por ID"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        doc = meta_db.users.find_one({"user_id": user_id}, {"_id": 0})
        
        if not doc:
            return None
        
        return self._to_entity(doc)

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """
        Obtener usuario como diccionario por ID.
        Usado por servicios que esperan un dict en lugar de entidad.
        """
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        return meta_db.users.find_one({"user_id": user_id}, {"_id": 0})
    
    def get_by_api_key(self, api_key: str) -> Optional[User]:
        """Obtener usuario por API key (comparando hash)"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        api_key_hash = _hash_api_key(api_key)
        doc = meta_db.users.find_one({"api_key_hash": api_key_hash}, {"_id": 0})
        
        if not doc:
            return None
        
        return self._to_entity(doc)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        doc = meta_db.users.find_one({"email": email}, {"_id": 0})
        
        if not doc:
            return None
        
        return self._to_entity(doc)
    
    def update_status(self, user_id: str, status: str) -> None:
        """Actualizar estado del usuario (active, blocked, suspended)"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        meta_db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )
    
    def update_plan(self, user_id: str, plan_name: str) -> None:
        """Actualizar plan del usuario"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        meta_db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "plan_name": plan_name,
                    "updated_at": datetime.now(timezone.utc),
                }
            }
        )
    
    def increment_usage(
        self, 
        user_id: str, 
        reads: int = 0, 
        writes: int = 0, 
        rag_queries: int = 0,
        projects: int = 0,
    ) -> None:
        """Incrementar contadores de uso"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        increments = {}
        if reads > 0:
            increments["usage.reads_count"] = reads
        if writes > 0:
            increments["usage.writes_count"] = writes
        if rag_queries > 0:
            increments["usage.rag_queries_count"] = rag_queries
        if projects > 0:
            increments["usage.projects_count"] = projects
        
        if increments:
            meta_db.users.update_one(
                {"user_id": user_id},
                {"$inc": increments}
            )
    
    def _to_entity(self, doc: dict) -> User:
        """Convertir documento de MongoDB a entidad User"""
        usage_doc = doc.get("usage", {})
        
        # Manejar datetimes naive de MongoDB
        created_at = doc["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        updated_at = doc["updated_at"]
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        
        period_start = usage_doc.get("period_start")
        if period_start and period_start.tzinfo is None:
            period_start = period_start.replace(tzinfo=timezone.utc)
        
        period_end = usage_doc.get("period_end")
        if period_end and period_end.tzinfo is None:
            period_end = period_end.replace(tzinfo=timezone.utc)
        
        return User(
            id=doc["user_id"],
            email=doc["email"],
            api_key_hash=doc["api_key_hash"],
            plan_name=doc["plan_name"],
            status=doc["status"],
            created_at=created_at,
            updated_at=updated_at,
            usage=UsageStats(
                projects_count=usage_doc.get("projects_count", 0),
                reads_count=usage_doc.get("reads_count", 0),
                writes_count=usage_doc.get("writes_count", 0),
                rag_queries_count=usage_doc.get("rag_queries_count", 0),
                period_start=period_start,
                period_end=period_end,
            ),
            webhook_url=doc.get("webhook_url"),
        )
