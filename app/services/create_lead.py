"""
Servicio para crear leads de contacto.
"""
from datetime import datetime, timezone
import logging

from app.infra.lead_repository import LeadRepository
from app.domain.entities import Lead

logger = logging.getLogger(__name__)


class CreateLeadService:
    """Servicio para crear leads desde formulario de contacto"""
    
    def __init__(self, lead_repo: LeadRepository):
        self.lead_repo = lead_repo
    
    def execute(
        self,
        email: str,
        name: str,
        company: str | None,
        interest: str,
        plan_interest: str,
    ) -> dict:
        """
        Crear un nuevo lead.
        
        Args:
            email: Email del lead
            name: Nombre del lead
            company: Empresa (opcional)
            interest: Descripción de su interés
            plan_interest: Plan que le interesa
        
        Returns:
            Diccionario con información del lead creado
        
        Raises:
            ValueError: Si hay errores de validación
        """
        # Validaciones de negocio
        if not email or '@' not in email:
            raise ValueError("Email inválido")
        
        if not name or len(name.strip()) < 2:
            raise ValueError("Nombre debe tener al menos 2 caracteres")
        
        if not interest or len(interest.strip()) < 10:
            raise ValueError("Por favor describe tu interés con más detalle (mínimo 10 caracteres)")
        
        if plan_interest not in ['free', 'starter', 'pro']:
            raise ValueError("Plan inválido")
        
        # Crear lead
        lead = self.lead_repo.create(
            email=email.strip().lower(),
            name=name.strip(),
            company=company.strip() if company else None,
            interest=interest.strip(),
            plan_interest=plan_interest,
        )
        
        logger.info(f"New lead created: {email} - {plan_interest}")
        
        return {
            "email": lead.email,
            "name": lead.name,
            "plan_interest": lead.plan_interest,
            "created_at": lead.created_at.isoformat(),
        }
