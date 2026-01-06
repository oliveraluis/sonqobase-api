"""
Endpoints de usuarios (requieren User API Key).
"""
import logging
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import List

from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository

router = APIRouter()
logger = logging.getLogger(__name__)


# Response Models
class UsageLimitResponse(BaseModel):
    count: int
    limit: int
    percentage: float


class UsageResponse(BaseModel):
    reads: UsageLimitResponse
    writes: UsageLimitResponse
    rag_queries: UsageLimitResponse


class ProjectSummary(BaseModel):
    active: int
    limit: int


class UserInfoResponse(BaseModel):
    user_id: str
    email: str
    plan: str
    status: str
    created_at: str


class AnalyticsResponse(BaseModel):
    user_id: str
    plan: str
    current_period: dict
    usage: UsageResponse
    projects: ProjectSummary


# Endpoints
@router.get("/me", response_model=UserInfoResponse)
async def get_user_info(request: Request):
    """
    Obtener información del usuario autenticado.
    Requiere User API Key.
    """
    # El middleware ya validó la autenticación
    if request.state.auth_level not in ["user", "master"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User API Key required"
        )
    
    user = request.state.user
    
    return UserInfoResponse(
        user_id=user.id,
        email=user.email,
        plan=user.plan_name,
        status=user.status,
        created_at=user.created_at.isoformat(),
    )


@router.get("/me/usage", response_model=AnalyticsResponse)
async def get_user_usage(request: Request):
    """
    Obtener uso actual y límites del usuario autenticado.
    Requiere User API Key.
    """
    if request.state.auth_level not in ["user", "master"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User API Key required"
        )
    
    user = request.state.user
    
    # Obtener plan para límites
    plan_repo = PlanRepository()
    plan = plan_repo.get_by_name(user.plan_name)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plan configuration not found"
        )
    
    # Calcular porcentajes
    def calc_percentage(count: int, limit: int) -> float:
        if limit == 0:
            return 0.0
        return round((count / limit) * 100, 2)
    
    return AnalyticsResponse(
        user_id=user.id,
        plan=user.plan_name,
        current_period={
            "start": user.usage.period_start.isoformat(),
            "end": user.usage.period_end.isoformat(),
        },
        usage=UsageResponse(
            reads=UsageLimitResponse(
                count=user.usage.reads_count,
                limit=plan.reads_limit,
                percentage=calc_percentage(user.usage.reads_count, plan.reads_limit),
            ),
            writes=UsageLimitResponse(
                count=user.usage.writes_count,
                limit=plan.writes_limit,
                percentage=calc_percentage(user.usage.writes_count, plan.writes_limit),
            ),
            rag_queries=UsageLimitResponse(
                count=user.usage.rag_queries_count,
                limit=plan.rag_queries_limit,
                percentage=calc_percentage(user.usage.rag_queries_count, plan.rag_queries_limit),
            ),
        ),
        projects=ProjectSummary(
            active=user.usage.projects_count,
            limit=plan.projects_limit,
        ),
    )
