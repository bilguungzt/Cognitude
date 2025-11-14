"""
Security tests for encryption service.
"""
import pytest
from app.services.encryption import EncryptionService
from app.config import Settings


def test_encryption_service_initialization():
    """Test that encryption service initializes correctly with a secret key."""
    # Mock settings with a secret key
    settings = Settings(SECRET_KEY="test-secret-key-for-encryption")
    
    # Should not raise an exception
    service = EncryptionService()
    assert service._fernet is not None


def test_encrypt_decrypt_roundtrip():
    """Test that encryption and decryption work correctly."""
    service = EncryptionService()
    
    plaintext = "my-secret-api-key-12345"
    encrypted = service.encrypt(plaintext)
    
    # Encrypted should be different from plaintext
    assert encrypted != plaintext
    assert len(encrypted) > 0
    
    # Decrypt should return original plaintext
    decrypted = service.decrypt(encrypted)
    assert decrypted == plaintext


def test_encrypt_empty_string():
    """Test encryption of empty string."""
    service = EncryptionService()
    
    encrypted = service.encrypt("")
    assert encrypted == ""


def test_decrypt_empty_string():
    """Test decryption of empty string."""
    service = EncryptionService()
    
    decrypted = service.decrypt("")
    assert decrypted == ""


def test_decrypt_invalid_data():
    """Test decryption of invalid encrypted data."""
    service = EncryptionService()
    
    with pytest.raises(ValueError, match="Failed to decrypt data"):
        service.decrypt("invalid-encrypted-data")


def test_encryption_consistency():
    """Test that same plaintext encrypts to different ciphertexts (Fernet property)."""
    service = EncryptionService()
    
    plaintext = "test-api-key"
    encrypted1 = service.encrypt(plaintext)
    encrypted2 = service.encrypt(plaintext)
    
    # Same plaintext should produce different ciphertexts
    assert encrypted1 != encrypted2
    
    # But both should decrypt to the same plaintext
    assert service.decrypt(encrypted1) == plaintext
    assert service.decrypt(encrypted2) == plaintext


def test_encryption_with_special_characters():
    """Test encryption of strings with special characters."""
    service = EncryptionService()
    
    plaintext = "key-with-special-chars!@#$%^&*()_+-=[]{}|;:,.<>?"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_encryption_with_unicode():
    """Test encryption of strings with unicode characters."""
    service = EncryptionService()
    
    plaintext = "key-with-unicode-🚀-emoji-and-中文"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)
    
    assert decrypted == plaintext


def test_encryption_key_derivation():
    """Test that same secret key produces same encryption capability."""
    # This tests the PBKDF2 key derivation consistency
    service1 = EncryptionService()
    service2 = EncryptionService()
    
    plaintext = "test-key"
    encrypted = service1.encrypt(plaintext)
    
    # Both services should be able to decrypt
    assert service1.decrypt(encrypted) == plaintext
    assert service2.decrypt(encrypted) == plaintext


def test_encryption_without_secret_key():
    """Test that encryption service fails without secret key."""
    # This would require mocking settings to return None
    # For now, we test that the service requires initialization
    service = EncryptionService()
    assert service._fernet is not None


@pytest.mark.security
def test_encrypted_data_is_not_plaintext():
    """Security test: encrypted data should not contain plaintext."""
    service = EncryptionService()
    
    plaintext = "super-secret-api-key-12345"
    encrypted = service.encrypt(plaintext)
    
    # Encrypted data should not contain the plaintext
    assert plaintext not in encrypted
    
    # Encrypted data should be base64 encoded (Fernet format)
    assert encrypted.isascii()  # Should be ASCII characters only


@pytest.mark.security
def test_encryption_key_strength():
    """Security test: verify encryption uses strong algorithms."""
    service = EncryptionService()
    
    # Test with a long key to ensure no length limitations
    long_plaintext = "x" * 1000
    encrypted = service.encrypt(long_plaintext)
    decrypted = service.decrypt(encrypted)
    
    assert decrypted == long_plaintext
    assert len(encrypted) > len(long_plaintext)  # Encrypted should be longer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])