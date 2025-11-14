"""
Encryption service for securing sensitive data at rest.
Uses Fernet symmetric encryption for API keys and other secrets.
"""
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

from app.config import get_settings

settings = get_settings()

class EncryptionService:
    """
    Handles encryption and decryption of sensitive data.
    Uses Fernet (AES-128-CBC + HMAC) for secure encryption.
    """
    
    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._initialize_key()
    
    def _initialize_key(self):
        """Initialize encryption key from settings or generate new one."""
        secret_key = settings.SECRET_KEY
        if not secret_key:
            raise ValueError("SECRET_KEY must be set for encryption")
        
        # Use PBKDF2 to derive a consistent key from the secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'cognitude-encryption-salt',  # Fixed salt is OK for key derivation
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.get_secret_value().encode()))
        self._fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value.
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""
        
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")
        
        # Convert to bytes and encrypt
        plaintext_bytes = plaintext.encode('utf-8')
        encrypted_bytes = self._fernet.encrypt(plaintext_bytes)
        
        # Return as string for database storage
        return encrypted_bytes.decode('utf-8')
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted: The encrypted string to decrypt
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted:
            return ""
        
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")
        
        try:
            # Convert to bytes and decrypt
            encrypted_bytes = encrypted.encode('utf-8')
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")

# Global instance
encryption_service = EncryptionService()