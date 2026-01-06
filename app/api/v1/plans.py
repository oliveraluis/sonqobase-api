"""
Endpoints públicos de planes (no requieren autenticación).
"""
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List

from app.infra.plan_repository import PlanRepository

router = APIRouter()
logger = logging.getLogger(__name__)


# Response Models
class PlanLimitsResponse(BaseModel):
    projects: int
    reads_per_month: int
    writes_per_month: int
    rag_queries_per_month: int
    pdf_max_size_mb: int
    retention_hours: int
    audit_retention_days: int


class PlanResponse(BaseModel):
    name: str
    display_name: str
    price_usd: float
    limits: PlanLimitsResponse
    features: List[str]


# Endpoints
@router.get("", response_model=List[PlanResponse])
async def list_plans():
    """
    Listar todos los planes disponibles.
    Endpoint público (no requiere autenticación).
    """
    plan_repo = PlanRepository()
    plans = plan_repo.get_all()
    
    return [
        PlanResponse(
            name=plan.name,
            display_name=plan.display_name,
            price_usd=plan.price_usd,
            limits=PlanLimitsResponse(
                projects=plan.projects_limit,
                reads_per_month=plan.reads_limit,
                writes_per_month=plan.writes_limit,
                rag_queries_per_month=plan.rag_queries_limit,
                pdf_max_size_mb=plan.pdf_max_size_mb,
                retention_hours=plan.retention_hours,
                audit_retention_days=plan.audit_retention_days,
            ),
            features=plan.features,
        )
        for plan in plans
    ]


@router.get("/{plan_name}", response_model=PlanResponse)
async def get_plan(plan_name: str):
    """
    Obtener detalles de un plan específico.
    Endpoint público (no requiere autenticación).
    """
    plan_repo = PlanRepository()
    plan = plan_repo.get_by_name(plan_name)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_name}' not found"
        )
    
    return PlanResponse(
        name=plan.name,
        display_name=plan.display_name,
        price_usd=plan.price_usd,
        limits=PlanLimitsResponse(
            projects=plan.projects_limit,
            reads_per_month=plan.reads_limit,
            writes_per_month=plan.writes_limit,
            rag_queries_per_month=plan.rag_queries_limit,
            pdf_max_size_mb=plan.pdf_max_size_mb,
            retention_hours=plan.retention_hours,
            audit_retention_days=plan.audit_retention_days,
        ),
        features=plan.features,
    )
