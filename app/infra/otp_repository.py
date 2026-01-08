"""
OTP Repository for managing OTP codes in MongoDB.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from pymongo import MongoClient
from cryptography.fernet import Fernet

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OTPRepository:
    """Repository for OTP operations"""
    
    def __init__(self):
        self.client = MongoClient(settings.mongo_uri)
        self.db = self.client[settings.mongo_meta_db]
        self.collection = self.db["otps"]
        
        # Initialize Fernet cipher for encryption
        self.cipher = Fernet(settings.encryption_key.encode())
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes"""
        try:
            # Index on user_id for fast lookups
            self.collection.create_index("user_id")
            # Index on email
            self.collection.create_index("email")
            # TTL index to auto-delete expired OTPs (60 seconds)
            self.collection.create_index("created_at", expireAfterSeconds=60)
            # Index on status
            self.collection.create_index("status")
        except Exception as e:
            # Check for IndexOptionsConflict (code 85)
            # This happens when changing TTL options on an existing index
            if hasattr(e, 'code') and e.code == 85:
                logger.warning("Index conflict detected for 'created_at'. Dropping old index and recreating...")
                try:
                    self.collection.drop_index("created_at_1")
                    # Retry creation with new options
                    self.collection.create_index("created_at", expireAfterSeconds=60)
                    logger.info("✅ TTL index recreated successfully with 60s expiration.")
                except Exception as retry_error:
                    logger.error(f"Failed to fix index conflict: {retry_error}")
            else:
                logger.warning(f"Failed to create indexes: {e}")
    
    def _encrypt_code(self, code: str) -> str:
        """Encrypt OTP code"""
        return self.cipher.encrypt(code.encode()).decode()
    
    def _decrypt_code(self, encrypted_code: str) -> str:
        """Decrypt OTP code"""
        return self.cipher.decrypt(encrypted_code.encode()).decode()
    
    def create_otp(
        self,
        otp_id: str,
        user_id: str,
        email: str,
        code: str,
        otp_type: str = "login"
    ) -> dict:
        """
        Create a new OTP record with encrypted code.
        
        Args:
            otp_id: Unique OTP identifier
            user_id: User ID
            email: User email
            code: 6-digit OTP code (will be encrypted)
            otp_type: Type of OTP (login, password_reset, etc.)
        
        Returns:
            Created OTP document (with encrypted code)
        """
        # Encrypt the OTP code before storing
        encrypted_code = self._encrypt_code(code)
        
        otp_doc = {
            "otp_id": otp_id,
            "user_id": user_id,
            "email": email,
            "code": encrypted_code,  # Store encrypted
            "type": otp_type,
            "status": "pending",  # pending, used, expired
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        self.collection.insert_one(otp_doc)
        logger.info(f"🔐 OTP created (encrypted): {otp_id} for user {user_id}")
        return otp_doc
    
    def get_otp_by_id(self, otp_id: str) -> Optional[dict]:
        """
        Get OTP by ID.
        
        Args:
            otp_id: OTP identifier
        
        Returns:
            OTP document or None
        """
        return self.collection.find_one({"otp_id": otp_id}, {"_id": 0})
    
    def get_latest_otp_by_user(self, user_id: str, status: str = "pending") -> Optional[dict]:
        """
        Get the latest OTP for a user.
        
        Args:
            user_id: User ID
            status: OTP status filter
        
        Returns:
            Latest OTP document or None
        """
        return self.collection.find_one(
            {"user_id": user_id, "status": status},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
    
    def verify_otp(self, user_id: str, code: str) -> Optional[dict]:
        """
        Verify OTP code for a user.
        Decrypts stored OTP and compares with provided code.
        
        Args:
            user_id: User ID
            code: OTP code to verify
        
        Returns:
            OTP document if valid, None otherwise
        """
        # Get latest pending OTP
        otp_doc = self.get_latest_otp_by_user(user_id, status="pending")
        
        if not otp_doc:
            logger.warning(f"No pending OTP found for user {user_id}")
            return None
        
        # Decrypt stored code
        try:
            stored_code = self._decrypt_code(otp_doc["code"])
            
            # Compare codes
            if stored_code == code:
                logger.info(f"✅ OTP verified successfully for user {user_id}")
                return otp_doc
            else:
                logger.warning(f"❌ Invalid OTP code for user {user_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to decrypt OTP: {e}")
            return None
    
    def update_otp_status(self, otp_id: str, status: str) -> bool:
        """
        Update OTP status.
        
        Args:
            otp_id: OTP identifier
            status: New status (used, expired, etc.)
        
        Returns:
            True if updated successfully
        """
        result = self.collection.update_one(
            {"otp_id": otp_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"OTP {otp_id} status updated to {status}")
            return True
        return False
    
    def invalidate_user_otps(self, user_id: str) -> int:
        """
        Invalidate all pending OTPs for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            Number of OTPs invalidated
        """
        result = self.collection.update_many(
            {"user_id": user_id, "status": "pending"},
            {
                "$set": {
                    "status": "expired",
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        count = result.modified_count
        if count > 0:
            logger.info(f"Invalidated {count} OTPs for user {user_id}")
        return count
