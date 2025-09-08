# backend/app/security/key_manager.py

"""
API Key Manager with PyNaCl encryption
Handles secure storage and retrieval of provider API keys
"""

import os
import hashlib
from typing import Optional, Tuple
from dataclasses import dataclass

try:
    import nacl.secret
    import nacl.utils
    import nacl.encoding
    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False
    print("Warning: PyNaCl not installed. Install with: pip install PyNaCl")

@dataclass
class EncryptedKey:
    """Represents an encrypted API key with metadata"""
    encrypted_data: str  # Base64 encoded encrypted key
    salt: str           # Base64 encoded salt
    key_hash: str       # SHA256 hash for duplicate detection
    provider: str       # Provider name (groq, gemini, etc.)

class APIKeyManager:
    """
    Manages encryption and decryption of API keys using PyNaCl
    Uses PBKDF2 to derive user-specific encryption keys from master secret
    """
    
    def __init__(self, master_secret: Optional[str] = None):
        if not NACL_AVAILABLE:
            raise ImportError("PyNaCl is required for API key encryption. Install with: pip install PyNaCl")
        
        self.master_secret = master_secret or os.getenv("SECRET_KEY")
        if not self.master_secret:
            raise ValueError("Master secret required for key derivation")
    
    def _derive_encryption_key(self, user_id: str, salt: bytes) -> bytes:
        """
        Derive a user-specific encryption key using PBKDF2
        """
        # Combine master secret with user ID for user-specific keys
        key_material = f"{self.master_secret}:{user_id}".encode('utf-8')
        
        # Use PBKDF2 with high iteration count for key derivation
        derived_key = hashlib.pbkdf2_hmac(
            'sha256',           # Hash algorithm
            key_material,       # Password
            salt,               # Salt
            100000,            # Iterations (100k is recommended minimum)
            32                 # Key length (32 bytes for NaCl)
        )
        
        return derived_key
    
    def _generate_salt(self) -> bytes:
        """Generate a cryptographically secure random salt"""
        return nacl.utils.random(16)  # 16 bytes = 128 bits
    
    def _hash_key(self, api_key: str) -> str:
        """Create a hash of the API key for duplicate detection"""
        return hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    
    def encrypt_api_key(self, api_key: str, user_id: str, provider: str) -> EncryptedKey:
        """
        Encrypt an API key for secure storage
        
        Args:
            api_key: The plain text API key to encrypt
            user_id: User ID for key derivation
            provider: Provider name (groq, gemini, etc.)
            
        Returns:
            EncryptedKey object with encrypted data and metadata
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        
        # Generate a unique salt for this encryption
        salt = self._generate_salt()
        
        # Derive encryption key from master secret + user ID + salt
        encryption_key = self._derive_encryption_key(user_id, salt)
        
        # Create NaCl SecretBox with derived key
        box = nacl.secret.SecretBox(encryption_key)
        
        # Encrypt the API key
        encrypted_data = box.encrypt(api_key.encode('utf-8'))
        
        # Create hash for duplicate detection
        key_hash = self._hash_key(api_key)
        
        return EncryptedKey(
            encrypted_data=nacl.encoding.Base64Encoder.encode(encrypted_data).decode('utf-8'),
            salt=nacl.encoding.Base64Encoder.encode(salt).decode('utf-8'),
            key_hash=key_hash,
            provider=provider
        )
    
    def decrypt_api_key(self, encrypted_key: EncryptedKey, user_id: str) -> str:
        """
        Decrypt an API key for use
        
        Args:
            encrypted_key: EncryptedKey object from storage
            user_id: User ID for key derivation
            
        Returns:
            Plain text API key
        """
        try:
            # Decode salt and encrypted data from base64
            salt = nacl.encoding.Base64Encoder.decode(encrypted_key.salt)
            encrypted_data = nacl.encoding.Base64Encoder.decode(encrypted_key.encrypted_data)
            
            # Derive the same encryption key
            encryption_key = self._derive_encryption_key(user_id, salt)
            
            # Create NaCl SecretBox with derived key
            box = nacl.secret.SecretBox(encryption_key)
            
            # Decrypt and return the API key
            decrypted_data = box.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")
    
    def verify_api_key(self, api_key: str, encrypted_key: EncryptedKey) -> bool:
        """
        Verify if a plain text API key matches the encrypted version
        without decrypting (using hash comparison)
        
        Args:
            api_key: Plain text API key to verify
            encrypted_key: Encrypted key to compare against
            
        Returns:
            True if keys match, False otherwise
        """
        return self._hash_key(api_key) == encrypted_key.key_hash
    
    def rotate_encryption(self, encrypted_key: EncryptedKey, user_id: str, provider: str) -> EncryptedKey:
        """
        Rotate encryption by decrypting and re-encrypting with new salt
        Useful for periodic key rotation
        
        Args:
            encrypted_key: Current encrypted key
            user_id: User ID for key derivation
            provider: Provider name
            
        Returns:
            New EncryptedKey with fresh encryption
        """
        # Decrypt the current key
        plain_key = self.decrypt_api_key(encrypted_key, user_id)
        
        # Re-encrypt with new salt
        return self.encrypt_api_key(plain_key, user_id, provider)

# Global instance - will be initialized with config
key_manager: Optional[APIKeyManager] = None

def get_key_manager() -> APIKeyManager:
    """Get the global key manager instance"""
    global key_manager
    if key_manager is None:
        key_manager = APIKeyManager()
    return key_manager

def initialize_key_manager(master_secret: str) -> None:
    """Initialize the global key manager with secret"""
    global key_manager
    key_manager = APIKeyManager(master_secret)