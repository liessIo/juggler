# backend/test_key_manager.py

"""
Quick test script for the API Key Manager
Run this to verify PyNaCl encryption works correctly
"""

import sys
import os

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.security.key_manager import APIKeyManager
    
    def test_encryption_decryption():
        print("Testing API Key Manager...")
        
        # Initialize with test secret
        km = APIKeyManager("test-secret-key-12345")
        
        # Test data
        test_key = "gsk_1234567890abcdef"
        user_id = "user123"
        provider = "groq"
        
        print(f"Original key: {test_key}")
        
        # Encrypt
        encrypted = km.encrypt_api_key(test_key, user_id, provider)
        print(f"Encrypted data: {encrypted.encrypted_data[:50]}...")
        print(f"Salt: {encrypted.salt}")
        print(f"Hash: {encrypted.key_hash[:16]}...")
        
        # Decrypt
        decrypted = km.decrypt_api_key(encrypted, user_id)
        print(f"Decrypted key: {decrypted}")
        
        # Verify
        if test_key == decrypted:
            print("✅ Encryption/decryption successful!")
        else:
            print("❌ Encryption/decryption failed!")
            return False
        
        # Test verification
        is_valid = km.verify_api_key(test_key, encrypted)
        print(f"Key verification: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        # Test with wrong user
        try:
            wrong_decrypt = km.decrypt_api_key(encrypted, "wrong_user")
            print("❌ Should have failed with wrong user!")
            return False
        except Exception as e:
            print(f"✅ Correctly rejected wrong user: {str(e)[:50]}...")
        
        return True
    
    if __name__ == "__main__":
        success = test_encryption_decryption()
        if success:
            print("\n🎉 All tests passed! Key manager is working correctly.")
        else:
            print("\n💥 Tests failed!")
            
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the backend directory")
except Exception as e:
    print(f"Error: {e}")
    print("PyNaCl might not be installed correctly")