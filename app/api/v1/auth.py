"""
Authentication endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict

from app.services.verify_otp import VerifyOTPService
from app.services.refresh_token import RefreshTokenService
from app.infra.otp_repository import OTPRepository
from app.infra.user_repository import UserRepository
from app.dependencies.auth import require_user_key

router = APIRouter()
logger = logging.getLogger(__name__)


class VerifyOTPRequest(BaseModel):
    code: str


@router.post("/verify-otp")
async def verify_otp(
    request: VerifyOTPRequest,
    user: dict = Depends(require_user_key)
):
    """
    Verify OTP code and issue JWT tokens.
    
    Requires User API Key to identify the user trying to login.
    """
    try:
        service = VerifyOTPService(
            otp_repo=OTPRepository(),
            user_repo=UserRepository()
        )
        
        result = service.execute(
            user_id=user["user_id"],
            code=request.code
        )
        
        return result
        
    except ValueError as e:
        logger.warning(f"OTP verification failed for user {user['user_id']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP"
        )


class RefreshTokenRequest(BaseModel):
    """Modelo para solicitar refresco de token"""
    refresh_token: str


@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
):
    """
    Renueva el Access Token usando un Refresh Token válido.
    
    Args:
        request: Body con refresh_token
    
    Returns:
        JSON con nuevo access_token
    """
    try:
        # Resolve dependency manually since we don't have it in Depends yet
        user_repo = UserRepository()
        service = RefreshTokenService(user_repo)
        return service.execute(request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
