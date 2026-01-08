"""
Endpoints de usuarios (requieren User API Key).
"""
import logging
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel
from typing import List

from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository
from app.dependencies.auth import require_user_key

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
@router.get("/me")
async def request_otp(user: dict = Depends(require_user_key)):
    """
    Request OTP code for authentication.
    Generates a 6-digit OTP and sends it to the user's email.
    
    Requiere User API Key (X-User-Key header).
    
    Returns:
        Message confirming OTP was sent
    """
    from app.services.generate_otp import GenerateOTPService
    from app.infra.otp_repository import OTPRepository
    from app.infra.user_repository import UserRepository
    
    try:
        service = GenerateOTPService(
            otp_repo=OTPRepository(),
            user_repo=UserRepository()
        )
        
        result = await service.execute(user["user_id"])
        
        return {
            "message": result["message"],
            "email": result["email"],
            "expires_in": result["expires_in"]
        }
    
    except ValueError as e:
        logger.error(f"Failed to generate OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OTP"
        )


@router.get("/debug/auth")
async def debug_auth(request: Request):
    """Debug endpoint to test middleware authentication"""
    return {
        "has_auth_level": hasattr(request.state, 'auth_level'),
        "auth_level": getattr(request.state, 'auth_level', None),
        "has_user": hasattr(request.state, 'user'),
        "user_id": getattr(request.state, 'user', None).id if hasattr(request.state, 'user') else None,
    }


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
