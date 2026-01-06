"""
Repositorio para gestión de Master API Keys.
"""
from typing import Optional
import hashlib

from app.domain.entities import MasterKey
from app.infra.mongo_client import get_mongo_client
from app.config import settings


def _hash_api_key(api_key: str) -> str:
    """Hashear API key con SHA-256"""
    return hashlib.sha256(api_key.encode()).hexdigest()


class MasterKeyRepository:
    """Repositorio para validación de Master API Keys"""
    
    def validate(self, api_key: str) -> bool:
        """
        Validar si una Master API Key es válida y activa.
        
        Args:
            api_key: Master API key en texto plano
        
        Returns:
            True si es válida y activa, False en caso contrario
        """
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        api_key_hash = _hash_api_key(api_key)
        
        doc = meta_db.master_keys.find_one({
            "key_hash": api_key_hash,
            "is_active": True
        })
        
        return doc is not None
    
    def get_by_key(self, api_key: str) -> Optional[MasterKey]:
        """Obtener Master Key por API key"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        api_key_hash = _hash_api_key(api_key)
        
        doc = meta_db.master_keys.find_one(
            {"key_hash": api_key_hash},
            {"_id": 0}
        )
        
        if not doc:
            return None
        
        return self._to_entity(doc)
    
    def _to_entity(self, doc: dict) -> MasterKey:
        """Convertir documento a entidad"""
        from datetime import timezone
        
        created_at = doc["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        return MasterKey(
            key_hash=doc["key_hash"],
            description=doc["description"],
            permissions=doc["permissions"],
            created_at=created_at,
            is_active=doc.get("is_active", True),
        )
