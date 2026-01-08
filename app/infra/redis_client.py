"""
Redis client for OTP storage and token blacklist.
"""
import redis
import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RedisClient:
    """Redis client wrapper for OTP and token management"""
    
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info(f"✅ Redis connected: {settings.redis_host}:{settings.redis_port}")
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.warning("⚠️  OTP and token blacklist features will not work without Redis")
            self.client = None
    
    def set_otp(self, user_id: str, otp_code: str, ttl_seconds: int = None) -> bool:
        """
        Store OTP code for a user with TTL.
        
        Args:
            user_id: User ID
            otp_code: 6-digit OTP code
            ttl_seconds: Time to live in seconds (default from settings)
        
        Returns:
            True if stored successfully
        """
        if not self.client:
            logger.error("Redis client not available")
            return False
        
        ttl = ttl_seconds or settings.otp_expire_seconds
        key = f"otp:{user_id}"
        
        try:
            self.client.setex(key, ttl, otp_code)
            logger.info(f"OTP stored for user {user_id} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Failed to store OTP: {e}")
            return False
    
    def get_otp(self, user_id: str) -> Optional[str]:
        """
        Retrieve OTP code for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            OTP code if exists and not expired, None otherwise
        """
        if not self.client:
            return None
        
        key = f"otp:{user_id}"
        
        try:
            otp = self.client.get(key)
            return otp
        except Exception as e:
            logger.error(f"Failed to retrieve OTP: {e}")
            return None
    
    def delete_otp(self, user_id: str) -> bool:
        """
        Delete OTP code for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            True if deleted
        """
        if not self.client:
            return False
        
        key = f"otp:{user_id}"
        
        try:
            self.client.delete(key)
            logger.info(f"OTP deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete OTP: {e}")
            return False
    
    def blacklist_token(self, token_jti: str, ttl_seconds: int) -> bool:
        """
        Add JWT token to blacklist.
        
        Args:
            token_jti: JWT ID (jti claim)
            ttl_seconds: Time until token naturally expires
        
        Returns:
            True if blacklisted successfully
        """
        if not self.client:
            logger.error("Redis client not available")
            return False
        
        key = f"blacklist:{token_jti}"
        
        try:
            self.client.setex(key, ttl_seconds, "1")
            logger.info(f"Token blacklisted: {token_jti}")
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def is_token_blacklisted(self, token_jti: str) -> bool:
        """
        Check if JWT token is blacklisted.
        
        Args:
            token_jti: JWT ID (jti claim)
        
        Returns:
            True if blacklisted
        """
        if not self.client:
            return False
        
        key = f"blacklist:{token_jti}"
        
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False


# Singleton instance
_redis_client = None

def get_redis_client() -> RedisClient:
    """Get singleton instance of RedisClient"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
