"""
Endpoints de administración (requieren Master API Key).
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.services.admin.create_user import CreateUserService
from app.services.admin.update_user_plan import UpdateUserPlanService
from app.services.admin.block_user import BlockUserService
from app.infra.user_repository import UserRepository
from app.infra.plan_repository import PlanRepository
from app.dependencies.auth import require_master_key

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class CreateUserRequest(BaseModel):
    email: EmailStr
    plan_name: str = "free"
    webhook_url: Optional[str] = None


class UpdatePlanRequest(BaseModel):
    plan_name: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    plan: str
    status: str
    api_key: Optional[str] = None  # Solo en creación
    created_at: str


# Dependency Injection
def get_create_user_service() -> CreateUserService:
    return CreateUserService(
        user_repo=UserRepository(),
        plan_repo=PlanRepository(),
    )


def get_update_plan_service() -> UpdateUserPlanService:
    return UpdateUserPlanService(
        user_repo=UserRepository(),
        plan_repo=PlanRepository(),
    )


def get_block_user_service() -> BlockUserService:
    return BlockUserService(user_repo=UserRepository())


# Endpoints
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: CreateUserRequest,
    service: CreateUserService = Depends(get_create_user_service),
    _: str = Depends(require_master_key),
):
    """
    Crear un nuevo usuario con un plan específico.
    Requiere Master API Key.
    """
    try:
        result = service.execute(
            email=payload.email,
            plan_name=payload.plan_name,
            webhook_url=payload.webhook_url,
        )
        
        logger.info(f"User created: {result['user_id']} ({payload.email})")
        
        return UserResponse(
            user_id=result["user_id"],
            email=result["email"],
            plan=result["plan"],
            status="active",
            api_key=result["api_key"],  # Solo se muestra una vez
            created_at=result["created_at"].isoformat(),
        )
    
    except ValueError as e:
        logger.warning(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/users/{user_id}/plan")
async def update_user_plan(
    user_id: str,
    payload: UpdatePlanRequest,
    service: UpdateUserPlanService = Depends(get_update_plan_service),
    _: str = Depends(require_master_key),
):
    """
    Actualizar el plan de un usuario (upgrade/downgrade).
    Requiere Master API Key.
    """
    
    try:
        result = service.execute(user_id, payload.plan_name)
        logger.info(f"User plan updated: {user_id} -> {payload.plan_name}")
        return result
    
    except ValueError as e:
        logger.warning(f"Failed to update plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/users/{user_id}/block")
async def block_user(
    user_id: str,
    service: BlockUserService = Depends(get_block_user_service),
    _: str = Depends(require_master_key),
):
    """
    Bloquear un usuario.
    Requiere Master API Key.
    """
    
    try:
        result = service.execute(user_id, block=True)
        logger.info(f"User blocked: {user_id}")
        return result
    
    except ValueError as e:
        logger.warning(f"Failed to block user: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/users/{user_id}/unblock")
async def unblock_user(
    user_id: str,
    service: BlockUserService = Depends(get_block_user_service),
    _: str = Depends(require_master_key),
):
    """
    Desbloquear un usuario.
    Requiere Master API Key.
    """
    
    try:
        result = service.execute(user_id, block=False)
        logger.info(f"User unblocked: {user_id}")
        return result
    
    except ValueError as e:
        logger.warning(f"Failed to unblock user: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Cost Monitoring Endpoints
@router.get("/cost-dashboard")
async def get_cost_dashboard(
    days: int = 7,
    _: str = Depends(require_master_key)
):
    """
    Get comprehensive cost dashboard.
    Requires Master API Key.
    """
    from app.services.cost_monitoring import CostMonitoringService
    
    cost_monitor = CostMonitoringService()
    
    # Gemini costs
    daily_costs = await cost_monitor.get_daily_costs(days=min(days, 7))
    monthly_costs = await cost_monitor.get_daily_costs(days=30)
    
    # MongoDB storage
    storage_stats = await cost_monitor.get_storage_stats()
    
    # Budget alerts
    alerts = await cost_monitor.check_budget_alerts()
    
    return {
        "gemini": {
            f"last_{days}_days": daily_costs,
            "last_30_days": monthly_costs,
            "avg_cost_per_query": monthly_costs["avg_cost_per_query"]
        },
        "mongodb": storage_stats,
        "alerts": alerts,
        "total_monthly_estimate": monthly_costs["total_cost"]
    }


@router.get("/storage-stats")
async def get_storage_stats(_: str = Depends(require_master_key)):
    """
    Get MongoDB storage statistics.
    Requires Master API Key.
    """
    from app.services.cost_monitoring import CostMonitoringService
    
    cost_monitor = CostMonitoringService()
    return await cost_monitor.get_storage_stats()


@router.get("/user-costs/{user_id}")
async def get_user_costs(
    user_id: str,
    days: int = 30,
    _: str = Depends(require_master_key)
):
    """
    Get cost breakdown for a specific user.
    Requires Master API Key.
    """
    from app.services.cost_monitoring import CostMonitoringService
    
    cost_monitor = CostMonitoringService()
    return await cost_monitor.get_user_costs(user_id, days)

