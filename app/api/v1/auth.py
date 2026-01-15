"""
Authentication endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from typing import Dict

from app.services.verify_otp import VerifyOTPService
from app.services.refresh_token import RefreshTokenService
from app.infra.otp_repository import OTPRepository
from app.infra.user_repository import UserRepository
from app.dependencies.auth import require_user_key
from app.services.generate_otp import GenerateOTPService

router = APIRouter()
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    api_key: str


@router.post("/login")
async def login(request: LoginRequest, req: Request):
    """
    Initiate login by generating and sending OTP.
    Public endpoint - does not require authentication.
    
    Args:
        api_key: User API Key
    
    Returns:
        Message confirming OTP was sent
    """
    
    try:
        logger.info(f"Login attempt with API key: {request.api_key[:15]}...")
        
        # Validate API key directly
        user_repo = UserRepository()
        user = user_repo.get_by_api_key(request.api_key)
        
        if not user:
            logger.warning(f"Invalid API key attempted: {request.api_key[:15]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="❌ API Key inválida. Verifica que sea correcta."
            )
        
        logger.info(f"Valid API key for user: {user.id}")
        
        # Check per-user OTP rate limit (3 per hour)
        otp_repo = OTPRepository()
        recent_otps = otp_repo.count_recent_otps(user.id, hours=1)
        
        if recent_otps >= 3:
            logger.warning(f"User {user.id} exceeded OTP rate limit")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="⚠️ Has solicitado demasiados códigos. Puedes solicitar otro en 1 hora."
            )
        
        # Generate OTP
        service = GenerateOTPService(
            otp_repo=otp_repo,
            user_repo=user_repo
        )
        
        result = await service.execute(user.id)
        logger.info(f"OTP generated successfully for user: {user.id}")
        
        return {
            "message": "✅ Código enviado a tu email. Revisa tu bandeja de entrada.",
            "email": result["email"],
            "expires_in": result["expires_in"]
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Failed to generate OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="❌ Error al procesar tu solicitud. Intenta nuevamente."
        )



class VerifyOTPRequest(BaseModel):
    code: str


@router.post("/request-otp")
async def request_otp(user: dict = Depends(require_user_key)):
    """
    Request OTP code for authentication.
    Generates a 6-digit OTP and sends it to the user's email.
    
    Requires User API Key (X-User-Key header).
    
    Returns:
        Message confirming OTP was sent
    """
    
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
