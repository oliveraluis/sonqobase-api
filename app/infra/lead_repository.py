"""
Repositorio para gestión de leads de contacto.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pymongo import DESCENDING

from app.domain.entities import Lead
from app.infra.mongo_client import get_mongo_client
from app.config import settings


class LeadRepository:
    """Repositorio para leads de contacto"""
    
    def create(self, email: str, name: str, company: Optional[str], interest: str, plan_interest: str) -> Lead:
        """
        Crear un nuevo lead.
        
        Args:
            email: Email del lead
            name: Nombre del lead
            company: Empresa (opcional)
            interest: Descripción de su interés
            plan_interest: Plan que le interesa
        
        Returns:
            Lead creado
        """
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        now = datetime.now(timezone.utc)
        
        lead_doc = {
            "email": email,
            "name": name,
            "company": company,
            "interest": interest,
            "plan_interest": plan_interest,
            "created_at": now,
            "status": "pending",
            "source": "landing_page",
        }
        
        meta_db.leads.insert_one(lead_doc)
        
        return Lead(
            email=email,
            name=name,
            company=company,
            interest=interest,
            plan_interest=plan_interest,
            created_at=now,
            status="pending",
            source="landing_page",
        )
    
    def get_all(self, limit: int = 100) -> List[dict]:
        """
        Obtener todos los leads.
        
        Args:
            limit: Número máximo de leads a retornar
        
        Returns:
            Lista de leads
        """
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        leads = meta_db.leads.find(
            {},
            {"_id": 0}
        ).sort("created_at", DESCENDING).limit(limit)
        
        return list(leads)
    
    def update_status(self, email: str, status: str) -> bool:
        """
        Actualizar el estado de un lead.
        
        Args:
            email: Email del lead
            status: Nuevo estado ("pending", "contacted", "converted")
        
        Returns:
            True si se actualizó, False si no se encontró
        """
        client = get_mongo_client()
        meta_db = client[settings.mongo_meta_db]
        
        result = meta_db.leads.update_one(
            {"email": email},
            {"$set": {"status": status}}
        )
        
        return result.modified_count > 0
