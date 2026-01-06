"""
Repositorio para gestión de planes de suscripción.
"""
from typing import Optional, List

from app.domain.entities import Plan
from app.infra.mongo_client import get_mongo_client
from app.config import settings


class PlanRepository:
    """Repositorio para operaciones de lectura de planes"""
    
    def get_by_name(self, plan_name: str) -> Optional[Plan]:
        """Obtener plan por nombre"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        doc = meta_db.plans.find_one({"name": plan_name}, {"_id": 0})
        
        if not doc:
            return None
        
        return self._to_entity(doc)
    
    def get_all(self) -> List[Plan]:
        """Obtener todos los planes disponibles"""
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        docs = meta_db.plans.find({}, {"_id": 0})
        
        return [self._to_entity(doc) for doc in docs]
    
    def _to_entity(self, doc: dict) -> Plan:
        """Convertir documento de MongoDB a entidad Plan"""
        return Plan(
            name=doc["name"],
            display_name=doc["display_name"],
            price_usd=doc["price_usd"],
            projects_limit=doc["limits"]["projects"],
            reads_limit=doc["limits"]["reads_per_month"],
            writes_limit=doc["limits"]["writes_per_month"],
            rag_queries_limit=doc["limits"]["rag_queries_per_month"],
            pdf_max_size_mb=doc["limits"]["pdf_max_size_mb"],
            retention_hours=doc["limits"]["retention_hours"],
            audit_retention_days=doc["limits"]["audit_retention_days"],
            features=doc.get("features", []),
        )
